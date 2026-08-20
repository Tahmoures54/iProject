# Path: pms_app/models/role.py
from __future__ import annotations
from datetime import datetime
from typing import Set

from pms_app.extensions import db

def utcnow() -> datetime:
    return datetime.utcnow()


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    permissions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # back_populates defined on User.roles (User imports association table)
    users = db.relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="dynamic",
    )

    def permission_set(self) -> Set[str]:
        raw = (self.permissions or "").strip()
        if not raw:
            return set()
        return {p.strip() for p in raw.split(",") if p and p.strip()}

    def has_permission(self, perm: str) -> bool:
        perm = (perm or "").strip()
        if not perm:
            return False
        role_name = (self.name or "").strip().lower()
        if role_name == "owner":
            return True
        perms = self.permission_set()
        if "*" in perms or "full:*" in perms:
            return True
        return perm in perms

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"