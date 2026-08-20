from __future__ import annotations
from datetime import datetime

from sqlalchemy.ext.associationproxy import association_proxy

from pms_app.extensions import db


def utcnow() -> datetime:
    return datetime.utcnow()


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    # Tenant scope (شرکت)
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

    # ──────────────────────────────────────────────
    # Relationships
    # ──────────────────────────────────────────────

    company = db.relationship(
        "Company",
        backref=db.backref("projects", lazy="dynamic"),
        lazy="joined",
    )

    # استفاده از association object (کلاس ProjectMembership)
    # ProjectMembership با backref نام "memberships" را روی Project ایجاد می‌کند.
    # این proxy اجازه می‌دهد با project.members مستقیم به لیست کاربران دسترسی داشته باشیم.
    members = association_proxy("memberships", "user")

    # ──────────────────────────────────────────────
    # Table constraints & indexes
    # ──────────────────────────────────────────────
    __table_args__ = (
        db.UniqueConstraint("company_id", "project_code", name="uq_projects_company_code"),
        db.Index("ix_projects_company_status", "company_id", "status"),
    )

    # ──────────────────────────────────────────────
    # Helper properties & methods
    # ──────────────────────────────────────────────

    @property
    def active_member_count(self) -> int:
        """تعداد اعضای فعال پروژه"""
        from pms_app.models.project_membership import ProjectMembership  # late import
        return (
            db.session.query(ProjectMembership)
            .filter_by(project_id=self.id, status="active")
            .count()
        )

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def has_member(self, user) -> bool:
        """آیا کاربر عضو فعال این پروژه است؟"""
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
        """
        آیا کاربر اجازه دسترسی به این پروژه را دارد؟
        منطق اولویت‌دار:
        - مالک پلتفرم → همیشه بله
        - اگر پروژه به شرکت کاربر تعلق نداشته باشد → خیر
        - ادمین شرکت → بله (برای تمام پروژه‌های شرکت)
        - کاربران عادی → فقط اگر عضو فعال پروژه باشند
        """
        from pms_app.models.user import User  # late import اگر لازم باشد

        if not user or not user.is_active:
            return False

        # مالک پلتفرم همیشه دسترسی دارد
        if user.is_owner:
            return True

        # پروژه باید متعلق به شرکت کاربر باشد
        if self.company_id != user.company_id:
            return False

        # ادمین شرکت دسترسی کامل به پروژه‌های شرکت دارد
        if user.is_company_admin:
            return True

        # کاربران معمولی فقط با عضویت مستقیم
        return self.has_member(user)

    def __repr__(self) -> str:
        return (
            f"<Project id={self.id} company_id={self.company_id} "
            f"code={self.project_code!r} name={self.project_name!r}>"
        )