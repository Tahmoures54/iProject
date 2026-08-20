# Path: pms_app/utils/helpers.py
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from flask import flash


def now_utc() -> datetime:
    """UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def normalize_str(value: Any, *, default: str = "") -> str:
    """Safe string normalize: None -> default, trim, collapse whitespace."""
    if value is None:
        return default
    s = str(value).strip()
    return " ".join(s.split())


def coerce_bool(value: Any, default: bool = False) -> bool:
    """Convert common truthy/falsey values to bool."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y", "on", "بله", "بلی"}:
        return True
    if s in {"0", "false", "no", "n", "off", "خیر", "نه"}:
        return False
    return default


def safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or value == "":
            return default
        return int(str(value).strip())
    except Exception:
        return default


def safe_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    try:
        if value is None or value == "":
            return default
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return default
    except Exception:
        return default


def parse_csv_list(value: Any) -> list[str]:
    """
    Parse a CSV-ish string to list of trimmed values.
    Example: "a, b ,c" -> ["a","b","c"]
    """
    if value is None:
        return []
    s = str(value).strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]


def unique_list(items: Iterable[Any]) -> list[Any]:
    """Preserve order unique list."""
    seen: set[Any] = set()
    out: list[Any] = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def flash_form_errors(form, category: str = "danger") -> None:
    """
    Flash WTForms errors in a simple, user-friendly way.
    """
    try:
        for field_name, errors in (getattr(form, "errors", {}) or {}).items():
            for err in errors:
                flash(f"{field_name}: {err}", category)
    except Exception:
        # If something unexpected happens, don't crash the request
        flash("فرم نامعتبر است.", category)


def ensure_rbac_seed() -> None:
    """
    Convenience wrapper so code can import ensure_rbac_seed from:
      - pms_app.utils.helpers.ensure_rbac_seed
    Actual implementation lives in pms_app.utils.security.
    """
    from pms_app.utils.security import ensure_rbac_seed as _seed  # local import to avoid cycles

    _seed()