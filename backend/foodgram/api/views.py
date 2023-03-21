from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, viewsets
from rest_framework.pagination import LimitOffsetPagination

from .mixins import ReadOrListOnlyViewSet
# from .permissions import IsAuthorOrReadOnlyPermission
from .serializers import (
    TagSerializer,
    UserSerializer,
    RecipeSerializer,
    IngredientSerializer,
)
from .models import Recipes, Ingredients, Tags, User


class TagViewSet(ReadOrListOnlyViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOrListOnlyViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    # permission_classes = [
    #     IsAuthorOrReadOnlyPermission,
    #     permissions.IsAuthenticatedOrReadOnly,
    # ]
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# class CommentViewSet(viewsets.ModelViewSet):
#     serializer_class = CommentSerializer
#     permission_classes = [
#         IsAuthorOrReadOnlyPermission,
#         permissions.IsAuthenticatedOrReadOnly,
#     ]

#     def perform_create(self, serializer):
#         serializer.save(
#             author=self.request.user,
#             post=get_object_or_404(Post, pk=self.kwargs.get("post_id")),
#         )

#     def get_queryset(self):
#         post_id = self.kwargs.get("post_id")
#         new_queryset = get_object_or_404(Post, id=post_id).comments.all()
#         return new_queryset


# class FollowViewSet(ReadOrWriteOnlyViewSet):
#     serializer_class = FollowSerializer
#     filter_backends = (filters.SearchFilter,)
#     permission_classes = (permissions.IsAuthenticated,)
#     search_fields = ("following__username",)

#     def perform_create(self, serializer):
#         user_name = serializer.context.get("request").data.get("following")
#         serializer.save(
#             user=self.request.user,
#             following=get_object_or_404(User, username=user_name),
#         )

#     def get_queryset(self):
#         user_id = self.request.auth.get("user_id")
#         new_queryset = get_object_or_404(User, id=user_id).follower.all()
#         return new_queryset
