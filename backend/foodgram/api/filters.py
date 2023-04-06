from django.forms.fields import MultipleChoiceField
from django_filters import rest_framework as filters

from api.models import Ingredients, Recipes


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Ingredients
        fields = ["name"]


# next two classes is a way to filter (possibly) multiple tags
# as a union set ("or")
class MultipleField(MultipleChoiceField):
    def valid_value(self, value):
        return True


class MultipleFilter(filters.MultipleChoiceFilter):
    field_class = MultipleField


class RecipeFilter(filters.FilterSet):
    author = filters.CharFilter(field_name="author__id")
    tags = MultipleFilter(field_name="tags__slug")
    is_favorited = filters.CharFilter(
        field_name="favorited", method="filter_favorited")
    is_in_shopping_cart = filters.CharFilter(
        field_name="shopping_cart", method="filter_shopping"
    )

    # if we have anonymous request or query with zero value - return basic
    # queryset, fitered queryset otherwise
    def filter_favorited(self, queryset, name, value):
        if any((not int(value), not self.request.auth)):
            return queryset
        return queryset.filter(favorited=self.request.user)

    def filter_shopping(self, queryset, name, value):
        if any((not int(value), not self.request.auth)):
            return queryset
        return queryset.filter(shopping_cart=self.request.user)

    class Meta:
        model = Recipes
        fields = ["author", "tags"]
