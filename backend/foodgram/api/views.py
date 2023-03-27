from rest_framework import filters, viewsets, permissions
from rest_framework.pagination import LimitOffsetPagination
from djoser.views import UserViewSet as UV

from .mixins import ReadOrListOnlyViewSet
# from .permissions import IsAuthorOrReadOnlyPermission
from .serializers import (
    TagSerializer,
    CustomUserSerializer,
    RecipeSerializer,
    IngredientSerializer,
    CustomUserCreateSerializer
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

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action == 'create' or self.action == 'partial_update':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]


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
