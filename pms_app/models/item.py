# Path: pms_app/models/item.py
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pms_app.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


class ContractItem(db.Model):
    """
    Detailed contract item / WBS entry model.
    - tenant-aware (company_id)
    - rich WBS fields (L1..L9)
    - scheduling, cost, progress, relationships and metadata
    """
    __tablename__ = "contract_items"

    id = db.Column(db.Integer, primary_key=True)

    # Tenant / FK scope
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

    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    updated_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # WBS / Hierarchy fields (L1..L9)
    l1_project_no = db.Column(db.String(50), nullable=True, index=True)
    l2_sub_project = db.Column(db.String(50), nullable=True, index=True)
    l3_phase = db.Column(db.String(50), nullable=True, index=True)
    l4_discipline = db.Column(db.String(50), nullable=True, index=True)
    l5_area_zone = db.Column(db.String(50), nullable=True, index=True)
    l6_site_location = db.Column(db.String(120), nullable=True, index=True)
    l7_equipment_tag = db.Column(db.String(50), nullable=True, index=True)
    l8_work_package = db.Column(db.String(50), nullable=True, index=True)
    l9_activity_name = db.Column(db.String(200), nullable=True)

    # Core fields
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    pms_item_number = db.Column(db.String(80), nullable=True, index=True)
    zone = db.Column(db.String(120), nullable=True, index=True)
    phase = db.Column(db.String(80), nullable=True)
    area = db.Column(db.String(120), nullable=True)
    discipline = db.Column(db.String(80), nullable=True)
    work_package = db.Column(db.String(120), nullable=True)
    wbs_code = db.Column(db.String(80), nullable=True, index=True)
    boq_item_code = db.Column(db.String(80), nullable=True)
    activity_id = db.Column(db.String(80), nullable=True)
    equipment_number = db.Column(db.String(80), nullable=True)
    unit_of_measure = db.Column(db.String(30), nullable=True)
    tag_number = db.Column(db.String(80), nullable=True, index=True)
    currency = db.Column(db.String(10), nullable=True)
    cost_center = db.Column(db.String(80), nullable=True)

    original_amount = db.Column(db.Numeric(18, 2), nullable=True)
    adjusted_amount = db.Column(db.Numeric(18, 2), nullable=True)
    weight_factor = db.Column(db.Numeric(18, 4), nullable=True)

    planned_quantity = db.Column(db.Numeric(18, 4), nullable=True)
    actual_quantity = db.Column(db.Numeric(18, 4), nullable=True)

    actual_progress_percentage = db.Column(db.Numeric(5, 2), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    priority = db.Column(db.String(20), nullable=False, default="medium", index=True)

    is_common = db.Column(db.Boolean, nullable=False, default=False)
    workfront = db.Column(db.String(120), nullable=True)
    risk_level = db.Column(db.String(20), nullable=True)
    quality_metrics = db.Column(db.Text, nullable=True)
    acceptance_criteria = db.Column(db.Text, nullable=True)
    stakeholder_id = db.Column(db.Integer, nullable=True)

    baseline_start_date = db.Column(db.Date, nullable=True)
    baseline_end_date = db.Column(db.Date, nullable=True)
    actual_start_date = db.Column(db.Date, nullable=True)
    actual_end_date = db.Column(db.Date, nullable=True)

    remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # New proposed fields
    responsible_owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_milestone = db.Column(db.Boolean, nullable=False, default=False)
    approval_status = db.Column(db.String(20), nullable=True)
    approval_date = db.Column(db.Date, nullable=True)
    revision_number = db.Column(db.Integer, nullable=True, default=0)
    estimated_duration = db.Column(db.Numeric(18, 4), nullable=True)  # e.g. days
    predecessors = db.Column(db.Text, nullable=True)  # comma-separated ids or codes
    successors = db.Column(db.Text, nullable=True)
    actual_cost = db.Column(db.Numeric(18, 2), nullable=True)
    cost_category = db.Column(db.String(50), nullable=True, index=True)
    funding_source = db.Column(db.String(100), nullable=True)
    resource_assignment = db.Column(db.Text, nullable=True)

    # Relationships
    company = db.relationship(
        "Company",
        backref=db.backref("contract_items", lazy="dynamic"),
        lazy="joined",
    )
    contract = db.relationship(
        "Contract",
        backref=db.backref("items", lazy="dynamic"),
        lazy="joined",
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="joined")
    updated_by = db.relationship("User", foreign_keys=[updated_by_id], lazy="joined")
    responsible_owner = db.relationship("User", foreign_keys=[responsible_owner_id], lazy="joined")

    __table_args__ = (
        db.Index("ix_items_company_contract_status", "company_id", "contract_id", "status"),
        db.Index("ix_items_contract_priority", "contract_id", "priority"),
        db.Index("ix_items_cost_category", "cost_category"),
    )

    def __repr__(self) -> str:
        return (
            f"<ContractItem id={self.id} company_id={self.company_id} "
            f"contract_id={self.contract_id} title={self.title!r}>"
        )

    # convenience helpers
    def duration_days(self) -> Optional[float]:
        """Return planned duration in days (baseline_end - baseline_start) if available."""
        if self.baseline_start_date and self.baseline_end_date:
            delta = (self.baseline_end_date - self.baseline_start_date).days
            return float(delta)
        return None