"""User's custom model."""
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """User's custom model."""
    username = models.CharField(
        "Username",
        max_length=150,
        unique=True,
        blank=False,
        help_text="Required. 150 characters or fewer."
    )

    email = models.EmailField(
        verbose_name="Email",
        max_length=254,
        unique=True,
        blank=False)

    first_name = models.CharField(
        verbose_name="Name",
        max_length=150,
        blank=False)

    last_name = models.CharField(
        verbose_name="Surname",
        max_length=150,
        blank=False)

    is_subscribed = models.BooleanField(null=True)
