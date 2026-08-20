from __future__ import annotations
import os
from .base import BaseConfig, _normalize_sqlite_uri

class DevelopmentConfig(BaseConfig):
    DEBUG = True

    # ابتدا ببینیم آیا DATABASE_URL یا SQLALCHEMY_DATABASE_URI تنظیم شده است یا خیر
    _dev_db_uri = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")

    # اگر روی Vercel هستیم (متغیر VERCEL=1)، حتماً باید از PostgreSQL استفاده کنیم
    if os.getenv("VERCEL") == "1":
        if not _dev_db_uri:
            raise RuntimeError("DATABASE_URL must be set on Vercel")
        SQLALCHEMY_DATABASE_URI = _dev_db_uri
    else:
        # در محیط محلی: اگر آدرس دیتابیس داده شده بود از همان استفاده کن، وگرنه SQLite
        if _dev_db_uri:
            SQLALCHEMY_DATABASE_URI = _normalize_sqlite_uri(BaseConfig.PROJECT_DIR, _dev_db_uri)
        else:
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{BaseConfig.DB_PATH.as_posix()}"
