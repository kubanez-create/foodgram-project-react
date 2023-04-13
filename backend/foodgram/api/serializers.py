from django.shortcuts import get_object_or_404
from djoser.serializers import (SetPasswordSerializer, UserCreateSerializer,
                                UserSerializer)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags
from users.models import CustomUser

AMOUNT_LOWER_BOUND = 1
AMOUNT_UPPER_BOUND = 1000000
TEXT_LENGTH_UPPER_BOUND = 20000

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = '__all__'

    def to_internal_value(self, data):
        return get_object_or_404(Tags, pk=data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        """Handle the need of is_subscribed info for anonymous user."""
        request = self.context.get('request')
        if not request.auth:
            return False
        return request.user in obj.subscribed.all()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredients
        fields = '__all__'

    def validate(self, attrs):
        """Validate ingredients quantities."""
        quantity = float(attrs.get('amount'))
        if any((quantity < AMOUNT_LOWER_BOUND, quantity > AMOUNT_UPPER_BOUND)):
            raise serializers.ValidationError(
                ('Amount for an ingredient cannot be less then 1 or '
                'greater then 1 million no matter how we measure it.')
            )
        return attrs

    # rewrote method to comply with technical specifications
    def to_representation(self, value):
        return {
            'id': value.ingredient.id,
            'name': value.ingredient.name,
            'measurement_unit': value.ingredient.measurement_unit,
            'amount': value.amount
        }

    # rewrote method to comply with technical specifications
    def to_internal_value(self, data):
        inst = get_object_or_404(Ingredients, pk=data.get('id'))
        return {
            'name': inst.name,
            'measurement_unit': inst.measurement_unit,
            'amount': data.get('amount'),
        }


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipeingredients_set')
    author = CustomUserSerializer(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        """
        Check whether the request user has the recipe in favorites.
        """
        return obj.favorited.filter(
            id=self.context.get('request').user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Check whether the request user has the recipe in a cart.
        """
        return obj.shopping_cart.filter(
            id=self.context.get('request').user.id).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipeingredients_set')
    author = CustomUserSerializer(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'image',
            'ingredients',
            'author',
            'name',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def validate(self, attrs):
        """Validate user's input."""
        recipe = Recipes.objects.filter(name=attrs.get('name'),
                                        author=self.context['request'].user)
        if recipe:
            raise serializers.ValidationError(
                'Name of a recipe must be unique for any particular user.')
        if len(attrs.get('text')) > TEXT_LENGTH_UPPER_BOUND:
            raise serializers.ValidationError(
                'Text for a recipe is too long. Consider writing a book.')
        return attrs

    def get_is_favorited(self, obj):
        """
        Check whether the request user has the recipe in favorites.
        """
        return obj.favorited.filter(
            id=self.context.get('request').user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Check whether the request user has the recipe in a cart.
        """
        return obj.shopping_cart.filter(
            id=self.context.get('request').user.id).exists()

    def create(self, validated_data):
        ingredients = validated_data.pop('recipeingredients_set')
        tags = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        recipe_ingredients = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredients, name=ingredient.get('name'))
            recipe_ingredients.append(RecipeIngredients(
                recipe=recipe, ingredient=current_ingredient,
                amount=ingredient.get('amount')
            ))
        RecipeIngredients.objects.bulk_create(recipe_ingredients)
        recipe.tags.add(*tags)
        return recipe

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            lst = []
            for ingredient in ingredients_data:
                if not RecipeIngredients.objects.filter(
                    recipe=instance,
                    ingredient=get_object_or_404(
                        Ingredients,
                        name=ingredient.get('name')),
                    amount=ingredient.get('amount')
                ).exists():
                    lst.append(RecipeIngredients(
                        recipe=instance,
                        ingredient=get_object_or_404(
                            Ingredients,
                            name=ingredient.get('name')),
                        amount=ingredient.get('amount')
                    ))
            RecipeIngredients.objects.bulk_create(lst)
        instance.save()
        return instance


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
        """Provide additional attributes.

        We use djoser's serializers which don't have username, first and last
         name fields so we need provide them.
        """
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
        """
        Check whether the request user is subscribed.

        Returns bool value which answer whether the request user is subscribed
         to the user which token was provided in request.
        """
        links = obj.subscribed.through.objects.select_related()
        if hasattr(self, 'initial_data'):
            return links.filter(
                from_customuser=obj,
                to_customuser=self.initial_data.get('subscribed')
            ).exists()
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
            return min(int(query.query_params.get('recipes_limit')[0]),
                       obj.recipes.count())
        return obj.recipes.count()

    def get_recipes(self, obj):
        """
        Get and serialize recipes.

        Return serialized recipe objects potentially filtered against
        'recipes_limit' query.
        """
        query = self.context.get('request')
        if query and query.query_params.get('recipes_limit'):
            qs = obj.recipes.all(
            )[: int(query.query_params.get('recipes_limit')[0])]
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

    # return annotated value for an ingredient
    def get_amount(self, obj):
        return obj.total
