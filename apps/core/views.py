from django.shortcuts import render

from apps.products.models import Category, Product


def home(request):
    categories = Category.objects.all()
    active_products = Product.objects.filter(is_active=True).select_related("category")

    context = {
        "categories": categories,
        "new_products": active_products.order_by("-created_at")[:12],
        "deal_products": active_products.filter(discount_percent__gt=0)[:12],
        "popular_products": active_products.filter(badge=Product.Badge.POPULAR)[:12],
    }
    return render(request, "core/home.html", context)
