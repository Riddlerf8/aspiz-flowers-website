from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images", "price_tiers")
    )

    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    query = request.GET.get("q")
    if query:
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": Category.objects.all(),
        "active_category": category_slug,
        "query": query or "",
    }
    return render(request, "products/list.html", context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = (
        Product.objects.filter(category=category, is_active=True)
        .prefetch_related("images", "price_tiers")
    )

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "category": category,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": Category.objects.all(),
        "active_category": slug,
    }
    return render(request, "products/list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images", "price_tiers"),
        slug=slug, is_active=True,
    )
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:6]

    return render(request, "products/detail.html", {"product": product, "related": related})
