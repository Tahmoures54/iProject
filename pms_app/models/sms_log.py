# Path: pms_app/models/sms_log.py
from __future__ import annotations
from datetime import datetime

from pms_app.extensions import db
from typing import Optional


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()


class SMSLog(db.Model):
    __tablename__ = "sms_logs"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    phone: str = db.Column(db.String(32), nullable=False, index=True)
    purpose: Optional[str] = db.Column(db.String(64), nullable=True, index=True)

    template: Optional[str] = db.Column(db.Text, nullable=True)
    message: str = db.Column(db.Text, nullable=False)

    provider: Optional[str] = db.Column(db.String(40), nullable=True, index=True)
    status: str = db.Column(db.String(20), nullable=False, default="queued", index=True)  # queued/sent/failed/skipped
    attempts: int = db.Column(db.Integer, nullable=False, default=0)

    provider_message_id: Optional[str] = db.Column(db.String(128), nullable=True)
    provider_status_code: Optional[int] = db.Column(db.Integer, nullable=True)
    provider_response: Optional[str] = db.Column(db.Text, nullable=True)

    error: Optional[str] = db.Column(db.Text, nullable=True)

    created_at: datetime = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    updated_at: datetime = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    sent_at: Optional[datetime] = db.Column(db.DateTime, nullable=True, index=True)

    # Relationship to User
    user = db.relationship(
        "User",
        backref=db.backref("sms_logs", lazy="dynamic"),
        lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<SMSLog id={self.id} to={self.phone} status={self.status} "
            f"purpose={self.purpose}>"
        )