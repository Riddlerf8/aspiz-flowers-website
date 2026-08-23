from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.products.models import Product

from . import cart as cart_service


def _parse_quantity(raw, default=1):
    """
    request.POST.get("quantity") can be missing, empty, or garbage (e.g. a
    hand-crafted request with quantity=abc) — int() on that raises
    ValueError/TypeError and used to bubble up as an unhandled 500. Missing
    values keep the old default-of-1 behavior; anything unparsable returns
    None so callers can respond with a normal validation error instead.
    """
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _cart_json(cart):
    """
    Shared serializer for every cart AJAX endpoint (add/update/remove/state)
    so the modal always gets the exact same shape back, whichever action
    triggered the request.
    """
    items = []
    for item in cart.items.select_related("product").prefetch_related("product__images"):
        image = item.product.primary_image
        items.append({
            "product_id": item.product_id,
            "name": item.product.name,
            "image_url": image.image.url if image else "",
            "unit_price": str(item.unit_price),
            "quantity": item.quantity,
            "line_total": str(item.line_total),
            "stock_quantity": item.product.stock_quantity,
        })
    return {
        "ok": True,
        "items": items,
        "cart_item_count": cart.total_items,
        "cart_total_price": str(cart.total_price),
    }


def cart_detail(request):
    current_cart = cart_service.get_cart(request)
    return render(request, "cart/detail.html", {"cart": current_cart})


def cart_state(request):
    """GET endpoint the cart modal calls when it opens, to render current
    contents without a full page load."""
    current_cart = cart_service.get_cart(request)
    return JsonResponse(_cart_json(current_cart))


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    quantity = _parse_quantity(request.POST.get("quantity"))
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if quantity is None:
        error = "Geçersiz adet."
        if is_ajax:
            return JsonResponse({"ok": False, "error": error}, status=400)
        messages.error(request, error)
        return redirect(product.get_absolute_url())

    try:
        cart_service.add_to_cart(request, product, quantity)
    except ValidationError as e:
        if is_ajax:
            return JsonResponse({"ok": False, "error": str(e.message)}, status=400)
        messages.error(request, e.message)
        return redirect(product.get_absolute_url())

    if is_ajax:
        return JsonResponse(_cart_json(cart_service.get_cart(request)))

    messages.success(request, f"{product.name} sepete eklendi.")
    return redirect("cart:detail")


@require_POST
def cart_update(request, product_id):
    quantity = _parse_quantity(request.POST.get("quantity"))
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if quantity is None:
        error = "Geçersiz adet."
        if is_ajax:
            return JsonResponse({"ok": False, "error": error}, status=400)
        messages.error(request, error)
        return redirect("cart:detail")

    try:
        cart_service.update_quantity(request, product_id, quantity)
    except ValidationError as e:
        if is_ajax:
            return JsonResponse({"ok": False, "error": str(e.message)}, status=400)
        messages.error(request, e.message)
        return redirect("cart:detail")

    if is_ajax:
        return JsonResponse(_cart_json(cart_service.get_cart(request)))
    return redirect("cart:detail")


@require_POST
def cart_remove(request, product_id):
    cart_service.remove_from_cart(request, product_id)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if is_ajax:
        return JsonResponse(_cart_json(cart_service.get_cart(request)))

    messages.info(request, "Ürün sepetten kaldırıldı.")
    return redirect("cart:detail")