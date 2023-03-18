from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredients(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=50)
    amount = models.IntegerField()

    def __str__(self):
        return self.name

class Tags(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Recipes(models.Model):
    tags = models.ManyToManyField(Tags, related_name='recipes')
    text = models.TextField('Text')
    pub_date = models.DateTimeField('Publication date', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Author',
        related_name='recipes')
    image = models.ImageField(upload_to='recipes/')
    ingredients = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ingredients',
        related_name='recipes')
    is_favored = models.BooleanField()
    is_in_shopping_cart = models.BooleanField()
    name = models.CharField('Name', max_length=200)
    cooking_time = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['author', 'name'],
                                    name='unique recipe')
        ]
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['pub_date']

    def __str__(self):
        return self.text
