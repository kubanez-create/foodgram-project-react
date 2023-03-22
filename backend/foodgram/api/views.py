# from django.shortcuts import get_object_or_404
from rest_framework import filters, viewsets, permissions
# from rest_framework.decorators import action
# from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from djoser.views import UserViewSet as UV

from .mixins import ReadOrListOnlyViewSet
# from .permissions import IsAuthorOrReadOnlyPermission
from .serializers import (
    TagSerializer,
    UserSerializer,
    RecipeSerializer,
    IngredientSerializer,
    PasswordSerializer
)
from .models import Recipes, Ingredients, Tags, User


class TagViewSet(ReadOrListOnlyViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOrListOnlyViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


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


class UserViewSet(UV):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return PasswordSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Instantiate and return the list of permissions given a current action.
        """
        if self.action == 'retrieve':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]




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
