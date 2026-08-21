# Shop Project (Django + MySQL + Tailwind)

فروشگاه آنلاین یاپای چیچک دپسو — پروژه‌ی کامل با احراز هویت، سبد خرید مبتنی بر دیتابیس،
قیمت‌گذاری پله‌ای (عمده‌فروشی)، مدیریت موجودی خودکار، اعلان سفارش جدید به واتساپ، و پنل ادمین.

## راه‌اندازی سریع (ویندوز)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> نصب MySQL روی ویندوز دیگه دردسر نداره — پروژه از `PyMySQL` (پکیج pure-Python) استفاده
> می‌کنه به‌جای `mysqlclient`، پس `pip install` بدون نیاز به کامپایلر یا Visual Studio کار می‌کنه.

```powershell
copy .env.example .env            # مقادیرش رو پر کن (SECRET_KEY, DB_*, WHATSAPP_*)
```

یه دیتابیس MySQL بساز (با کاراکترست utf8mb4 برای پشتیبانی درست از حروف ترکی/فارسی):

اگه هنوز MySQL Server رو نصب نکردی، از [MySQL Installer برای ویندوز](https://dev.mysql.com/downloads/installer/) نصبش کن، یا اگه XAMPP/Laragon داری همون MySQL/MariaDB داخلش کافیه. بعد از نصب، از **MySQL Workbench** یا **Command Prompt** (اگه `mysql` رو به PATH اضافه کرده باشی) این دستور رو بزن:
```sql
CREATE DATABASE shop_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```powershell
npm install
npm run build:css                 # یا npm run watch:css موقع توسعه

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

سپس به آدرس `http://127.0.0.1:8000` برو، و پنل ادمین در `http://127.0.0.1:8000/admin/`.

## اتصال واتساپ (WhatsApp Business Cloud API)

هر وقت کاربر سفارشش رو تکمیل (checkout) می‌کنه، یه پیام خودکار به شماره واتساپ فروشگاه
می‌ره که شامل شماره سفارش، اسم مشتری، مبلغ کل، و لینک مستقیم به صفحه‌ی اون سفارش تو ادمینه.

**راه‌اندازی یک‌باره (قبل از اینکه کار کنه، این مراحل رو تو Meta Business Manager انجام بده):**

1. یه WhatsApp Business Account و شماره تلفن بساز/تأیید کن: https://business.facebook.com
2. تو WhatsApp Manager بخش **Message Templates**، یه تمپلیت جدید بساز با اسمی که تو
   `.env` گذاشتی (پیش‌فرض: `new_order_alert`)، دسته‌ش رو `Utility` بذار، و متن بدنه‌ش
   این باشه (دقیقاً همینطور، ۴ تا placeholder):
   ```
   New order #{{1}} from {{2}} — total {{3}} TRY. Details: {{4}}
   ```
   بعد بفرستش برای تأیید متا (معمولاً چند دقیقه تا یک روز طول می‌کشه).
3. مقادیر زیر رو تو `.env` پر کن:
   - `WHATSAPP_PHONE_NUMBER_ID` — از صفحه‌ی API Setup اپ متا
   - `WHATSAPP_ACCESS_TOKEN` — یه **permanent token** بساز (نه توکن موقت ۲۴ساعته)
   - `WHATSAPP_ADMIN_PHONE` — شماره واتساپی که باید اعلان‌ها رو دریافت کنه، فرمت بین‌المللی بدون `+` (مثلاً `905XXXXXXXXX`)
   - `SITE_BASE_URL` — دامنه واقعی سایت (برای لینک داخل پیام)

اگه ارسال پیام به هر دلیلی fail بشه (توکن اشتباه، تمپلیت هنوز تأیید نشده، قطعی شبکه...)،
**سفارش همچنان با موفقیت ثبت میشه** — فقط تو پنل ادمین ستون "Whatsapp notified" روی سفارش
`False` می‌مونه، و می‌تونی از اکشن **"Resend WhatsApp notification"** تو لیست سفارش‌ها
دوباره امتحانش کنی.

## چیزی که تکمیل شده

- **accounts** — مدل کاربر سفارشی (phone/address)، ثبت‌نام، ورود، خروج، پروفایل
- **products** — لیست، دسته‌بندی، جزئیات محصول، جست‌وجو، صفحه‌بندی
- **cart** — سبد خرید مبتنی بر دیتابیس (برای کاربر لاگین‌کرده و مهمان)، ادغام خودکار سبد مهمان هنگام لاگین، قیمت پله‌ای خودکار بر اساس تعداد
- **orders** — تسویه‌حساب، تاریخچه سفارش، لغو سفارش (با بازگردانی خودکار موجودی)، **اعلان خودکار سفارش جدید به واتساپ**
- کسر/بازگردانی موجودی با قفل ردیف (`select_for_update`) برای جلوگیری از overselling در سفارش‌های همزمان
- تمپلیت‌های Tailwind ریسپانسیو (هدر، فوتر، کارت محصول و ...)

## نکات فنی مهم

- `AUTH_USER_MODEL = "accounts.User"` — قبل از اولین migrate تنظیم شده (تغییرش بعداً سخته)
- سبد خرید هم برای کاربر مهمان (session-based) کار می‌کنه هم کاربر لاگین‌کرده؛ هنگام لاگین سبدها merge می‌شن
- زبان سایت (متن‌های مشتری‌محور، وضعیت سفارش و...) **ترکی**ه؛ پنل ادمین `/admin/` به‌طور جداگانه
  همیشه **انگلیسی** نمایش داده می‌شه (`config/middleware.py: AdminLanguageMiddleware`)، صرف‌نظر از
  `LANGUAGE_CODE` کلی سایت. توجه: چندتا choice-label مشترک بین ادمین و مشتری (مثل وضعیت سفارش:
  "Kargoda" و بج‌های محصول) عمداً ترکی موندن چون همون‌جا رو مشتری هم می‌بینه.
- برای production حتماً `DEBUG=False`، `SECRET_KEY` تصادفی و طولانی تنظیم کن — با `DEBUG=False`،
  تنظیمات امنیتی (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, HSTS) خودکار فعال میشن.

## تغییرات این نسخه (Changelog)

| # | تغییر | چرا |
|---|---|---|
| 1 | دیتابیس از PostgreSQL به **MySQL** تغییر کرد؛ با **PyMySQL** (نه mysqlclient) تا رو ویندوز بدون کامپایلر نصب بشه | درخواست صریح پروژه + سیستم‌عامل ویندوز |
| 2 | اتصال کامل **WhatsApp Business Cloud API** به فرآیند checkout | مهم‌ترین قابلیت پروژه، قبلاً اصلاً وجود نداشت |
| 3 | فیلد `whatsapp_notified` + اکشن "Resend WhatsApp notification" تو ادمین | تا اگه ارسال پیام fail شد، سفارش گم نشه |
| 4 | پنل ادمین انگلیسی، سایت مشتری ترکی (`AdminLanguageMiddleware`) | درخواست صریح |
| 5 | دکمه‌ی "علاقه‌مندی‌ها" (wishlist) حذف شد | دکمه بدون بک‌اند/جاوااسکریپت بود؛ کلیک هیچ اتفاقی نمی‌انداخت |
| 6 | context processor سبد خرید دیگه برای هر بازدید ناشناس، ردیف Cart/Session نمی‌سازه | جلوگیری از رشد بی‌مورد دیتابیس با ترافیک بالا |
| 7 | تنظیمات امنیتی production (`SECURE_SSL_REDIRECT` و...) وقتی `DEBUG=False` است | آماده‌سازی برای انتشار واقعی |
