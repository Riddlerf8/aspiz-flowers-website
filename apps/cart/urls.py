from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("state/", views.cart_state, name="state"),
    path("add/<int:product_id>/", views.cart_add, name="add"),
    path("update/<int:product_id>/", views.cart_update, name="update"),
    path("remove/<int:product_id>/", views.cart_remove, name="remove"),
]
