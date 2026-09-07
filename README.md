# Shop Project (Django + MySQL + Tailwind)

Yapay Çiçek Depso online store — a complete project featuring authentication, a
database-backed shopping cart, tiered (wholesale) pricing, automatic inventory
management, WhatsApp notifications for new orders, and an admin panel.

## Quick Start (Windows)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Installing MySQL on Windows is no longer a hassle — the project uses **PyMySQL**
> (a pure-Python package) instead of `mysqlclient`, so `pip install` works without
> requiring a compiler or Visual Studio.

```powershell
copy .env.example .env            # fill in the values (SECRET_KEY, DB_*, WHATSAPP_*)
```

Create a MySQL database (using the `utf8mb4` character set for proper support of
Turkish/Persian characters):

If you haven't installed MySQL Server yet, install it via the
[MySQL Installer for Windows](https://dev.mysql.com/downloads/installer/), or if you
already have XAMPP/Laragon, the bundled MySQL/MariaDB is sufficient. Once installed,
run the following command using **MySQL Workbench** or **Command Prompt** (if you've
added `mysql` to your PATH):

```sql
CREATE DATABASE shop_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```powershell
npm install
npm run build:css                 # or npm run watch:css during development

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then visit `http://127.0.0.1:8000`, and the admin panel at
`http://127.0.0.1:8000/admin/`.

## WhatsApp Integration (WhatsApp Business Cloud API)

Whenever a customer completes checkout, an automatic message is sent to the store's
WhatsApp number containing the order number, customer name, total amount, and a
direct link to that order's page in the admin panel.

**One-time setup (complete these steps in Meta Business Manager before this will work):**

1. Create/verify a WhatsApp Business Account and phone number: https://business.facebook.com
2. In WhatsApp Manager, under **Message Templates**, create a new template with the
   name you set in `.env` (default: `new_order_alert`), set its category to
   `Utility`, and use the following body text (exactly as shown, with 4 placeholders):
   ```
   New order #{{1}} from {{2}} — total {{3}} TRY. Details: {{4}}
   ```
   Then submit it for Meta approval (this usually takes anywhere from a few minutes
   to a full day).
3. Fill in the following values in `.env`:
   - `WHATSAPP_PHONE_NUMBER_ID` — from the API Setup page of the Meta app
   - `WHATSAPP_ACCESS_TOKEN` — generate a **permanent token** (not the 24-hour
     temporary token)
   - `WHATSAPP_ADMIN_PHONE` — the WhatsApp number that should receive notifications,
     in international format without a `+` (e.g., `905XXXXXXXXX`)
   - `SITE_BASE_URL` — the site's real domain (used for the link inside the message)

If sending the message fails for any reason (invalid token, template not yet
approved, network outage, etc.), **the order is still placed successfully** — only
the "Whatsapp notified" column for that order remains `False` in the admin panel,
and you can retry it at any time using the **"Resend WhatsApp notification"** action
in the order list.

## What's Completed

- **accounts** — custom user model (phone/address), registration, login, logout,
  profile
- **products** — listing, categories, product details, search, pagination
- **cart** — database-backed shopping cart (for both logged-in and guest users),
  automatic guest-cart merging on login, automatic tiered pricing based on quantity
- **orders** — checkout, order history, order cancellation (with automatic
  inventory restoration), **automatic WhatsApp notification for new orders**
- Inventory deduction/restoration using row locking (`select_for_update`) to
  prevent overselling on concurrent orders
- Responsive Tailwind templates (header, footer, product cards, etc.)

## Important Technical Notes

- `AUTH_USER_MODEL = "accounts.User"` — set before the first migration (difficult
  to change later)
- The shopping cart works for both guest users (session-based) and logged-in
  users; carts are merged automatically on login
- The site language (customer-facing text, order status, etc.) is **Turkish**; the
  admin panel at `/admin/` is always displayed in **English** independently
  (`config/middleware.py: AdminLanguageMiddleware`), regardless of the overall
  `LANGUAGE_CODE` setting. Note: a few choice labels shared between the admin panel
  and customer-facing pages (such as order status "Kargoda" and product badges)
  were intentionally left in Turkish, since customers see that same field.
- For production, be sure to set `DEBUG=False` and a long, randomly generated
  `SECRET_KEY` — with `DEBUG=False`, security settings (`SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, HSTS) are enabled automatically.

## Changelog

| # | Change | Reason |
|---|---|---|
| 1 | Database switched from PostgreSQL to **MySQL**, using **PyMySQL** (not `mysqlclient`) so it installs on Windows without a compiler | Explicit project requirement + Windows OS |
| 2 | Full **WhatsApp Business Cloud API** integration added to the checkout flow | The project's most important feature, previously nonexistent |
| 3 | Added `whatsapp_notified` field + "Resend WhatsApp notification" admin action | So an order isn't lost if message sending fails |
| 4 | Admin panel in English, customer-facing site in Turkish (`AdminLanguageMiddleware`) | Explicit requirement |
| 5 | Removed the "Wishlist" button | The button had no backend/JavaScript behind it; clicking it did nothing |
| 6 | The cart context processor no longer creates a Cart/Session row for every anonymous visit | Prevents unnecessary database growth under high traffic |
| 7 | Production security settings (`SECURE_SSL_REDIRECT`, etc.) enabled when `DEBUG=False` | Preparation for a real production launch |
