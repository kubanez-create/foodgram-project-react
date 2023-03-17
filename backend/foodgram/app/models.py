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
    tags = models.ManyToManyField('Тэги', Tags, related_name='recipes')
    text = models.TextField('Текст')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        'Автор',
        User,
        on_delete=models.SET_NULL,
        related_name='recipes')
    image = models.ImageField(upload_to='recipes/')
    ingredients = models.ForeignKey(
        'Ингредиенты',
        Ingredients,
        on_delete=models.SET_NULL,
        related_name='recipes')
    is_favored = models.BooleanField()
    is_in_shopping_cart = models.BooleanField()
    name = models.CharField('Название', max_length=200)
    cooking_time = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["author", "title_id"],
                                    name="unique review")
        ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['pub_date']

    def __str__(self):
        return self.text
