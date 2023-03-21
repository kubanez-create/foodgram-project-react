from rest_framework import serializers
# from rest_framework.relations import SlugRelatedField

from .models import Ingredients, Tags, Recipes
from users.models import User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = "__all__"


class RecipeSerializer(serializers.ModelSerializer):
    # author = serializers.SlugRelatedField(
    #     read_only=True, slug_field="username"
    # )

    class Meta:
        model = Recipes
        fields = "__all__"
        # read_only_fields = ("author", "post")

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def validate(self, data):
        request_author = self.context.get("request").user
        if not (request_author.username != data["following"].username):
            raise serializers.ValidationError(
                "Подписаться на самого себя не возможно")


class PasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )