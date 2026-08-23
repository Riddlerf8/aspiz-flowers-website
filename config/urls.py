from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("products/", include("apps.products.urls")),
    path("cart/", include("apps.cart.urls")),
    path("orders/", include("apps.orders.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
elif settings.SERVE_MEDIA_VIA_DJANGO:
    # Static files are now handled by WhiteNoiseMiddleware (see settings.py)
    # even outside DEBUG, so only MEDIA (user uploads) needs a URL route
    # here in production.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)