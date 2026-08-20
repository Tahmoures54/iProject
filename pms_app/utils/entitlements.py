# Path: pms_app/utils/entitlements.py
from __future__ import annotations
from typing import Optional, Tuple
from flask import url_for, current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pms_app.extensions import db
from pms_app.models.subscription import Subscription
from pms_app.utils.plans import BRONZE_LIMITS, FREE_LIMITS, GOLD_LIMITS, SILVER_LIMITS


# ---------------------------------------------------------
# این فایل: محدودیت‌های پلن (Plan limits) را enforce می‌کند
# RBAC/Permission جداگانه در security.py و routeها چک می‌شود
# ---------------------------------------------------------


def _get_user(user_id: int):
    from pms_app.models.user import User  # local import
    return db.session.get(User, int(user_id))


def _get_company_id(user) -> Optional[int]:
    """استاندارد: company_id اولویت دارد"""
    if user is None:
        return None
    return getattr(user, "company_id", None)


def _is_owner_without_company(user) -> bool:
    """مالک پلتفرم بدون شرکت → بای‌پس همه محدودیت‌ها"""
    return bool(getattr(user, "is_owner", False)) and _get_company_id(user) is None


def _scope_subscription_query(user_id: int):
    """فیلتر subscription بر اساس company_id یا legacy user_id"""
    user = _get_user(user_id)
    if user is None:
        return Subscription.query.filter(db.text("1=0"))

    if _is_owner_without_company(user):
        return Subscription.query.filter(db.text("1=0"))

    cid = _get_company_id(user)
    if hasattr(Subscription, "company_id") and cid is not None:
        return Subscription.query.filter(Subscription.company_id == cid)

    if hasattr(Subscription, "user_id"):
        return Subscription.query.filter(Subscription.user_id == user_id)

    return Subscription.query.filter(db.text("1=0"))


def _create_default_subscription(user_id: int) -> Optional[Subscription]:
    """ایجاد subscription پیش‌فرض free اگر وجود نداشت"""
    user = _get_user(user_id)
    if user is None or _is_owner_without_company(user):
        return None

    sub = Subscription(plan="free", status="active")
    cid = _get_company_id(user)

    if hasattr(sub, "company_id") and cid is not None:
        sub.company_id = cid
        if hasattr(sub, "billing_user_id"):
            sub.billing_user_id = user_id
    elif hasattr(sub, "user_id"):
        sub.user_id = user_id
    else:
        return None

    return sub


def _get_or_create_subscription(user_id: int) -> Optional[Subscription]:
    """گرفتن یا ساخت subscription"""
    query = _scope_subscription_query(user_id)
    sub = query.one_or_none()

    if sub is not None:
        return sub

    sub = _create_default_subscription(user_id)
    if sub is None:
        return None

    db.session.add(sub)
    try:
        db.session.flush()
        return sub
    except IntegrityError:
        db.session.rollback()
        query = _scope_subscription_query(user_id)
        return query.one_or_none()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.exception("خطا در ایجاد subscription پیش‌فرض")
        return None


# -----------------------------
# Public API
# -----------------------------


def get_effective_tier(user_id: int) -> str:
    """
    tier موثر:
    - owner بدون شرکت → gold (بای‌پس محدودیت)
    - در غیر این صورت → tier واقعی subscription یا free
    """
    user = _get_user(user_id)
    if user is None:
        return "free"

    if _is_owner_without_company(user):
        return "gold"

    sub = _get_or_create_subscription(user_id)
    if sub is None:
        return "free"

    tier = (sub.effective_tier() or "free").lower().strip()

    # سازگاری legacy
    if tier in {"pro", "pro_trial"}:
        tier = "silver"

    return tier if tier in {"free", "bronze", "silver", "gold"} else "free"


def get_limits_for_tier(tier: str):
    t = tier.lower().strip()
    return {
        "gold": GOLD_LIMITS,
        "silver": SILVER_LIMITS,
        "bronze": BRONZE_LIMITS,
        "free": FREE_LIMITS,
    }.get(t, FREE_LIMITS)


def count_active_users(user_id: int) -> int:
    from pms_app.models.user import User
    cid = _get_company_id(_get_user(user_id))
    if cid is None:
        return 1  # حداقل برای owner یا کاربر بدون شرکت
    return User.query.filter(
        User.company_id == cid,
        User.is_active.is_(True)
    ).count()


def count_active_projects(user_id: int) -> int:
    from pms_app.models.project import Project
    user = _get_user(user_id)
    cid = _get_company_id(user)

    q = Project.query
    if cid is not None and hasattr(Project, "company_id"):
        q = q.filter(Project.company_id == cid)

    excluded_status = ["closed", "completed", "canceled", "cancelled", "archived"]
    if hasattr(Project, "status"):
        q = q.filter(Project.status.notin_(excluded_status))

    return q.count()


def count_active_contracts(user_id: int) -> int:
    from pms_app.models.contract import Contract
    user = _get_user(user_id)
    cid = _get_company_id(user)

    q = Contract.query
    if cid is not None and hasattr(Contract, "company_id"):
        q = q.filter(Contract.company_id == cid)

    excluded_status = ["closed", "completed", "canceled", "cancelled", "archived"]
    if hasattr(Contract, "status"):
        q = q.filter(Contract.status.notin_(excluded_status))

    return q.count()


def can_create(kind: str, user_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    چک محدودیت پلن برای ایجاد resource
    kind: "project" | "contract" | ...
    """
    kind = (kind or "").lower().strip()
    tier = get_effective_tier(user_id)
    limits = get_limits_for_tier(tier)

    user = _get_user(user_id)
    if _is_owner_without_company(user):
        return True, None, None

    upgrade_url = url_for("billing.pricing") if "billing" in current_app.blueprints else None

    if kind == "project":
        max_projects = limits.active_projects
        if max_projects is None:
            return True, None, None
        used = count_active_projects(user_id)
        if used >= max_projects:
            msg = (
                f"سقف پروژه‌های فعال پلن شما پر شده است ({used}/{max_projects}). "
                "برای ایجاد پروژه جدید، یکی را آرشیو کنید یا پلن را ارتقا دهید."
            )
            return False, msg, upgrade_url
        return True, None, None

    if kind == "contract":
        max_contracts = limits.active_contracts
        if max_contracts is None:
            return True, None, None
        used = count_active_contracts(user_id)
        if used >= max_contracts:
            msg = (
                f"سقف قراردادهای فعال پلن شما پر شده است ({used}/{max_contracts}). "
                "برای ایجاد قرارداد جدید، یکی را آرشیو کنید یا پلن را ارتقا دهید."
            )
            return False, msg, upgrade_url
        return True, None, None

    return True, None, None


def can_add_user(user_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """چک محدودیت تعداد کاربران"""
    tier = get_effective_tier(user_id)
    limits = get_limits_for_tier(tier)

    max_users = limits.max_users
    if max_users is None:
        return True, None, None

    used = count_active_users(user_id)
    if used >= max_users:
        upgrade_url = url_for("billing.pricing") if "billing" in current_app.blueprints else None
        msg = (
            f"سقف تعداد کاربران پلن شما پر شده است ({used}/{max_users}). "
            "برای افزودن کاربر جدید، پلن را ارتقا دهید."
        )
        return False, msg, upgrade_url

    return True, None, None