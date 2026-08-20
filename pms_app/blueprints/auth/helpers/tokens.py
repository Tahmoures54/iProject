# Path: pms_app/blueprints/auth/helpers/tokens.py
from __future__ import annotations

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from pms_app.models.user import User

RESET_SALT = "pms-reset-salt"


def _serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY is not set in Flask config.")
    return URLSafeTimedSerializer(secret)


def generate_reset_token(user: User) -> str:
    return _serializer().dumps({"uid": int(user.id)}, salt=RESET_SALT)


def verify_reset_token(token: str, max_age_seconds: int = 3600) -> int | None:
    try:
        data = _serializer().loads(token, salt=RESET_SALT, max_age=max_age_seconds)
        return int(data.get("uid"))
    except (SignatureExpired, BadSignature):
        return None


def send_reset_link(email_to: str, link: str) -> None:
    """DEV: print link to console/log."""
    current_app.logger.info("Password reset link for %s: %s", email_to, link)
    if current_app.config.get("DEV_EMAIL_CONSOLE", True):
        print(f"\n=== PASSWORD RESET LINK ===\nTO: {email_to}\nLINK: {link}\n===========================\n")