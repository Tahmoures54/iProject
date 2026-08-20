from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.associationproxy import association_proxy

from pms_app.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project_code = db.Column(db.String(50), nullable=False, index=True)
    project_name = db.Column(db.String(200), nullable=False, index=True)
    industry = db.Column(db.String(50), nullable=False, index=True)
    client_name = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    base_currency = db.Column(db.String(10), nullable=False)

    start_date = db.Column(db.Date, nullable=True)
    finish_date = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    company = db.relationship(
        "Company",
        backref=db.backref("projects", lazy="dynamic"),
        lazy="joined",
    )

    members = association_proxy("memberships", "user")

    __table_args__ = (
        db.UniqueConstraint("company_id", "project_code", name="uq_projects_company_code"),
        db.Index("ix_projects_company_status", "company_id", "status"),
    )

    @property
    def active_member_count(self) -> int:
        from pms_app.models.project_membership import ProjectMembership
        return (
            db.session.query(ProjectMembership)
            .filter_by(project_id=self.id, status="active")
            .count()
        )

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def has_member(self, user) -> bool:
        from pms_app.models.project_membership import ProjectMembership
        if not user or not user.id:
            return False
        return (
            ProjectMembership.query.filter_by(
                project_id=self.id,
                user_id=user.id,
                status="active",
            ).first()
            is not None
        )

    def can_access(self, user) -> bool:
        if not user or not user.is_active:
            return False
        if user.is_owner:
            return True
        if self.company_id != user.company_id:
            return False
        if user.is_company_admin:
            return True
        return self.has_member(user)

    def __repr__(self) -> str:
        return (
            f"<Project id={self.id} company_id={self.company_id} "
            f"code={self.project_code!r} name={self.project_name!r}>"
        )

    # ------------------------------------------------------------------
    # Earned Value Management (project-level aggregation)
    # ------------------------------------------------------------------
    def get_evm(self, as_of: Optional[date] = None):
        """Return aggregated EVMResult across all contracts of this project."""
        from pms_app.utils.evm import project_evm
        return project_evm(self, as_of=as_of)

    @property
    def bac(self) -> Optional[Decimal]:
        result = self.get_evm()
        return result.bac if result.bac > 0 else None

    @property
    def earned_value(self) -> Optional[Decimal]:
        return self.get_evm().ev

    @property
    def actual_cost_total(self) -> Optional[Decimal]:
        return self.get_evm().ac

    @property
    def cpi(self) -> Optional[Decimal]:
        return self.get_evm().cpi

    @property
    def spi(self) -> Optional[Decimal]:
        return self.get_evm().spi

    @property
    def percent_complete(self) -> Optional[Decimal]:
        return self.get_evm().percent_complete

    @property
    def eac(self) -> Optional[Decimal]:
        return self.get_evm().eac

    def evm_summary(self) -> dict:
        """Dict ready for dashboards / API / templates."""
        return self.get_evm().as_dict()
