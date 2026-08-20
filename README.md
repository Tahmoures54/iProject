```md
# PMS (Smart Project Management System)

سامانه تحت وب برای مدیریت **پروژه‌ها، قراردادها و آیتم‌های قراردادی** با Flask.  
این پروژه به صورت ماژولار (Blueprint) پیاده‌سازی شده و شامل RBAC، فرم‌ها، گزارش‌ها، Import/Export و تست‌ها است.

---

## امکانات اصلی

- احراز هویت: ورود/خروج، ثبت‌نام، فراموشی رمز، تغییر رمز
- RBAC: نقش‌ها و مجوزها (admin / pm / engineer / viewer)
- مدیریت پروژه‌ها (Projects)
- مدیریت قراردادها در سطح پروژه (Contracts)
- مدیریت آیتم‌های قراردادی در سطح قرارداد (Items)
  - Import از Excel
  - Export به CSV
- گزارش‌ها (Reports)
- صفحات عمومی: Home / About / Help / Terms / Privacy
- تست‌ها با pytest

---

## ساختار پروژه

```
pms/
├── app.py
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── pms_app/
│   ├── __init__.py
│   ├── blueprints/
│   │   ├── auth/
│   │   ├── contracts/
│   │   ├── items/
│   │   ├── main/
│   │   ├── projects/
│   │   ├── reports/
│   │   └── users/
│   ├── config/
│   ├── extensions.py
│   ├── models/
│   ├── static/
│   ├── templates/
│   └── utils/
├── requirements.txt
└── tests/
```

---

## پیش‌نیازها

- Python 3.10+
- pip

---

## نصب

داخل ریشه پروژه:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
```

---

## تنظیمات محیطی (.env)

فایل `.env` را در ریشه پروژه بساز (این فایل نباید commit شود):

نمونه:

```dotenv
PMS_ENV=development
FLASK_DEBUG=1

SECRET_KEY=change-me-very-secret

# اگر خالی باشد، config از instance/pms.db استفاده می‌کند
SQLALCHEMY_DATABASE_URI=sqlite:///instance/pms.db

HOST=127.0.0.1
PORT=5000

# اجرای خودکار upgrade در dev
AUTO_DB_UPGRADE=1
```

---

## اجرای برنامه

```bash
python app.py
```

سپس در مرورگر:
- http://127.0.0.1:5000

---

## دیتابیس و Migration

### حالت توسعه سریع
در development، برنامه (طبق تنظیمات create_app) اگر جدول‌ها وجود نداشته باشد، `db.create_all()` را اجرا می‌کند و RBAC را seed می‌کند.

### حالت استاندارد (با Alembic)
اگر migration اولیه داری:

```bash
set FLASK_APP=app.py
flask db upgrade
```

اگر مشکل encoding در `migrations/alembic.ini` داشتی (ویندوز):
```bash
python fix_alembic_ini.py
```

---

## RBAC و نقش‌ها

در `pms_app/utils/security.py` نقش‌ها و permissionها تعریف و seed می‌شوند.  
نمونه permissionها:
- `projects.read`, `projects.write`
- `contracts.read`, `contracts.write`
- `items.read`, `items.write`
- `reports.read`
- `users.admin`

---

## 2FA (احراز هویت دو مرحله‌ای)

برای 2FA نیاز به پکیج‌ها:
- `pyotp`
- `qrcode[pil]`
- `Pillow`

در UI:
- کاربر بعد از ورود می‌تواند از مسیر **/enable-2fa** فعال کند.

---

## تست‌ها

```bash
pytest -q
```

---

## نکات امنیتی

- `.env` و `instance/` و `logs/` را commit نکن.
- در production حتماً:
  - `SECRET_KEY` قوی تنظیم شود
  - SSL فعال باشد
  - از WSGI server مثل gunicorn و reverse proxy مثل nginx استفاده شود
  - بهتر است از PostgreSQL به جای SQLite استفاده شود

---

## اجرای Production (پیشنهادی)

- Nginx (Reverse Proxy)
- Gunicorn (WSGI)
- Systemd (Service)
- PostgreSQL (DB)

---

## مجوز / License

این پروژه به صورت داخلی استفاده می‌شود. در صورت نیاز می‌توان License را مشخص کرد.
```