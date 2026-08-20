# Path: pms_app/blueprints/users/__init__.py
from __future__ import annotations

from flask import Blueprint

# ایجاد Blueprint با نام "users"
# نام blueprint باید با چیزی که در url_for استفاده می‌شود هماهنگ باشد
bp = Blueprint(
    name="users",
    import_name=__name__,
    url_prefix=None,           # اگر می‌خواهی پیشوند URL داشته باشه، اینجا بگذار (مثلاً "/users")
    template_folder="templates",  # اختیاری – اگر قالب‌ها داخل این blueprint باشند
    static_folder="static",       # اختیاری – اگر فایل‌های استاتیک داری
)

# ایمپورت routes بعد از تعریف bp (برای جلوگیری از circular import)
from . import routes  # noqa: E402,F401