from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("search/", views.product_search_api, name="search_api"),
    path("category/<slug:slug>/", views.category_detail, name="by_category"),
    path("<slug:slug>/", views.product_detail, name="detail"),
]
