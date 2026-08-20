# Path: pms_app/blueprints/auth/helpers/subscription.py
from __future__ import annotations

import os

from flask import current_app, flash, redirect, url_for

from pms_app.extensions import db
from pms_app.models.subscription import Subscription
from pms_app.models.user import User
from pms_app.utils.security import is_owner as is_owner_user


def _free_days_default() -> int:
    val = current_app.config.get("FREE_DAYS", os.getenv("FREE_DAYS", "90"))
    try:
        return max(1, int(val))
    except (ValueError, TypeError):
        return 90


def is_company_based() -> bool:
    return hasattr(Subscription, "company_id")


def get_or_create_for_company(*, company_id: int, billing_user_id: int | None) -> Subscription:
    sub = Subscription.query.filter_by(company_id=int(company_id)).one_or_none()
    if sub is not None:
        return sub

    if hasattr(Subscription, "create_free"):
        try:
            sub = Subscription.create_free(company_id=int(company_id), billing_user_id=billing_user_id)
        except TypeError:
            sub = Subscription(company_id=int(company_id), plan="free", status="active")
    else:
        sub = Subscription(company_id=int(company_id), plan="free", status="active")

    if hasattr(sub, "start_free_period"):
        sub.start_free_period(days=_free_days_default())

    db.session.add(sub)
    db.session.flush()
    return sub


def get_or_create_for_user_legacy(user: User) -> Subscription:
    sub = Subscription.query.filter_by(user_id=int(user.id)).one_or_none()
    if sub is not None:
        return sub

    if hasattr(Subscription, "create_free"):
        sub = Subscription.create_free(user_id=int(user.id))
    else:
        sub = Subscription(user_id=int(user.id), plan="free", status="active")

    if hasattr(sub, "start_free_period"):
        sub.start_free_period(days=_free_days_default())

    db.session.add(sub)
    db.session.flush()
    return sub


def enforce_paywall(user: User):
    """Return redirect if paywall triggered, else None."""
    try:
        if is_owner_user(user):
            return None
    except Exception:
        pass

    try:
        if is_company_based():
            company_id = getattr(user, "company_id", None)
            if company_id is None:
                return None
            sub = get_or_create_for_company(
                company_id=int(company_id),
                billing_user_id=int(user.id),
            )
        else:
            sub = get_or_create_for_user_legacy(user)

        if hasattr(sub, "needs_payment") and sub.needs_payment():
            flash("دوره رایگان شما پایان یافته است. برای ادامه استفاده، پلن را خریداری کنید.", "warning")
            return redirect(url_for("billing.pricing"))
    except Exception:
        current_app.logger.exception("Paywall enforcement failed (ignored)")

    return None