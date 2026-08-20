# Path: pms_app/models/contract.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pms_app.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)

    # NEW: tenant scope (برای فیلتر ساده و جلوگیری از leakage)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    contract_number = db.Column(db.String(80), nullable=False, index=True)
    contract_title = db.Column(db.String(200), nullable=False)
    contractor_name = db.Column(db.String(200), nullable=True)

    contract_type = db.Column(db.String(30), nullable=False)
    pricing_model = db.Column(db.String(30), nullable=False)
    currency = db.Column(db.String(10), nullable=False)

    original_contract_value = db.Column(db.Numeric(18, 2), nullable=True)
    revised_contract_value = db.Column(db.Numeric(18, 2), nullable=True)

    start_date = db.Column(db.Date, nullable=True)
    finish_date = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow, index=True)

    __table_args__ = (
        db.UniqueConstraint("project_id", "contract_number", name="uq_contract_project_number"),
        db.Index("ix_contracts_company_project_status", "company_id", "project_id", "status"),
        db.Index("ix_contracts_finish_date", "finish_date"),
    )

    company = db.relationship("Company", backref=db.backref("contracts", lazy="dynamic"), lazy="joined")
    project = db.relationship("Project", backref=db.backref("contracts", lazy="dynamic"), lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<Contract id={self.id} company_id={self.company_id} number={self.contract_number!r} "
            f"project_id={self.project_id} status={self.status!r}>"
        )

    @property
    def original_value_decimal(self) -> Optional[Decimal]:
        v = self.original_contract_value
        return Decimal(v) if v is not None else None

    @property
    def revised_value_decimal(self) -> Optional[Decimal]:
        v = self.revised_contract_value
        return Decimal(v) if v is not None else None

    @property
    def due_date(self) -> Optional[date]:
        return self.finish_date

    @property
    def is_active_contract(self) -> bool:
        s = (self.status or "").strip().lower()
        return s not in {"closed", "canceled", "cancelled", "terminated", "archived", "completed"}

    def days_to_due(self, today: Optional[date] = None) -> Optional[int]:
        d = self.due_date
        if d is None:
            return None
        today = today or date.today()
        return (d - today).days

    def sms_purpose_due_reminder(self, *, days_before: int) -> str:
        return f"CONTRACT_DUE_REMINDER:{int(self.id)}:{int(days_before)}"