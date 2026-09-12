import re

from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from .models import User


def _unique_username_from_email(email):
    """cicek@gmail.com -> 'cicek', then cicek2, cicek3... if taken."""
    base = re.sub(r"[^a-zA-Z0-9_.]", "", email.split("@")[0]) or "kullanici"
    username = base
    suffix = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


class RegisterForm(forms.ModelForm):
    full_name = forms.CharField(
        label="Ad Soyad",
        max_length=150,
        required=True,
    )
    email = forms.EmailField(label="E-posta Adresi", required=True)
    phone = forms.CharField(label="Telefon Numarası", max_length=20, required=True)
    terms = forms.BooleanField(
        label="Kullanım Şartları'nı okudum ve kabul ediyorum.",
        required=True,
        error_messages={"required": "Devam etmek için kullanım şartlarını kabul etmelisiniz."},
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "phone", "terms")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("autocomplete", "off")

    def clean_email(self):
        email = self.cleaned_data["email"]
        # is_active=True only: an inactive row is a previous registration
        # that never verified its email code (see register_view), and
        # doesn't deserve to permanently squat on the address.
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("Bu e-posta adresi zaten kayıtlı.")
        return email

    def clean_phone(self):
        phone = re.sub(r"\D", "", self.cleaned_data["phone"])
        if len(phone) < 10:
            raise forms.ValidationError("Geçerli bir telefon numarası girin.")
        if User.objects.filter(phone=phone, is_active=True).exists():
            raise forms.ValidationError("Bu telefon numarası zaten kayıtlı.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = _unique_username_from_email(self.cleaned_data["email"])
        user.phone = self.cleaned_data["phone"]
        user.set_unusable_password()

        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""

        if commit:
            user.save()
        return user


class LoginRequestForm(forms.Form):
    email = forms.EmailField(label="E-posta Adresi")
    phone = forms.CharField(label="Telefon Numarası", max_length=20)


class LoginVerifyForm(forms.Form):
    code = forms.RegexField(label="Giriş Kodu", regex=r"^\d{6}$", max_length=6, min_length=6)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "address")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bu form giriş modalıyla aynı görsel dili kullanıyor (bkz.
        # templates/accounts/profile.html + site.css bölüm 7/10: .form-group,
        # .input-with-icon). Buradaki class'lar Tailwind değil, o CSS
        # sınıflarıyla eşleşiyor; bilerek INPUT_CLASS kullanmıyoruz.
        for name, field in self.fields.items():
            if name == "address":
                field.widget.attrs.setdefault("rows", 3)
            field.widget.attrs.setdefault("autocomplete", "off")

    def clean_email(self):
        # RegisterForm already blocks duplicate emails at sign-up, but
        # nothing stopped someone from later editing their profile email to
        # match another account here — the DB unique constraint (see
        # migration 0003) would then reject the save with an ugly
        # IntegrityError instead of a normal form error. This catches it
        # early with a proper Turkish message.
        email = self.cleaned_data["email"]
        exists = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError("Bu e-posta adresi zaten kullanılıyor.")
        return email

    def clean_phone(self):
        phone = re.sub(r"\D", "", self.cleaned_data["phone"])
        if len(phone) < 10:
            raise forms.ValidationError("Geçerli bir telefon numarası girin.")
        exists = User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError("Bu telefon numarası zaten kullanılıyor.")
        return phone


class StyledPasswordResetForm(PasswordResetForm):
    """Uses the same .form-group/.input-with-icon design as ProfileForm/the login modal."""


class StyledSetPasswordForm(SetPasswordForm):
    """Uses the same .form-group/.input-with-icon design as ProfileForm/the login modal."""