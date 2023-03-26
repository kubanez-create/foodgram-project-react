from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from djoser.views import TokenCreateView, TokenDestroyView

from .views import TagViewSet, RecipeViewSet, IngredientViewSet, UserViewSet

router = DefaultRouter()

app_name = 'api'

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    re_path(r"^auth/token/login/?$", TokenCreateView.as_view(), name="login"),
    re_path(r"^auth/token/logout/?$", TokenDestroyView.as_view(), name="logout"),
]
