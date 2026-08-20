# Path: pms_app/utils/plans.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Plan:
    key: str
    title_fa: str
    price_from_toman_monthly: Optional[int]  # None => تماس بگیرید/سفارشی
    annual_discount_percent: Optional[int]   # None => ندارد
    max_users: Optional[int]                 # None => نامحدود
    max_active_projects: Optional[int]       # None => نامحدود
    max_active_contracts: Optional[int]      # None => نامحدود
    notes_fa: str = ""


PLANS: dict[str, Plan] = {
    "free": Plan(
        key="free",
        title_fa="رایگان",
        price_from_toman_monthly=0,
        annual_discount_percent=None,
        max_users=2,
        max_active_projects=1,
        max_active_contracts=1,
        notes_fa="مناسب شروع و تست سیستم (محدود).",
    ),
    "bronze": Plan(
        key="bronze",
        title_fa="برنزی",
        price_from_toman_monthly=3_000_000,
        annual_discount_percent=20,
        max_users=5,
        max_active_projects=10,
        max_active_contracts=10,
        notes_fa="برای تیم‌های کوچک با رشد تدریجی و محدودیت منطقی.",
    ),
    "silver": Plan(
        key="silver",
        title_fa="نقره‌ای",
        price_from_toman_monthly=None,
        annual_discount_percent=None,
        max_users=None,
        max_active_projects=None,
        max_active_contracts=None,
        notes_fa="نامحدود + مناسب تیم‌های حرفه‌ای.",
    ),
    "gold": Plan(
        key="gold",
        title_fa="طلایی",
        price_from_toman_monthly=None,
        annual_discount_percent=None,
        max_users=None,
        max_active_projects=None,
        max_active_contracts=None,
        notes_fa="نامحدود + پشتیبانی ویژه/سفارشی‌سازی.",
    ),
}

PLAN_ORDER = ["free", "bronze", "silver", "gold"]
PAID_PLANS = {"bronze", "silver", "gold"}

LEGACY_PLAN_MAP: dict[str, str] = {
    "pro": "silver",
    "pro_trial": "silver",
}


def normalize_plan(plan: str | None) -> str:
    p = (plan or "").strip().lower()
    if not p:
        return "free"
    if p in LEGACY_PLAN_MAP:
        return LEGACY_PLAN_MAP[p]
    if p not in PLANS:
        return "free"
    return p


def plan_info(plan: str | None) -> Plan:
    return PLANS[normalize_plan(plan)]


def is_paid_plan(plan: str | None) -> bool:
    return normalize_plan(plan) in PAID_PLANS


def annual_price_from_monthly(
    monthly_from: Optional[int],
    discount_percent: Optional[int],
) -> Optional[int]:
    if monthly_from is None:
        return None

    monthly = int(monthly_from)
    if monthly <= 0:
        return 0

    discount = int(discount_percent or 0)
    discount = max(0, min(discount, 90))

    full_year = monthly * 12
    return int(full_year * (100 - discount) / 100)


@dataclass(frozen=True)
class Limits:
    max_users: Optional[int]
    active_projects: Optional[int]
    active_contracts: Optional[int]

    # --- Compatibility aliases ---
    @property
    def max_active_projects(self) -> Optional[int]:
        return self.active_projects

    @property
    def max_active_contracts(self) -> Optional[int]:
        return self.active_contracts

    @property
    def projects(self) -> Optional[int]:
        return self.active_projects

    @property
    def contracts(self) -> Optional[int]:
        return self.active_contracts


def limits_for(plan_key: str | None) -> Limits:
    key = normalize_plan(plan_key)
    p = PLANS[key]
    return Limits(
        max_users=p.max_users,
        active_projects=p.max_active_projects,
        active_contracts=p.max_active_contracts,
    )


FREE_LIMITS = limits_for("free")
BRONZE_LIMITS = limits_for("bronze")
SILVER_LIMITS = limits_for("silver")
GOLD_LIMITS = limits_for("gold")
PRO_LIMITS = SILVER_LIMITS