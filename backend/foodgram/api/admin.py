from django.contrib import admin

from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags
from users.models import CustomUser


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author')
    list_display_links = ('name',)
    readonly_fields = ('total_favorited',)
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def total_favorited(self, obj):
        return ('Общее количество добавлений в избранное '
                f'{obj.favorited.count()}')


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
