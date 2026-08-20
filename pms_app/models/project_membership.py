# Path: pms_app/models/project_membership.py
from __future__ import annotations
from datetime import datetime
from pms_app.extensions import db


class ProjectMembership(db.Model):
    __tablename__ = "project_memberships"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # نقش کاربر در این پروژه
    role = db.Column(db.String(50), nullable=False, default="member")  # مثال: admin, manager, member, contractor

    # وضعیت عضویت
    status = db.Column(
        db.String(20),
        nullable=False,
        default="active",  # active, pending, declined, removed
        index=True,
    )

    # تاریخ‌ها
    invited_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    joined_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # چه کسی دعوت کرده
    invited_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # روابط
    project = db.relationship(
        "Project",
        backref=db.backref("memberships", lazy="dynamic", cascade="all, delete-orphan"),
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("project_memberships", lazy="dynamic", cascade="all, delete-orphan"),
    )

    invited_by = db.relationship(
        "User",
        foreign_keys=[invited_by_id],
        backref=db.backref("invitations_sent", lazy="dynamic"),
    )

    __table_args__ = (
        db.UniqueConstraint("project_id", "user_id", name="uq_project_membership"),
        db.Index("ix_project_membership_status", "project_id", "status"),
    )

    def __repr__(self):
        return f"<ProjectMembership project_id={self.project_id} user_id={self.user_id} role={self.role} status={self.status}>"