# Path: pms_app/models/company.py
from __future__ import annotations

from datetime import datetime

from pms_app.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


class Company(db.Model):
    """
    Tenant/Company:
    - هر شرکت پلن/اشتراک خودش را دارد
    - کاربران (به جز owner) باید company_id داشته باشند
    """

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)

    # optional: plan relation (در صورت استفاده از Plan)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=True)

    # ایجادکننده شرکت (معمولاً company_admin)
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow, index=True
    )

    # Relationships
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="created_companies",
        lazy="joined",
    )

    users = db.relationship(
        "User",
        back_populates="company",
        foreign_keys="User.company_id",
        lazy="dynamic",
    )

    # FIXED: remove backref (it was creating Plan.companies and conflicting with Plan model)
    plan = db.relationship(
        "Plan",
        back_populates="companies",
        foreign_keys=[plan_id],
        lazy="joined",
    )

    __table_args__ = (
        db.Index("ix_companies_active_name", "is_active", "name"),
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r} active={self.is_active}>"