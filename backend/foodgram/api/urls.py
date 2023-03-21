from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TagView, RecipeViewSet, IngredientView

router = DefaultRouter()

app_name = 'app'

router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('tags/', TagView.as_view()),
    path('ingredients/', IngredientView.as_view()),
    # path('v1/', include('djoser.urls')),
    # path('v1/', include('djoser.urls.jwt')),
]
