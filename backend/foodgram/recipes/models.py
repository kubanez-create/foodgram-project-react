from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Ingredients(models.Model):
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Tags(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipes(models.Model):
    tags = models.ManyToManyField(Tags, related_name='recipes')
    text = models.TextField('Text')
    pub_date = models.DateTimeField('Publication date', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE, verbose_name='Author', related_name='recipes'
    )
    image = models.ImageField(upload_to='recipes/')
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name='Ingredients',
        through='RecipeIngredients'
    )
    favorited = models.ManyToManyField(User, related_name='favorites',
                                       blank=True)
    shopping_cart = models.ManyToManyField(User, related_name='shopping',
                                           blank=True)
    name = models.CharField('Name', max_length=200)
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                1,
                message=(
                    'Sorry, but you cannot cook'
                    ' anything in less then a minute!'
                ),
            ),
            MaxValueValidator(
                10080,
                message=(
                    'We are interested in recipes with less then one'
                    'whole week of cooking time.'
                )
            )
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['author', 'name'],
                                    name='unique recipe')
        ]
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.IntegerField()

    class Meta:
        ordering = ['recipe__pub_date']

    def __str__(self):
        return f'{self.recipe} {self.ingredient}'
