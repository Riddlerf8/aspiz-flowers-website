from django.shortcuts import render
from django.urls import reverse

from apps.products.models import Category, Product

# "Yeni Ürünler" (by created_at) and "Popüler Ürünler" (badge=POPULAR) each
# already get their own hand-built section below. Every other badge in the
# admin's dropdown (Editörün Seçimi, Yeni Sezon, Özel Seri, Tükenmek Üzere)
# had NO matching homepage section at all — this list is what makes each of
# those show up too, in this display order, whenever a product carries it.
EXTRA_BADGE_SECTION_TITLES = {
    Product.Badge.EDITOR_CHOICE: "Editörün Seçimi",
    Product.Badge.NEW_SEASON: "Yeni Sezon",
    Product.Badge.SPECIAL_SERIES: "Özel Seri",
    Product.Badge.LOW_STOCK: "Tükenmek Üzere",
}


def home(request):
    categories = Category.objects.all()
    active_products = Product.objects.filter(is_active=True).select_related("category")

    badge_sections = []
    for badge_value, title in EXTRA_BADGE_SECTION_TITLES.items():
        products = active_products.filter(badge=badge_value).order_by("-created_at")[:12]
        if products:
            badge_sections.append({
                "title": title,
                "products": products,
                "see_all_url": f"{reverse('products:list')}?badge={badge_value}",
            })

    context = {
        "categories": categories,
        "new_products": active_products.order_by("-created_at")[:12],
        "deal_products": active_products.filter(discount_percent__gt=0)[:12],
        "popular_products": active_products.filter(badge=Product.Badge.POPULAR)[:12],

        "badge_sections": badge_sections,

        "new_url": f"{reverse('products:list')}?filter=new",
        "deal_url": f"{reverse('products:list')}?filter=deal",
        "popular_url": f"{reverse('products:list')}?filter=popular",
    }
    return render(request, "core/home.html", context)