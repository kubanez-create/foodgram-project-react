from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, RecipeViewSet, IngredientViewSet, UserViewSet

router = DefaultRouter()

app_name = 'app'

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
