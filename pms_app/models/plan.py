# Path: pms_app/models/plan.py
from __future__ import annotations

from datetime import datetime

from pms_app.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    max_projects = db.Column(db.Integer, default=1)
    max_users = db.Column(db.Integer, default=5)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=utcnow)

    # relation (FIXED: use back_populates instead of backref to avoid name collision)
    companies = db.relationship(
        "Company",
        back_populates="plan",
        lazy="dynamic",  # مشابه چیزی که قبلاً در Company.backref("companies", lazy="dynamic") داشتی
    )

    def __repr__(self) -> str:
        return f"<Plan {self.name}>"