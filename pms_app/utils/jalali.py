# Path: pms_app/utils/jalali.py
"""
Jalali (Solar / Persian) calendar helpers.

Storage remains Gregorian (date / datetime) in the database.
Conversion is used for:
- display in UI
- S-Curve / report labels
- optional parsing of Jalali input strings
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

try:
    import jdatetime
except ImportError:  # pragma: no cover
    jdatetime = None  # type: ignore

DateLike = Union[date, datetime, str, None]

# Persian month names
JALALI_MONTHS = (
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
)

JALALI_WEEKDAYS = (
    "شنبه",
    "یکشنبه",
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
)


def _ensure_jdatetime():
    if jdatetime is None:
        raise RuntimeError(
            "پکیج jdatetime نصب نیست. اجرا کنید: pip install jdatetime"
        )


def to_jalali(value: DateLike) -> Optional["jdatetime.date"]:
    """Convert Gregorian date/datetime/str to jdatetime.date."""
    if value is None:
        return None
    _ensure_jdatetime()

    if isinstance(value, datetime):
        g = value.date()
    elif isinstance(value, date):
        g = value
    elif isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        # try ISO first
        try:
            if "T" in value or " " in value:
                g = datetime.fromisoformat(value.replace("Z", "")).date()
            else:
                g = date.fromisoformat(value[:10])
        except ValueError:
            # try Jalali string already
            parsed = parse_jalali(value)
            return parsed
    else:
        return None

    return jdatetime.date.fromgregorian(date=g)


def to_gregorian(jy: int, jm: int, jd: int) -> date:
    """Convert Jalali y/m/d to Gregorian date."""
    _ensure_jdatetime()
    return jdatetime.date(jy, jm, jd).togregorian()


def parse_jalali(text: str) -> Optional["jdatetime.date"]:
    """
    Parse common Jalali formats:
    - 1403/01/15
    - 1403-01-15
    - 14030115
    """
    if not text:
        return None
    _ensure_jdatetime()
    text = text.strip().replace(".", "/").replace("-", "/")
    parts = text.split("/")
    try:
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return jdatetime.date(y, m, d)
        if len(text) == 8 and text.isdigit():
            y, m, d = int(text[0:4]), int(text[4:6]), int(text[6:8])
            return jdatetime.date(y, m, d)
    except (ValueError, TypeError):
        return None
    return None


def parse_jalali_to_gregorian(text: str) -> Optional[date]:
    """Parse Jalali string → Gregorian date (for form input)."""
    j = parse_jalali(text)
    if j is None:
        return None
    return j.togregorian()


def format_jalali(
    value: DateLike,
    fmt: str = "%Y/%m/%d",
    *,
    with_month_name: bool = False,
) -> str:
    """
    Format a Gregorian date as Jalali string.

    fmt uses jdatetime strftime codes, e.g.:
      %Y/%m/%d  → 1403/06/29
      %Y-%m-%d
    If with_month_name=True → "۲۹ شهریور ۱۴۰۳"
    """
    j = to_jalali(value)
    if j is None:
        return "—"

    if with_month_name:
        return f"{j.day} {JALALI_MONTHS[j.month - 1]} {j.year}"

    try:
        return j.strftime(fmt)
    except Exception:
        return f"{j.year:04d}/{j.month:02d}/{j.day:02d}"


def format_jalali_month(value: DateLike) -> str:
    """Short label for charts: 1403/06"""
    j = to_jalali(value)
    if j is None:
        return ""
    return f"{j.year}/{j.month:02d}"


def format_jalali_month_name(value: DateLike) -> str:
    """e.g. شهریور ۱۴۰۳"""
    j = to_jalali(value)
    if j is None:
        return ""
    return f"{JALALI_MONTHS[j.month - 1]} {j.year}"


def jalali_today() -> "jdatetime.date":
    _ensure_jdatetime()
    return jdatetime.date.today()


def days_between(start: DateLike, end: DateLike) -> Optional[int]:
    """Calendar day difference (Gregorian under the hood – same for both calendars)."""
    j1 = to_jalali(start)
    j2 = to_jalali(end)
    if j1 is None or j2 is None:
        return None
    g1 = j1.togregorian()
    g2 = j2.togregorian()
    return (g2 - g1).days


def add_jalali_months(value: DateLike, months: int) -> Optional[date]:
    """Add months in Jalali calendar, return Gregorian date."""
    j = to_jalali(value)
    if j is None:
        return None
    _ensure_jdatetime()
    # jdatetime supports replace; handle year overflow manually
    y, m, d = j.year, j.month, j.day
    m += months
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    # clamp day to month length
    for day in range(d, 0, -1):
        try:
            return jdatetime.date(y, m, day).togregorian()
        except ValueError:
            continue
    return None
