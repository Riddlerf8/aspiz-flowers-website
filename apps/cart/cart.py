"""
Cart resolution + merge logic, kept out of views.py so it stays testable
and reusable (e.g. from a future API endpoint).
"""
from django.core.exceptions import ValidationError

from .models import Cart, CartItem


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_cart(request):
    """
    Returns the current user's/session's cart, creating it if needed.
    Also merges any anonymous session cart into the account cart the
    moment a user is authenticated (covers the "logged in mid-shopping"
    case cleanly, instead of silently losing the guest cart).
    """
    session_key = _ensure_session(request)

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        guest_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
        if guest_cart and guest_cart.pk != cart.pk:
            for item in guest_cart.items.all():
                existing = cart.items.filter(product=item.product).first()
                if existing:
                    existing.quantity += item.quantity
                    existing.save(update_fields=["quantity"])
                else:
                    item.cart = cart
                    item.save(update_fields=["cart"])
            guest_cart.delete()
        return cart

    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


def add_to_cart(request, product, quantity=1):
    cart = get_cart(request)

    if quantity < 1:
        raise ValidationError("Adet en az 1 olmalı.")
    if quantity > product.stock_quantity:
        raise ValidationError(
            f"Yetersiz stok: '{product.name}' için sadece {product.stock_quantity} adet var."
        )

    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
    if not created:
        new_quantity = item.quantity + quantity
        if new_quantity > product.stock_quantity:
            raise ValidationError(
                f"Yetersiz stok: '{product.name}' için sadece {product.stock_quantity} adet var."
            )
        item.quantity = new_quantity
        item.save(update_fields=["quantity"])
    return cart


def update_quantity(request, product_id, quantity):
    cart = get_cart(request)
    item = cart.items.filter(product_id=product_id).first()
    if not item:
        return cart
    if quantity < 1:
        item.delete()
        return cart
    if quantity > item.product.stock_quantity:
        raise ValidationError(
            f"Yetersiz stok: '{item.product.name}' için sadece {item.product.stock_quantity} adet var."
        )
    item.quantity = quantity
    item.save(update_fields=["quantity"])
    return cart


def remove_from_cart(request, product_id):
    cart = get_cart(request)
    cart.items.filter(product_id=product_id).delete()
    return cart
