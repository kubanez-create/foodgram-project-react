"""User's custom model."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """User's custom model."""

    username = models.CharField(
        "Username",
        max_length=150,
        unique=True,
        blank=False,
    )

    email = models.EmailField(
        verbose_name="Email", max_length=254, unique=True, blank=False
    )

    first_name = models.CharField(
        verbose_name="Name", max_length=150, blank=False)

    last_name = models.CharField(
        verbose_name="Surname", max_length=150, blank=False)

    is_subscribed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
