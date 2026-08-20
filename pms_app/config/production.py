# Path: pms_app/config/production.py
from __future__ import annotations

import os

from .base import BaseConfig


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    # In production you typically set DATABASE_URL to PostgreSQL (or similar).
    # We still accept SQLITE, but it's not recommended for production.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or BaseConfig.SQLALCHEMY_DATABASE_URI

    # Optional: make cookies safer in prod (adjust as needed)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SAMESITE = "Lax"