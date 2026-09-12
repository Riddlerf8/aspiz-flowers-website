from django.conf import settings
from django.db import models

from apps.products.models import Product


class Cart(models.Model):
    """
    A cart belongs to either a logged-in user OR an anonymous session key,
    never both being empty. This lets guests shop and, on login, we merge
    their session cart into their account cart (see get_cart in cart.py).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="carts", null=True, blank=True,
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name="cart_must_have_user_or_session",
            )
        ]

    def __str__(self):
        return f"Cart #{self.pk} ({self.user or self.session_key})"

    @property
    def total_items(self):
        # Count of distinct line items (products) in the cart, not the
        # sum of quantities — e.g. 3 different flowers x5 each shows "3",
        # not "15".
        return self.items.count()

    @property
    def total_price(self):
        return sum(item.line_total for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def unit_price(self):
        """Uses the best applicable wholesale tier price, falling back to
        the lowest tier price if the ordered quantity is below every tier.

        Contact-only ("DM") tiers have no fixed price, so the cart/checkout
        total can never be computed from one — those quantities fall back
        to the highest tier that DOES have a price. The customer still sees
        the "DM" prompt on the product page and is nudged to WhatsApp for
        an actual quote at that volume; this fallback only keeps the cart
        math sane if they add that quantity anyway.
        """
        tiers = [t for t in self.product.price_tiers.order_by("-min_quantity") if t.price is not None]
        for tier in tiers:
            if self.quantity >= tier.min_quantity:
                return tier.price
        if tiers:
            return tiers[-1].price
        return 0

    @property
    def line_total(self):
        return self.unit_price * self.quantity