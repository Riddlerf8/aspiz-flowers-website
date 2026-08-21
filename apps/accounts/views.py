from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from apps.orders.models import Order

from .forms import LoginForm, ProfileForm, RegisterForm


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
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
        if _is_ajax(self.request):
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    next_url = request.POST.get("next") or request.GET.get("next") or ""
    ajax = _is_ajax(request)

    if request.method == "POST":
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