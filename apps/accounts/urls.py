from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_request_view, name="login"),
    path("login/verify/", views.login_verify_view, name="login_verify"),
    path("login/verify-page/", views.login_verify_page, name="login_verify_page"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
]
