import tempfile

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as UV
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .mixins import ListViewSet, ReadOrListOnlyViewSet
from .models import Ingredients, Recipes, Tags, User
from .permissions import IsAuthorOrReadOnlyPermission
from .serializers import (
    CustomSetPasswordSerializer,
    CustomUserCreateSerializer,
    CustomUserSerializer,
    DownloadSerializer,
    FavoritesSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShoppingSerializer,
    TagSerializer,
)


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

    def get_permissions(self):
        if self.action in [
            'create', 'partial_update', 'favorite', 'shopping_cart']:
            permission_classes = [permissions.IsAuthenticated]
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
        permission_classes=[
            permissions.IsAuthenticated, IsAuthorOrReadOnlyPermission],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            data = {'favorited': request.user}
            serializer = FavoritesSerializer(recipe, data=data, partial=True)
            if serializer.is_valid():
                recipe.favorited.add(request.user)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if request.user not in recipe.favorited.all():
                return Response(
                    {'errors': (
                        f'Рецепт {recipe} не '
                        'находился в Избранном')},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                recipe.favorited.remove(request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthorOrReadOnlyPermission],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            data = {'shopping_cart': request.user}
            serializer = ShoppingSerializer(recipe, data=data, partial=True)
            if serializer.is_valid():
                recipe.shopping_cart.add(request.user)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if request.user not in recipe.shopping_cart.all():
                return Response(
                    {'errors': (f'Рецепт {recipe} не ' 'находился в корзине')},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                recipe.shopping_cart.remove(request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(UV):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'set_password':
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
            if serializer.is_valid():
                writer.subscribed.add(request.user)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            links = writer.subscribed.through.objects.all()
            if not links.filter(
                from_customuser=writer, to_customuser=request.user
            ).exists():
                return Response(
                    {'errors': (f'Вы не подписаны на автора {writer}.')},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                writer.subscribed.remove(request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsViewSet(ListViewSet):
    serializer_class = FollowSerializer

    def get_queryset(self):
        return self.request.user.subscribed.all()


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
        # use Sum(distinct=True) to get total amount w\0 double counting
        qs = Ingredients.objects.annotate(
            total=Sum('recipeingredients__amount', distinct=True)
        ).filter(recipeingredients__recipe__in=user_shopping_recipes)

        serializer = self.get_serializer(qs, many=True)
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
            response = HttpResponse(
                tmpdirname + '/shopping_list.txt', content_type='text/txt'
            )
            response['Content-Disposition'] = \
            'attachment; filename=shopping_list.txt'
            return response
