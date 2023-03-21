from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, RecipeViewSet, IngredientViewSet

router = DefaultRouter()

app_name = 'api'

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('v1/', include('djoser.urls')),
    # path('v1/', include('djoser.urls.jwt')),
]
