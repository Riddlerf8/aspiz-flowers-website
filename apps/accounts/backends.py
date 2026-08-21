from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate with either the username OR the email address in the same
    field. The login form only shows one input labelled "E-posta Adresi",
    so we look the user up by email first and fall back to username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                # Run the hasher anyway to keep response time constant
                # regardless of whether the user exists.
                User().set_password(password)
                return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email__iexact=username).order_by("id").first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
