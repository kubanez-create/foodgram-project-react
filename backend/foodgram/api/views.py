from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters, viewsets, permissions, status
from rest_framework.pagination import LimitOffsetPagination
from djoser.views import UserViewSet as UV

from .mixins import ReadOrListOnlyViewSet
from .permissions import IsAuthorOrReadOnlyPermission
from .serializers import (
    TagSerializer,
    CustomUserSerializer,
    RecipeSerializer,
    RecipeCreateSerializer,
    IngredientSerializer,
    CustomUserCreateSerializer,
    FavoritesSerializer
)
from .models import Recipes, Ingredients, Tags, User


class TagViewSet(ReadOrListOnlyViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOrListOnlyViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action == 'create' or self.action == 'partial_update':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
       detail=True, methods=['POST', 'DELETE'],
       permission_classes=[IsAuthorOrReadOnlyPermission]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            data = {'favored': request.user}
            serializer = FavoritesSerializer(recipe, data=data, partial=True)
            if serializer.is_valid():
                recipe.favored.add(request.user)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if request.user not in recipe.favored.all():
                return Response(
                    {'errors': (
                                    f'Рецепт "{recipe}" не '
                                    'находился в Избранном'
                                )},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                recipe.favored.remove(request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(UV):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action == 'retrieve' or self.action == 'me':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
