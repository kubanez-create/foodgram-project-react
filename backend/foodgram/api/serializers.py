import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import (
    SetPasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from rest_framework import serializers

from users.models import CustomUser
from .models import Ingredients, RecipeIngredients, Recipes, Tags


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
        return {
            'id': instance.id,
            'name': instance.name,
            'color': instance.color,
            'slug': instance.slug,
        }

    def to_internal_value(self, data):
        inst = get_object_or_404(Tags, pk=data)
        return {'name': inst.name, 'slug': inst.slug, 'color': inst.color}


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredients
        fields = ('id', 'recipe', 'ingredient', 'amount')

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.name,
            'measurement_unit': instance.measurement_unit,
            'amount': instance.recipeingredients_set.all()[0].amount,
        }

    def to_internal_value(self, data):
        inst = get_object_or_404(Ingredients, pk=data.get('id'))
        return {
            'name': inst.name,
            'measurement_unit': inst.measurement_unit,
            'amount': data.get('amount'),
        }


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True)

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'ingredients',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'image',
            'ingredients',
            'name',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        tags_list = []
        for i in ingredients:
            current_ingredient = get_object_or_404(
                Ingredients, name=i.get('name'))
            RecipeIngredients.objects.create(
                recipe=recipe, ingredient=current_ingredient,
                amount=i.get('amount')
            )
        for t in tags:
            current_tag = Tags.objects.get(slug=t.get('slug'))
            tags_list.append(current_tag)
        recipe.tags.add(*tags_list)
        return recipe

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
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
                curr_ingredient, _ = RecipeIngredients.objects.get_or_create(
                    recipe=instance,
                    ingredient=ingredient.get('name'),
                    amount=ingredient.get('amount'),
                )
        return instance


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not bool(request.auth):
            return False
        else:
            return request.user in obj.customuser_set.all()


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'password')


class CustomSetPasswordSerializer(SetPasswordSerializer):
    username = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs['username'] = self.context['request'].data.get('username')
        attrs['first_name'] = self.context['request'].data.get('first_name')
        attrs['last_name'] = self.context['request'].data.get('last_name')
        return attrs


class FavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipes

    def validate(self, data):
        request_author = self.initial_data.get('favorited')
        recipe_id = self.instance.id
        favorites = request_author.favorites.select_related('author')
        if favorites.filter(id=recipe_id).exists():
            raise serializers.ValidationError('Данный рецепт уже в избранных.')
        return data


class ShoppingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipes

    def validate(self, data):
        request_author = self.initial_data.get('shopping_cart')
        recipe_id = self.instance.id
        shopping = request_author.shopping.select_related('author')
        if shopping.filter(id=recipe_id).exists():
            raise serializers.ValidationError('Данный рецепт уже в корзине.')
        return data


class RecipeFollowSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipes


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        model = CustomUser

    def get_is_subscribed(self, obj):
        links = obj.subscribed.through.objects.select_related()
        if hasattr(self, 'initial_data'):
            return links.filter(
                from_customuser=obj,
                to_customuser=self.initial_data.get('subscribed')
            ).exists()
        else:
            return True

    def get_recipes_count(self, obj):
        """
        Return number of recipes.

        Return whichever the minimal value is between number of
        recipes the author of request has and recipes_limit query
        if there is any.
        """
        query = self.context.get('request')
        if query and query.query_params.get('recipes_limit'):
            return min(int(query.get('recipes_limit')[0]), obj.recipes.count())
        return obj.recipes.count()

    def get_recipes(self, obj):
        """
        Get and serialize recipes.

        Return serialized recipe objects potentially filtered against
        'recipes_limit' query.
        """
        query = self.context.get('request')
        if query and query.query_params.get('recipes_limit'):
            qs = obj.recipes.all()[: int(query.get('recipes_limit')[0])]
            serializer = RecipeFollowSerializer(qs, many=True)
            return serializer.data
        serializer = RecipeFollowSerializer(obj.recipes.all(), many=True)
        return serializer.data

    def validate(self, data):
        if not (self.instance != self.initial_data.get('subscribed')):
            raise serializers.ValidationError(
                'Подписаться на самого себя не возможно')

        user_following = self.instance.subscribed.select_related()
        if self.initial_data.get('subscribed') in user_following:
            raise serializers.ValidationError(
                'Вы уже подписаны на данного автора')
        return data


class DownloadSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        fields = ('name', 'amount', 'measurement_unit')
        model = Ingredients

    def get_amount(self, obj):
        return obj.total
