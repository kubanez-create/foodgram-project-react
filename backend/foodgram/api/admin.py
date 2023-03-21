from django.contrib import admin

from .models import Ingredients, Tags, Recipes
from users.models import User


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author')
    list_filter = ('author', 'name')
    empty_value_display = '-пусто-'


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'first_name', 'last_name', 'email')
    list_filter = ('first_name', 'email')
    empty_value_display = '-пусто-'


admin.site.register(Recipes, RecipeAdmin)
admin.site.register(Tags)
admin.site.register(Ingredients)
admin.site.register(User, UserAdmin)
