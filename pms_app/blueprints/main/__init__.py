# Path: pms_app/blueprints/main/__init__.py

from __future__ import annotations

from flask import Blueprint

# ═══════════════════════════════════════════════════════════════════════════
# 📦 MAIN BLUEPRINT
# ═══════════════════════════════════════════════════════════════════════════

bp = Blueprint(
    "main",                          # نام Blueprint
    __name__,                        # نام ماژول
    template_folder="templates",     # پوشه تمپلیت‌ها (اختیاری)
    url_prefix=""                    # بدون پیشوند (صفحه اصلی)
)

# Import routes بعد از تعریف bp
from . import routes  # noqa: E402, F401