import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


INPUT_CLASS = "w-full rounded-lg border border-cream-200 px-3 py-2 text-sm focus:outline-none focus:border-wine-400"


def _unique_username_from_email(email):
    """cicek@gmail.com -> 'cicek', then cicek2, cicek3... if taken."""
    base = re.sub(r"[^a-zA-Z0-9_.]", "", email.split("@")[0]) or "kullanici"
    username = base
    suffix = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(
        label="Ad Soyad",
        max_length=150,
        required=True,
    )
    email = forms.EmailField(label="E-posta Adresi", required=True)
    terms = forms.BooleanField(
        label="Kullanım Şartları'nı okudum ve kabul ediyorum.",
        required=True,
        error_messages={"required": "Devam etmek için kullanım şartlarını kabul etmelisiniz."},
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "password1", "password2", "terms")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UserCreationForm pulls in a "username" field from Meta by default;
        # we generate it automatically from the email instead of asking for it.
        self.fields.pop("username", None)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", INPUT_CLASS)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu e-posta adresi zaten kayıtlı.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = _unique_username_from_email(self.cleaned_data["email"])

        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""

        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="E-posta Adresi",
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "class": INPUT_CLASS,
            "autocomplete": "email",
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASS}),
    )
    remember_me = forms.BooleanField(label="Beni hatırla", required=False)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "address")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "address":
                field.widget.attrs.setdefault("class", INPUT_CLASS)
                field.widget.attrs.setdefault("rows", 3)
            else:
                field.widget.attrs.setdefault("class", INPUT_CLASS)
