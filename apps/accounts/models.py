from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending Django's built-in auth, so we can safely
    add store-specific fields later (phone, wholesale tier, etc.) without
    a painful migration to swap AUTH_USER_MODEL after the fact.
    """
    phone = models.CharField("Telefon", max_length=20, blank=True)
    address = models.TextField("Adres", blank=True)

    def __str__(self):
        return self.get_full_name() or self.username
