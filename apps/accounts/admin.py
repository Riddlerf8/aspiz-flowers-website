from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm

from .models import User


class AdminUserChangeForm(BaseUserChangeForm):
    """
    Only overrides the on-screen labels for phone/address inside admin.
    The model's verbose_name ("Telefon"/"Adres") is left as-is because the
    site's own profile page (apps/accounts/forms.py ProfileForm) reads its
    field labels straight from the model, and that page must stay Turkish.
    """
    class Meta(BaseUserChangeForm.Meta):
        model = User
        labels = {"phone": "Phone", "address": "Address"}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = AdminUserChangeForm
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Store info", {"fields": ("phone", "address")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff")