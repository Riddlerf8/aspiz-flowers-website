"""
Minimal Google OAuth2 "Sign in with Google" flow, implemented directly with
`requests` (already a project dependency, same pattern as apps/orders/whatsapp.py)
instead of adding django-allauth/social-auth as a new dependency for one button.

One-time setup (do this in Google Cloud Console before this works):
1. console.cloud.google.com -> APIs & Services -> Credentials
2. Create Credentials -> OAuth client ID -> Web application
3. Under "Authorized redirect URIs" add EXACTLY:
       <SITE_BASE_URL>/accounts/google/callback/
   e.g. https://cicekdeposu.com/accounts/google/callback/
   (must match GOOGLE_OAUTH_REDIRECT_URI in settings.py exactly, including
   the trailing slash, or Google will reject the callback)
4. Put the resulting Client ID and Client Secret in .env as
   GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET — the login button
   appears automatically once both are set (see google_oauth_enabled in
   apps/core/context_processors.py).
"""
from urllib.parse import urlencode

import requests
from django.conf import settings

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPES = "openid email profile"


def build_authorization_url(state):
    """
    Builds the URL to redirect the browser to so the user can approve
    access on Google's own consent screen. `state` is an anti-CSRF token
    we generate and store in the session, then verify on callback.
    """
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "prompt": "select_account",
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def exchange_code_for_token(code):
    """Swaps the one-time authorization code for an access token. Raises
    requests.RequestException on failure — the caller decides how to show
    that to the user."""
    response = requests.post(
        TOKEN_ENDPOINT,
        data={
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_userinfo(access_token):
    """Returns {"email": ..., "given_name": ..., "family_name": ..., "email_verified": ...}."""
    response = requests.get(
        USERINFO_ENDPOINT,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
