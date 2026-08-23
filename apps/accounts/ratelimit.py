"""
Lightweight cache-based rate limiting for the login and register endpoints.

Uses Django's default cache (LocMemCache, no extra config needed) instead of
adding a dependency like django-axes. Good enough for a single-process
deployment; if the app later runs behind multiple gunicorn/uwsgi workers,
point CACHES at Redis/Memcached in settings.py so the counters are shared
across processes — LocMemCache state is per-process and won't work correctly
otherwise.
"""
from django.core.cache import cache

LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60  # 15 minutes

REGISTER_MAX_ATTEMPTS = 5
REGISTER_WINDOW_SECONDS = 60 * 60  # 1 hour


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _login_key(request, identifier):
    return f"login_lock:{_client_ip(request)}:{identifier.lower()}"


def is_login_locked(request, identifier):
    return cache.get(_login_key(request, identifier), 0) >= LOGIN_MAX_ATTEMPTS


def register_login_failure(request, identifier):
    key = _login_key(request, identifier)
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, LOGIN_LOCKOUT_SECONDS)
    return attempts


def clear_login_failures(request, identifier):
    cache.delete(_login_key(request, identifier))


def _register_key(request):
    return f"register_rate:{_client_ip(request)}"


def is_register_rate_limited(request):
    return cache.get(_register_key(request), 0) >= REGISTER_MAX_ATTEMPTS


def register_attempt(request):
    key = _register_key(request)
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, REGISTER_WINDOW_SECONDS)
    return attempts
