from django.contrib import admin

from .models import Ingredients, Tags, Recipes
from users.models import CustomUser


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author')
    list_filter = ('author', 'name')
    empty_value_display = '-пусто-'


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'first_name', 'last_name', 'email')
    list_filter = ('first_name', 'email')
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name',)
    empty_value_display = '-пусто-'


admin.site.register(Recipes, RecipeAdmin)
admin.site.register(Tags)
admin.site.register(Ingredients, IngredientAdmin)
admin.site.register(CustomUser, UserAdmin)
