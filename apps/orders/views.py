from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.cart import get_cart

from .models import Order, OrderItem
from .whatsapp import send_order_notification


@login_required
def checkout(request):
    cart = get_cart(request)

    if not cart.items.exists():
        messages.warning(request, "Sepetiniz boş.")
        return redirect("cart:detail")

    if request.method == "POST":
        try:
            with transaction.atomic():
                order = Order.objects.create(user=request.user)
                for item in cart.items.select_related("product"):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                    )
                cart.items.all().delete()
        except ValidationError as e:
            messages.error(request, e.message if hasattr(e, "message") else str(e))
            return redirect("cart:detail")

        # Order is already committed at this point — a WhatsApp failure
        # must never undo a valid order, so this runs outside the atomic
        # block above and only logs/flags on failure (see whatsapp.py).
        send_order_notification(order)

        messages.success(request, f"Siparişiniz alındı! Sipariş No: #{order.pk}")
        return redirect("orders:detail", pk=order.pk)

    return render(request, "orders/checkout.html", {"cart": cart})


@login_required
def order_history(request):
    orders = request.user.orders.order_by("-created_at")
    return render(request, "orders/history.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "orders/detail.html", {"order": order})


@login_required
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == "POST" and order.status in (Order.Status.PENDING, Order.Status.CONFIRMED):
        order.cancel()
        messages.info(request, f"Sipariş #{order.pk} iptal edildi.")
    return redirect("orders:detail", pk=order.pk)
