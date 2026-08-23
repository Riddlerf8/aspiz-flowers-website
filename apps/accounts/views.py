import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from requests import RequestException

from apps.orders.models import Order

from . import google_oauth
from .forms import LoginForm, ProfileForm, RegisterForm, _unique_username_from_email
from .ratelimit import (
    clear_login_failures,
    is_login_locked,
    is_register_rate_limited,
    register_attempt,
    register_login_failure,
)

User = get_user_model()


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


LOGIN_LOCKOUT_MESSAGE = "Çok fazla başarısız giriş denemesi yapıldı. Lütfen 15 dakika sonra tekrar deneyin."
REGISTER_RATE_LIMIT_MESSAGE = "Çok fazla kayıt denemesi yapıldı. Lütfen daha sonra tekrar deneyin."


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        # Brute-force guard: block further attempts for this IP+identifier
        # pair before Django even touches the DB/password hasher.
        identifier = (request.POST.get("username") or "").strip()
        if identifier and is_login_locked(request, identifier):
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "errors": {"__all__": [LOGIN_LOCKOUT_MESSAGE]}},
                    status=429,
                )
            messages.error(request, LOGIN_LOCKOUT_MESSAGE)
            return redirect("accounts:login")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        identifier = form.cleaned_data.get("username", "")
        if identifier:
            clear_login_failures(self.request, identifier)
        response = super().form_valid(form)
        if not form.cleaned_data.get("remember_me"):
            # Session ends when the browser closes instead of the default
            # SESSION_COOKIE_AGE (2 weeks) when "Beni hatırla" isn't checked.
            self.request.session.set_expiry(0)
        if _is_ajax(self.request):
            # The auth modal (auth-modal.js) submits via fetch and expects
            # JSON back so it can redirect in place instead of Django doing
            # a normal 302 — the modal never gets a full-page navigation.
            return JsonResponse({"success": True, "redirect_url": self.get_success_url()})
        return response

    def form_invalid(self, form):
        identifier = (self.request.POST.get("username") or "").strip()
        if identifier:
            register_login_failure(self.request, identifier)
        if _is_ajax(self.request):
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    next_url = request.POST.get("next") or request.GET.get("next") or ""
    ajax = _is_ajax(request)

    if request.method == "POST":
        # Guard against scripted mass account creation from a single IP.
        if is_register_rate_limited(request):
            if ajax:
                return JsonResponse(
                    {"success": False, "errors": {"__all__": [REGISTER_RATE_LIMIT_MESSAGE]}},
                    status=429,
                )
            messages.error(request, REGISTER_RATE_LIMIT_MESSAGE)
            return render(request, "accounts/register.html", {"form": RegisterForm(), "next": next_url})

        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
            messages.success(request, "Hoş geldin! Hesabın oluşturuldu.")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                target = next_url
            else:
                target = reverse("core:home")
            if ajax:
                return JsonResponse({"success": True, "redirect_url": target})
            return redirect(target)

        register_attempt(request)
        if ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form, "next": next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "Çıkış yapıldı.")
    return redirect("core:home")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil güncellendi.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    orders = request.user.orders.order_by("-created_at")[:10]
    return render(request, "accounts/profile.html", {"form": form, "orders": orders})


def google_login(request):
    """Redirects to Google's consent screen. Hidden in templates via
    google_oauth_enabled until GOOGLE_OAUTH_CLIENT_ID/SECRET are set."""
    if not settings.GOOGLE_OAUTH_ENABLED:
        messages.error(request, "Google ile giriş şu anda kullanılamıyor.")
        return redirect("accounts:login")

    state = secrets.token_urlsafe(24)
    request.session["google_oauth_state"] = state
    next_url = request.GET.get("next") or ""
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        request.session["google_oauth_next"] = next_url
    return redirect(google_oauth.build_authorization_url(state))


def google_callback(request):
    """
    Handles Google's redirect back after consent. Matches the account by
    email: links to an existing account if one already has that email
    (e.g. someone who first registered normally), otherwise creates a new
    account. Accounts created this way get an unusable password (see
    set_unusable_password) since they only ever log in via Google — the
    "şifremi unuttum" flow correctly won't apply to them.
    """
    if not settings.GOOGLE_OAUTH_ENABLED:
        messages.error(request, "Google ile giriş şu anda kullanılamıyor.")
        return redirect("accounts:login")

    error = request.GET.get("error")
    if error:
        messages.error(request, "Google girişi iptal edildi.")
        return redirect("accounts:login")

    state = request.GET.get("state")
    expected_state = request.session.pop("google_oauth_state", None)
    if not state or not expected_state or state != expected_state:
        messages.error(request, "Google girişi doğrulanamadı, lütfen tekrar deneyin.")
        return redirect("accounts:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Google girişi doğrulanamadı, lütfen tekrar deneyin.")
        return redirect("accounts:login")

    try:
        access_token = google_oauth.exchange_code_for_token(code)
        userinfo = google_oauth.fetch_userinfo(access_token)
    except RequestException:
        messages.error(request, "Google ile bağlantı kurulamadı, lütfen tekrar deneyin.")
        return redirect("accounts:login")

    email = userinfo.get("email")
    if not email or not userinfo.get("email_verified"):
        messages.error(request, "Google hesabınızın e-postası doğrulanmamış.")
        return redirect("accounts:login")

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = User(
            username=_unique_username_from_email(email),
            email=email,
            first_name=userinfo.get("given_name", ""),
            last_name=userinfo.get("family_name", ""),
        )
        user.set_unusable_password()
        user.save()

    login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
    messages.success(request, "Google hesabınızla giriş yaptınız.")

    next_url = request.session.pop("google_oauth_next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("core:home")