from django.forms.fields import MultipleChoiceField
from django_filters import rest_framework as filters
from api.models import Ingredients, Recipes


# class MyFilterBackend(filters.DjangoFilterBackend):
#     def get_filterset(self, request, queryset, view):
#         filterset_base = super().get_filterset(request, queryset, view)

#         return filterset_base
class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredients
        fields = ['name']


class MultipleField(MultipleChoiceField):
    def valid_value(self, value):   
        return True


class MultipleFilter(filters.MultipleChoiceFilter):
    field_class = MultipleField


class RecipeFilter(filters.FilterSet):
    author = filters.CharFilter(field_name='author__id')
    tags = MultipleFilter(field_name='tags__slug')
    is_favorited = filters.CharFilter(field_name='favorited',
                                      method='filter_favorited')

    def filter_favorited(self, queryset, name, value):
        if not value or not self.request.auth:
            return queryset
        else:
            return self.request.user.favorites.all()


    class Meta:
        model = Recipes
        fields = ['author', 'tags']
