from django.contrib import admin

from .models import Order, OrderItem

# Status.choices carries the Turkish labels shown to shoppers (Kargoda,
# Teslim Edildi, ...). The admin panel is English-only per store policy,
# so this is a second, admin-only label set for the SAME values — it
# never touches what's stored or what customers see in their order history.
STATUS_LABELS_EN = {
    Order.Status.PENDING: "Pending",
    Order.Status.CONFIRMED: "Confirmed",
    Order.Status.SHIPPED: "Shipped",
    Order.Status.DELIVERED: "Delivered",
    Order.Status.CANCELLED: "Cancelled",
}


class StatusAdminFilter(admin.SimpleListFilter):
    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return list(STATUS_LABELS_EN.items())

    def queryset(self, request, queryset):
        return queryset.filter(status=self.value()) if self.value() else queryset


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status_en", "total", "whatsapp_notified", "created_at")
    list_filter = (StatusAdminFilter, "whatsapp_notified")
    search_fields = ("id", "user__username", "user__email")
    inlines = [OrderItemInline]
    actions = ["cancel_orders", "resend_whatsapp"]

    @admin.display(description="Status")
    def status_en(self, obj):
        return STATUS_LABELS_EN.get(obj.status, obj.status)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        # Swap the dropdown's labels to English when editing an order in
        # admin — the stored value ("shipped", "delivered", ...) is
        # unchanged, so the site's own Turkish get_status_display() is
        # unaffected.
        if db_field.name == "status":
            kwargs["choices"] = list(STATUS_LABELS_EN.items())
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    @admin.action(description="Cancel selected orders (restocks items)")
    def cancel_orders(self, request, queryset):
        for order in queryset:
            order.cancel()

    @admin.action(description="Resend WhatsApp notification")
    def resend_whatsapp(self, request, queryset):
        from .whatsapp import send_order_notification

        sent = 0
        for order in queryset:
            if send_order_notification(order):
                sent += 1
        self.message_user(request, f"WhatsApp notification sent for {sent} of {queryset.count()} order(s).")