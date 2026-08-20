# Path: pms_app/blueprints/auth/helpers/captcha.py
from __future__ import annotations

import secrets

from flask import session


def _new_captcha() -> tuple[int, int, int]:
    a = secrets.randbelow(9) + 1
    b = secrets.randbelow(9) + 1
    return a, b, a + b


def ensure_captcha(regenerate: bool = False) -> None:
    if (
        regenerate
        or session.get("captcha_a") is None
        or session.get("captcha_b") is None
        or session.get("captcha_correct") is None
    ):
        a, b, correct = _new_captcha()
        session["captcha_a"] = a
        session["captcha_b"] = b
        session["captcha_correct"] = correct


def verify_captcha(answer_raw: str) -> bool:
    expected = session.get("captcha_correct")
    try:
        return expected is not None and int(answer_raw) == int(expected)
    except (ValueError, TypeError):
        return False


def clear_captcha() -> None:
    for key in ("captcha_a", "captcha_b", "captcha_correct"):
        session.pop(key, None)