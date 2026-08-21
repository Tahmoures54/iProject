# Path: pms_app/config/production.py
from __future__ import annotations

import os

from .base import BaseConfig


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    # Prefer PostgreSQL in production via DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or BaseConfig.SQLALCHEMY_DATABASE_URI

    # Harden cookies
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Prefer strong SECRET_KEY from env (BaseConfig already reads it)
    # WTF CSRF
    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", "3600"))

    # SQLAlchemy engine options for Postgres under load
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "280")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    }
