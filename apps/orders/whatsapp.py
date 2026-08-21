"""
Sends a "new order" alert to the shop's WhatsApp number using the official
WhatsApp Business Cloud API (Meta), whenever a customer completes checkout.

Why a message TEMPLATE instead of a free-form message
-------------------------------------------------------
WhatsApp only allows a business to freely message a phone number that has
messaged the business FIRST within the last 24 hours ("customer service
window"). Since it's the *shop's own* number receiving this alert (not the
customer), that window is essentially never open, so the message must use a
pre-approved message template — a fixed layout with a few numbered
placeholders ({{1}}, {{2}}, ...). Template text/placeholders cannot contain
newline characters, so the template keeps things short and links out to the
full order in Django Admin for details.

One-time setup (do this in Meta Business Manager before this works):
1. Create/verify a WhatsApp Business Account + phone number.
2. In WhatsApp Manager -> Message Templates, create a template named to
   match WHATSAPP_ORDER_TEMPLATE_NAME (default: "new_order_alert"),
   category "Utility", with a body like:
       "New order #{{1}} from {{2}} — total {{3}} TRY. Details: {{4}}"
   Submit it for approval (usually approved within minutes to a day).
3. Put WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_ADMIN_PHONE
   in your .env (see .env.example for where to find each value).

This module fails SAFE: if the API call errors for any reason (bad token,
template not approved yet, network issue), checkout still completes
normally and the order is saved — we log the failure and flag the order so
staff can notice it in /admin/ and hit "Resend WhatsApp notification".
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _order_summary_line(order):
    items = list(order.items.select_related("product")[:3])
    summary = ", ".join(f"{item.quantity}x {item.product.name}" for item in items)
    remaining = order.items.count() - len(items)
    if remaining > 0:
        summary += f" +{remaining} more"
    return summary or "-"


def send_order_notification(order):
    """
    Sends the new-order WhatsApp template message. Returns True on success,
    False on any failure (already logged). Never raises.
    """
    if not (settings.WHATSAPP_PHONE_NUMBER_ID and settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_ADMIN_PHONE):
        logger.warning("WhatsApp notification skipped for order #%s: WhatsApp settings not configured.", order.pk)
        return False

    order_link = f"{settings.SITE_BASE_URL}/admin/orders/order/{order.pk}/change/"
    customer_name = order.user.get_full_name() or order.user.username

    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
        f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": settings.WHATSAPP_ADMIN_PHONE,
        "type": "template",
        "template": {
            "name": settings.WHATSAPP_ORDER_TEMPLATE_NAME,
            "language": {"code": settings.WHATSAPP_TEMPLATE_LANGUAGE},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(order.pk)},
                        {"type": "text", "text": customer_name},
                        {"type": "text", "text": str(order.total)},
                        {"type": "text", "text": order_link},
                    ],
                }
            ],
        },
    }
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("WhatsApp notification failed for order #%s.", order.pk)
        return False

    order.whatsapp_notified = True
    order.save(update_fields=["whatsapp_notified"])
    return True
