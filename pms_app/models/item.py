# Path: pms_app/models/item.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pms_app.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


class ContractItem(db.Model):
    """
    Contract item / WBS activity – full fields for:
    - WBS hierarchy (L1–L9 + parent)
    - CBS (cbs_code, cost_category, cost_center)
    - EVM (BAC, progress, AC, baseline dates, planned progress)
    - Schedule (baseline / actual / forecast)
    - Quantities & unit price (BOQ)
    """
    __tablename__ = "contract_items"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Hierarchical WBS parent (optional)
    parent_item_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    updated_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ----- WBS L1..L9 -----
    l1_project_no = db.Column(db.String(50), nullable=True, index=True)
    l2_sub_project = db.Column(db.String(50), nullable=True, index=True)
    l3_phase = db.Column(db.String(50), nullable=True, index=True)
    l4_discipline = db.Column(db.String(50), nullable=True, index=True)
    l5_area_zone = db.Column(db.String(50), nullable=True, index=True)
    l6_site_location = db.Column(db.String(120), nullable=True, index=True)
    l7_equipment_tag = db.Column(db.String(50), nullable=True, index=True)
    l8_work_package = db.Column(db.String(50), nullable=True, index=True)
    l9_activity_name = db.Column(db.String(200), nullable=True)

    # Core identity
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    pms_item_number = db.Column(db.String(80), nullable=True, index=True)
    zone = db.Column(db.String(120), nullable=True, index=True)
    phase = db.Column(db.String(80), nullable=True)
    area = db.Column(db.String(120), nullable=True)
    discipline = db.Column(db.String(80), nullable=True, index=True)
    work_package = db.Column(db.String(120), nullable=True)
    wbs_code = db.Column(db.String(80), nullable=True, index=True)
    cbs_code = db.Column(db.String(80), nullable=True, index=True)  # Cost Breakdown Structure
    boq_item_code = db.Column(db.String(80), nullable=True)
    activity_id = db.Column(db.String(80), nullable=True)
    equipment_number = db.Column(db.String(80), nullable=True)
    unit_of_measure = db.Column(db.String(30), nullable=True)
    tag_number = db.Column(db.String(80), nullable=True, index=True)
    currency = db.Column(db.String(10), nullable=True)
    cost_center = db.Column(db.String(80), nullable=True)

    # ----- Cost / BAC -----
    unit_price = db.Column(db.Numeric(18, 4), nullable=True)
    original_amount = db.Column(db.Numeric(18, 2), nullable=True)  # baseline BAC component
    adjusted_amount = db.Column(db.Numeric(18, 2), nullable=True)  # current BAC
    weight_factor = db.Column(db.Numeric(18, 4), nullable=True)  # relative weight in contract/project
    actual_cost = db.Column(db.Numeric(18, 2), nullable=True)  # AC
    cost_category = db.Column(db.String(50), nullable=True, index=True)
    funding_source = db.Column(db.String(100), nullable=True)

    # ----- Quantities (BOQ) -----
    planned_quantity = db.Column(db.Numeric(18, 4), nullable=True)
    actual_quantity = db.Column(db.Numeric(18, 4), nullable=True)

    # ----- Progress (EVM) -----
    planned_progress_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # planned % at data date
    actual_progress_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # actual physical %

    # ----- Schedule -----
    baseline_start_date = db.Column(db.Date, nullable=True)
    baseline_end_date = db.Column(db.Date, nullable=True)
    actual_start_date = db.Column(db.Date, nullable=True)
    actual_end_date = db.Column(db.Date, nullable=True)
    forecast_finish_date = db.Column(db.Date, nullable=True)
    estimated_duration = db.Column(db.Numeric(18, 4), nullable=True)  # days

    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    priority = db.Column(db.String(20), nullable=False, default="medium", index=True)

    is_common = db.Column(db.Boolean, nullable=False, default=False)
    is_milestone = db.Column(db.Boolean, nullable=False, default=False)
    workfront = db.Column(db.String(120), nullable=True)
    risk_level = db.Column(db.String(20), nullable=True)
    quality_metrics = db.Column(db.Text, nullable=True)
    acceptance_criteria = db.Column(db.Text, nullable=True)
    stakeholder_id = db.Column(db.Integer, nullable=True)

    responsible_owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    approval_status = db.Column(db.String(20), nullable=True)
    approval_date = db.Column(db.Date, nullable=True)
    revision_number = db.Column(db.Integer, nullable=True, default=0)

    predecessors = db.Column(db.Text, nullable=True)
    successors = db.Column(db.Text, nullable=True)
    resource_assignment = db.Column(db.Text, nullable=True)

    remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    company = db.relationship("Company", backref=db.backref("contract_items", lazy="dynamic"), lazy="joined")
    contract = db.relationship("Contract", backref=db.backref("items", lazy="dynamic"), lazy="joined")
    parent = db.relationship(
        "ContractItem",
        remote_side=[id],
        backref=db.backref("children", lazy="dynamic"),
        foreign_keys=[parent_item_id],
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="joined")
    updated_by = db.relationship("User", foreign_keys=[updated_by_id], lazy="joined")
    responsible_owner = db.relationship("User", foreign_keys=[responsible_owner_id], lazy="joined")

    __table_args__ = (
        db.Index("ix_items_company_contract_status", "company_id", "contract_id", "status"),
        db.Index("ix_items_contract_priority", "contract_id", "priority"),
        db.Index("ix_items_cost_category", "cost_category"),
        db.Index("ix_items_discipline", "discipline"),
        db.Index("ix_items_cbs_code", "cbs_code"),
    )

    def __repr__(self) -> str:
        return (
            f"<ContractItem id={self.id} company_id={self.company_id} "
            f"contract_id={self.contract_id} title={self.title!r}>"
        )

    def duration_days(self) -> Optional[float]:
        if self.baseline_start_date and self.baseline_end_date:
            return float((self.baseline_end_date - self.baseline_start_date).days)
        if self.estimated_duration is not None:
            return float(self.estimated_duration)
        return None

    @property
    def bac(self) -> Optional[Decimal]:
        """Budget at Completion for this item."""
        if self.adjusted_amount is not None:
            return Decimal(str(self.adjusted_amount))
        if self.original_amount is not None:
            return Decimal(str(self.original_amount))
        # derive from qty × unit price if possible
        if self.planned_quantity is not None and self.unit_price is not None:
            return Decimal(str(self.planned_quantity)) * Decimal(str(self.unit_price))
        return None

    def get_evm(self, as_of: Optional[date] = None):
        from pms_app.utils.evm import item_evm
        return item_evm(self, as_of=as_of)

    @property
    def earned_value(self) -> Optional[Decimal]:
        result = self.get_evm()
        return result.ev if result.bac > 0 else None

    @property
    def cost_variance(self) -> Optional[Decimal]:
        return self.get_evm().cv

    @property
    def schedule_variance(self) -> Optional[Decimal]:
        return self.get_evm().sv

    @property
    def cpi(self) -> Optional[Decimal]:
        return self.get_evm().cpi

    @property
    def spi(self) -> Optional[Decimal]:
        return self.get_evm().spi

    @property
    def eac(self) -> Optional[Decimal]:
        return self.get_evm().eac

    @property
    def etc(self) -> Optional[Decimal]:
        return self.get_evm().etc

    @property
    def vac(self) -> Optional[Decimal]:
        return self.get_evm().vac

    @property
    def tcpi(self) -> Optional[Decimal]:
        return self.get_evm().tcpi

    def evm_summary(self) -> dict:
        return self.get_evm().as_dict()
