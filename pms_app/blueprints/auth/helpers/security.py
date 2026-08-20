# Path: pms_app/blueprints/auth/helpers/security.py
from __future__ import annotations

from urllib.parse import urljoin, urlparse

from flask import request

FA_TO_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def is_safe_redirect_url(target: str) -> bool:
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ("http", "https")) and (ref_url.netloc == test_url.netloc)


def normalize_otp(code: str) -> str:
    s = (code or "").strip().translate(FA_TO_EN)
    return "".join(ch for ch in s if ch.isdigit())


def normalize_digits(s: str) -> str:
    return (s or "").strip().translate(FA_TO_EN)


def get_client_ip() -> str:
    xff = (request.headers.get("X-Forwarded-For") or "").strip()
    if xff:
        return xff.split(",")[0].strip()
    return (request.remote_addr or "").strip()


def get_user_agent() -> str:
    return (request.user_agent.string or "").strip()[:255]