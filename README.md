# iProject — سامانه هوشمند کنترل پروژه و CBS

**iProject** یک پلتفرم تحت وب حرفه‌ای برای **مدیریت و کنترل پروژه** است که بر اساس استانداردهای روز دنیا (WBS، CBS و Earned Value Management) طراحی شده است.

مناسب شرکت‌های مهندسی، پیمانکاری، مشاور و سازمان‌هایی که نیاز به کنترل دقیق پیشرفت فیزیکی، زمانی و مالی پروژه‌ها همراه با مدیریت قرارداد و صورت‌وضعیت دارند.

---

## امکانات اصلی

### کنترل پروژه (Project Controls)
- ساختار شکست کار (**WBS**) و ساختار شکست هزینه (**CBS**)
- پشتیبانی از **Earned Value Management (EVM)**
  - شاخص‌های CPI، SPI، EAC، TCPI و ...
- داشبوردهای لحظه‌ای پیشرفت فیزیکی، زمانی و مالی
- ردیابی انحرافات و هشدارها

### مدیریت قرارداد و آیتم‌ها
- ثبت قرارداد، الحاقیه و صورت‌وضعیت
- مدیریت آیتم‌های قراردادی در سطح قرارداد
- **Import از Excel** و **Export به CSV**
- محاسبات خودکار مبالغ و پیشرفت

### امنیت و دسترسی
- احراز هویت کامل (ثبت‌نام، ورود، فراموشی رمز، تغییر رمز)
- احراز هویت دو مرحله‌ای (**2FA**)
- **RBAC** با نقش‌های: مالک سیستم، ادمین شرکت، مدیر پروژه، پیمانکار، مشاهده‌گر و ...
- Multi-tenancy بر اساس شرکت (جداسازی کامل داده‌ها)

### سایر قابلیت‌ها
- صفحات عمومی (Home، About، Help، Terms، Privacy)
- سیستم اشتراک و پلن‌های پولی (رایگان، برنز، نقره، طلا)
- پشتیبانی از SMS
- تست‌ها با pytest
- آماده استقرار با Docker و Gunicorn

---

## ساختار پروژه

```
iProject/
├── app.py                 # نقطه ورود اصلی
├── pms_app/
│   ├── blueprints/        # ماژول‌های auth, projects, contracts, items, billing, users, reports, main
│   ├── models/            # مدل‌های User, Company, Project, Contract, ContractItem, Subscription, ...
│   ├── templates/         # قالب‌های Jinja2
│   ├── static/            # CSS, JS, تصاویر
│   ├── utils/             # امنیت، entitlement، SMS، پلن‌ها
│   └── config/            # تنظیمات development / production / testing
├── migrations/            # Alembic
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## پیش‌نیازها

- Python 3.10+
- PostgreSQL (توصیه برای production) یا SQLite (توسعه)
- Docker (اختیاری اما توصیه می‌شود)

---

## نصب سریع (توسعه)

```bash
git clone https://github.com/Tahmoures54/iProject.git
cd iProject

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

فایل `.env` را بسازید (نمونه در `.env.example`):

```dotenv
PMS_ENV=development
FLASK_DEBUG=1
SECRET_KEY=change-me-to-a-strong-secret
SQLALCHEMY_DATABASE_URI=sqlite:///instance/pms.db
HOST=127.0.0.1
PORT=5000
AUTO_DB_UPGRADE=1
```

اجرا:

```bash
python app.py
```

سپس به آدرس زیر بروید:  
http://127.0.0.1:5000

---

## استقرار Production (توصیه)

- **WSGI**: Gunicorn
- **Reverse Proxy**: Nginx
- **دیتابیس**: PostgreSQL
- **Container**: Docker + docker-compose

```bash
docker compose up -d --build
```

حتماً:
- `SECRET_KEY` قوی تنظیم کنید
- SSL فعال باشد
- فایل `.env` را هرگز commit نکنید

---

## تست‌ها

```bash
pytest -q
```

---

## نقش‌ها و دسترسی‌ها (RBAC)

| نقش              | توضیح                              |
|------------------|------------------------------------|
| owner            | مالک کامل پلتفرم                   |
| admin            | ادمین سیستم                        |
| company_admin    | مدیر شرکت (دسترسی کامل شرکت)      |
| manager          | مدیر پروژه                         |
| contractor       | پیمانکار (دسترسی محدود به پروژه)  |
| viewer           | فقط مشاهده                         |

---

## استانداردهای پشتیبانی‌شده

- **WBS** (Work Breakdown Structure)
- **CBS** (Cost Breakdown Structure)
- **EVM** (Earned Value Management)
- مدیریت قرارداد و صورت‌وضعیت مطابق نیازهای پروژه‌های پیمانکاری ایران

---

## مجوز

این پروژه برای استفاده داخلی و تجاری طراحی شده است. در صورت نیاز به لایسنس خاص، با مالک پروژه هماهنگ کنید.

---

**iProject** — کنترل پروژه را حرفه‌ای کنید.
