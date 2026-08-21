from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Beklemede"
        CONFIRMED = "confirmed", "Onaylandı"
        SHIPPED = "shipped", "Kargoda"
        DELIVERED = "delivered", "Teslim Edildi"
        CANCELLED = "cancelled", "İptal Edildi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    # Tracks whether the "new order" WhatsApp alert reached Meta's API
    # successfully, so staff can spot + resend failed notifications from
    # the admin instead of silently missing an order (see apps/orders/whatsapp.py).
    whatsapp_notified = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.pk} - {self.user}"

    @property
    def total(self):
        return sum(item.line_total for item in self.items.all())

    @transaction.atomic
    def cancel(self):
        """
        Cancelling an order restores stock automatically — the admin never
        has to touch stock numbers by hand in either direction.
        """
        if self.status == self.Status.CANCELLED:
            return
        for item in self.items.select_related("product").select_for_update():
            Product.objects.filter(pk=item.product_id).update(
                stock_quantity=models.F("stock_quantity") + item.quantity
            )
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if is_new:
            # Lock the product row so two simultaneous orders can't both
            # oversell the last units of stock.
            product = Product.objects.select_for_update().get(pk=self.product_id)

            if product.stock_quantity < self.quantity:
                raise ValidationError(
                    f"Yetersiz stok: '{product.name}' için sadece {product.stock_quantity} adet kaldı."
                )

            product.stock_quantity -= self.quantity
            product.save(update_fields=["stock_quantity"])

        super().save(*args, **kwargs)
