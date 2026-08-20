# Path: pms_app/extensions.py
from __future__ import annotations

from typing import Optional, Tuple

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHash,
    VerificationError,
    VerifyMismatchError,
)
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# Flask extensions (initialized in app factory)
db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
login_manager: LoginManager = LoginManager()
csrf: CSRFProtect = CSRFProtect()

# Where to redirect for @login_required (these are safe to set before init_app)
login_manager.login_view = "auth.login"
login_manager.login_message = "برای دسترسی به این صفحه ابتدا وارد شوید."
login_manager.login_message_category = "info"

# Argon2 hasher
ph = PasswordHasher()


def init_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions. Call this inside your create_app factory.
    """
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # initialize migrate with app and db
    migrate.init_app(app, db)


# -----------------------
# Password hashing helpers
# -----------------------
def generate_password_hash(raw: str) -> str:
    """
    Hash a plaintext password using Argon2.
    Raises ValueError if raw is None.
    """
    if raw is None:
        raise ValueError("Password cannot be None")
    return ph.hash(raw)


def check_password_hash(hash_str: str, raw: str) -> bool:
    """
    Verify a password against an Argon2 hash.
    Returns True if the password matches, False otherwise.
    """
    if not hash_str or raw is None:
        return False
    try:
        return bool(ph.verify(hash_str, raw))
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False
    except Exception:
        # unexpected error -> treat as False but log at caller if needed
        return False


def verify_password_hash(hash_str: str, raw: str) -> Tuple[bool, Optional[str]]:
    """
    Verify password and optionally return a new hash if rehash is needed.
    Returns tuple (ok: bool, new_hash_or_none: Optional[str]).

    Example usage:
        ok, new_hash = verify_password_hash(self.password_hash, password)
        if ok and new_hash:
            self.password_hash = new_hash
            db.session.commit()
    """
    if not hash_str or raw is None:
        return (False, None)

    try:
        ok = bool(ph.verify(hash_str, raw))
        if not ok:
            return (False, None)

        # If Argon2 parameters changed, request a rehash
        if ph.check_needs_rehash(hash_str):
            return (True, ph.hash(raw))

        return (True, None)

    except (VerifyMismatchError, VerificationError, InvalidHash):
        return (False, None)
    except Exception:
        return (False, None)


# -----------------------
# CSRF helpers
# -----------------------
def csrf_exempt(view):
    """
    Convenience wrapper to mark a view as CSRF-exempt:
        @bp.post("/webhook")
        @csrf_exempt
        def webhook(): ...
    """
    return csrf.exempt(view)


__all__ = [
    "db",
    "migrate",
    "login_manager",
    "csrf",
    "ph",
    "init_extensions",
    "generate_password_hash",
    "check_password_hash",
    "verify_password_hash",
    "csrf_exempt",
]