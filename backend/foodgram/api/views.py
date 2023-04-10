import tempfile

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserView
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Ingredients, Recipes, Tags, User
from .filters import IngredientFilter, RecipeFilter
from .mixins import ListViewSet, ReadOrListOnlyViewSet
from .permissions import IsAuthorOrReadOnlyPermission
from .serializers import (CustomSetPasswordSerializer,
                          CustomUserCreateSerializer, CustomUserSerializer,
                          DownloadSerializer, FavoritesSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          ShoppingSerializer, TagSerializer)


class TagViewSet(ReadOrListOnlyViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(ReadOrListOnlyViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # Удалил пермишен классы из actions и оставил их определение здесь
    # т.к. нам нужно предоставлять доступ не авторизованным пользователям к
    # списку пользователей и переопределение метода get_permissions позволяет
    # нам определить пользовательские разрешения достаточно сжатым кодом
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['favorite', 'shopping_cart', 'partial_update']:
            permission_classes = [
                permissions.IsAuthenticated,
                IsAuthorOrReadOnlyPermission,
            ]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            data = {'favorited': request.user}
            serializer = FavoritesSerializer(recipe, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            recipe.favorited.add(request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if request.user not in recipe.favorited.all():
                return Response(
                    {'errors': (f'Рецепт {recipe} не '
                                'находился в Избранном')},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            recipe.favorited.remove(request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return None

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            data = {'shopping_cart': request.user}
            serializer = ShoppingSerializer(recipe, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            recipe.shopping_cart.add(request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if request.user not in recipe.shopping_cart.all():
                return Response(
                    {'errors': (f'Рецепт {recipe} не находился в корзине')},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            recipe.shopping_cart.remove(request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return None


class UserViewSet(DjoserUserView):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        if self.action == 'set_password':
            return CustomSetPasswordSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'me', 'set_password', 'subscribe']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    # applied djoser's serializer doesn't have username, first and last name
    # field so we need to provide them
    @action(['post'], detail=False)
    def set_password(self, request, *args, **kwargs):
        whole_data = request.data
        whole_data['username'] = request.user.username
        whole_data['first_name'] = request.user.first_name
        whole_data['last_name'] = request.user.last_name
        serializer = self.get_serializer(data=whole_data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthorOrReadOnlyPermission],
    )
    def subscribe(self, request, id=None):
        writer = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            data = {'subscribed': request.user}
            serializer = FollowSerializer(writer, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            writer.subscribed.add(request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            links = writer.subscribed.through.objects.all()
            if not links.filter(
                from_customuser=writer, to_customuser=request.user
            ).exists():
                return Response(
                    {'errors': (f'Вы не подписаны на автора {writer}.')},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            writer.subscribed.remove(request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return None


class SubscriptionsViewSet(ListViewSet):
    serializer_class = FollowSerializer

    def get_queryset(self):
        return self.request.user.customuser_set.all()


class ShoppingViewSet(ListViewSet):
    serializer_class = DownloadSerializer

    def list(self, request, *args, **kwargs):
        """
        Calculate and return list on ingredients for a shopping cart.

        Annotate ingredients, filter them against the list of chosen recipes
        then return it in txt file.
        """
        # select recipes in shopping cart of a request user
        user_shopping_recipes = self.request.user.shopping.select_related()
        # get annotated queryset for ingredients
        # use Sum(distinct=True) to get total amount w\o double counting
        qs = Ingredients.objects.filter(
            recipeingredients__recipe__in=user_shopping_recipes).values(
                'name').annotate(
                    total=Sum('recipeingredients__amount'))

        qs_list = []
        for ingredient in qs:
            ingredient_object = get_object_or_404(
                Ingredients, name=ingredient['name'])
            ingredient_object.total = ingredient['total']
            qs_list.append(ingredient_object)
        serializer = self.get_serializer(qs_list, many=True)
        # get a string to write into txt file
        result = [
            f' - {i["name"]} ({i["measurement_unit"]}) - {i["amount"]}'
            for i in serializer.data
        ]
        # use temp directory keep working directory clean
        with tempfile.TemporaryDirectory() as tmpdirname:
            # write list of ingredients into txt file
            with open(tmpdirname + '/shopping_list.txt', 'w') as f:
                f.write('\n'.join(result))
            response = FileResponse(
                open(tmpdirname + '/shopping_list.txt', 'rb'),
                content_type='text/plain'
            )
            response[
                'Content-Disposition'
            ] = 'attachment; filename=shopping_list.txt'
            return response
