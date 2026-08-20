# Path: pms_app/models/subscription.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Optional

from pms_app.extensions import db

PlanKey = Literal["free", "bronze", "silver", "gold"]
LegacyPlanKey = Literal["pro", "pro_trial"]
AnyPlanKey = PlanKey | LegacyPlanKey


def utcnow() -> datetime:
    return datetime.utcnow()


class Subscription(db.Model):
    """
    Subscription باید روی Company باشد (نه روی User).
    """

    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)

    # NEW: شرکت مالک اشتراک
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # OPTIONAL: کاربری که پرداخت/مدیریت اشتراک را انجام می‌دهد (برای لاگ/سازگاری)
    billing_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    plan = db.Column(db.String(20), nullable=False, default="free", index=True)
    status = db.Column(db.String(30), nullable=False, default="active", index=True)

    free_ends_at = db.Column(db.DateTime, nullable=True, index=True)

    trial_started_at = db.Column(db.DateTime, nullable=True)
    trial_ends_at = db.Column(db.DateTime, nullable=True)

    stripe_customer_id = db.Column(db.String(255), nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True, index=True)

    current_period_end = db.Column(db.DateTime, nullable=True, index=True)
    cancel_at_period_end = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow, index=True)

    company = db.relationship("Company", backref=db.backref("subscription", uselist=False), lazy="joined")
    billing_user = db.relationship("User", foreign_keys=[billing_user_id], lazy="joined")

    __table_args__ = (
        db.CheckConstraint(
            "plan in ('free','bronze','silver','gold','pro','pro_trial')",
            name="ck_subscriptions_plan",
        ),
    )

    def __repr__(self) -> str:
        return f"<Subscription company_id={self.company_id} plan={self.plan} status={self.status}>"

    # ---------- Normalization ----------
    @staticmethod
    def normalize_plan(plan: str | None) -> PlanKey:
        p = (plan or "").strip().lower()
        if p in {"pro", "pro_trial"}:
            return "silver"
        if p in {"free", "bronze", "silver", "gold"}:
            return p  # type: ignore[return-value]
        return "free"

    def normalized_plan(self) -> PlanKey:
        return Subscription.normalize_plan(self.plan)

    def normalized_status(self) -> str:
        return (self.status or "").strip().lower()

    # ---------- Constructors ----------
    @staticmethod
    def create_free(company_id: int, billing_user_id: int | None = None) -> "Subscription":
        return Subscription(company_id=int(company_id), billing_user_id=billing_user_id, plan="free", status="active")

    # ---------- Free period ----------
    def start_free_period(self, days: int = 365) -> None:
        now = utcnow()
        self.plan = "free"
        self.status = "active"
        self.free_ends_at = now + timedelta(days=max(int(days), 1))

        self.current_period_end = None
        self.cancel_at_period_end = False

        self.stripe_subscription_id = None
        self.stripe_customer_id = None

    def is_free_period_active(self, now: Optional[datetime] = None) -> bool:
        now = now or utcnow()
        if self.free_ends_at is None:
            return True
        return now < self.free_ends_at

    # ---------- Paid status ----------
    def is_paid_plan(self) -> bool:
        return self.normalized_plan() in {"bronze", "silver", "gold"}

    def _status_allows_access(self) -> bool:
        s = self.normalized_status()
        return s in {"active", "trialing", "past_due"}

    def _within_current_period(self, now: Optional[datetime] = None) -> bool:
        now = now or utcnow()
        if self.current_period_end is None:
            return True
        return now < self.current_period_end

    def is_paid_active(self, now: Optional[datetime] = None) -> bool:
        if not self.is_paid_plan():
            return False
        if not self._status_allows_access():
            return False
        if not self._within_current_period(now=now):
            return False
        return True

    def effective_tier(self, now: Optional[datetime] = None) -> PlanKey:
        now = now or utcnow()
        if self.is_paid_active(now=now):
            return self.normalized_plan()
        return "free"

    def needs_payment(self, now: Optional[datetime] = None) -> bool:
        now = now or utcnow()
        if self.is_paid_active(now=now):
            return False
        if self.free_ends_at is None:
            return False
        return now >= self.free_ends_at

    def set_manual_paid_plan(self, plan: PlanKey, *, days: int = 365) -> None:
        if plan == "free":
            self.start_free_period(days=days)
            return

        self.plan = plan
        self.status = "active"
        self.cancel_at_period_end = False
        self.current_period_end = utcnow() + timedelta(days=max(int(days), 1))

        self.stripe_subscription_id = None
        self.stripe_customer_id = None

    def paid_until(self) -> Optional[datetime]:
        if self.is_paid_plan():
            return self.current_period_end
        return None


__all__ = ["Subscription", "PlanKey", "LegacyPlanKey", "AnyPlanKey"]