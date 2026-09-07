from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.cart.cart import get_cart

from .models import Order, OrderItem
from .whatsapp import get_customer_whatsapp_link, send_order_notification


@login_required
def checkout(request):
    order_id = request.GET.get("order")
    if order_id:
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        return render(
            request,
            "orders/checkout.html",
            {
                "order": order,
                "whatsapp_link": get_customer_whatsapp_link(order),
                "auto_open_whatsapp": request.GET.get("whatsapp") == "1",
            },
        )

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
        # This is a best-effort backend alert via the Meta Business API
        # (requires WHATSAPP_PHONE_NUMBER_ID/ACCESS_TOKEN + an approved
        # template to actually be configured — see whatsapp.py docstring).
        send_order_notification(order)

        messages.success(request, f"Siparişiniz alındı! Sipariş No: #{order.pk}")
        # ?whatsapp=1 tells the order detail page to auto-open the
        # customer's own WhatsApp with the full cart pre-filled — this is
        # the "direct payment" path and works even if the Business API
        # alert above isn't configured/approved yet.
        return redirect(f"{reverse('orders:checkout')}?order={order.pk}&whatsapp=1")

    return render(request, "orders/checkout.html", {"cart": cart})


@login_required
def order_history(request):
    orders = request.user.orders.order_by("-created_at")
    return render(request, "orders/history.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    get_object_or_404(Order, pk=pk, user=request.user)
    return redirect(f"{reverse('orders:checkout')}?order={pk}")


@login_required
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == "POST":
        # Once the customer has been handed off to WhatsApp for this order,
        # the shop already has (or is about to have) the request in a real
        # chat — letting the site silently cancel/restock behind that
        # conversation would confuse staff. So self-service cancel is only
        # available for the (rare) case where no WhatsApp link exists yet,
        # e.g. WHATSAPP_ADMIN_PHONE isn't configured.
        if get_customer_whatsapp_link(order):
            messages.error(
                request,
                "Bu sipariş WhatsApp üzerinden mağazamıza iletildi, bu yüzden "
                "sitede iptal edilemiyor. Değişiklik için lütfen WhatsApp "
                "sohbeti üzerinden bizimle iletişime geçin.",
            )
        elif order.status in (Order.Status.PENDING, Order.Status.CONFIRMED):
            order.cancel()
            messages.info(request, f"Sipariş #{order.pk} iptal edildi.")
    return redirect("orders:detail", pk=order.pk)