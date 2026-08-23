import re

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import User


# bg-white/text-wine-900 burada bilerek belirtiliyor: <meta name="color-scheme"
# content="light dark"> (base.html) yüzünden, rengi belirtilmemiş input/textarea'lar
# tarayıcının karanlık moduna göre siyah kutu olarak render edilebiliyordu.
INPUT_CLASS = (
    "w-full rounded-lg border border-cream-200 dark:border-white/10 px-3 py-2 text-sm "
    "bg-white text-wine-900 placeholder-wine-300 dark:bg-[#1c1c1c] dark:text-[#f5f3ef] "
    "focus:outline-none focus:border-wine-400"
)


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


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.setdefault("class", INPUT_CLASS)


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", INPUT_CLASS)