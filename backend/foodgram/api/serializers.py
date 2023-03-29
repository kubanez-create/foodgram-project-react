import base64

from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from users.models import CustomUser
from .models import Ingredients, Recipes, Tags, RecipeIngredients

# from rest_framework.relations import SlugRelatedField

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = '__all__'

    def to_representation(self, instance):
        return {"id": instance.id, "name": instance.name,
                "color": instance.color, "slug": instance.slug}
    def to_internal_value(self, data):
        inst = get_object_or_404(Tags, pk=data)
        return {'name': inst.name, 'slug': inst.slug, 'color': inst.color}



class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')

    def to_representation(self, instance):
        return {"id": instance.id, "name": instance.name,
                "measurement_unit": instance.measurement_unit,
                "amount": instance.amount}
    def to_internal_value(self, data):
        inst = get_object_or_404(Ingredients, pk=data.get('id'))
        return {'name': inst.name, 'measurement_unit': inst.measurement_unit,
                'amount': data.get('amount')}


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True)

    class Meta:
        model = Recipes
        fields = ('id', 'tags', 'ingredients', 'author', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')



class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipes
        fields = ('tags', 'image', 'ingredients', 'name', 'text',
                  'cooking_time')

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        tags_list = []
        for i in ingredients:
            current_ingredient, status = get_object_or_404(
                Ingredients, name=i.get('name'))
            RecipeIngredients.objects.create(recipe=recipe,
                                             ingredient=current_ingredient)
        for t in tags:
            current_tag = Tags.objects.get(slug=t.get('slug'))
            tags_list.append(current_tag)
        recipe.tags.add(*tags_list)
        return recipe

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            lst = []
            for tag in tags_data:
                current_tag = Tags.objects.get(slug=tag.get('slug'))
                lst.append(current_tag)
            instance.tags.set(lst)
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            lst = []
            for ingredient in ingredients_data:
                current_ingredient = Ingredients.objects.get(
                    name=ingredient.get('name')
                )
                current_ingredient.amount = ingredient.get('amount')
                lst.append(current_ingredient)
            instance.ingredients.set(lst)

        instance.save()
        return instance

class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name','last_name',
                  'is_subscribed')


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'password')


class FavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipes

    def validate(self, data):
        request_author = self.initial_data.get('favored')
        recipe_id = self.instance.id
        favorites = request_author.favorites.select_related('author')
        if favorites.filter(id__in=[recipe_id]).exists():
            raise serializers.ValidationError(
                'Данный рецепт уже в избранных.')
        return data