# Path: pms_app/models/report.py
from __future__ import annotations

from datetime import datetime

from pms_app.extensions import db


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)

    # حداقل فیلدهایی که با blueprint/reports سازگار باشند
    title = db.Column(db.String(200), nullable=False, index=True)

    # (اختیاری) توضیحات/محتوا
    description = db.Column(db.Text, nullable=True)

    # (اختیاری) نوع گزارش (مثلاً: progress / cost / ...)
    report_type = db.Column(db.String(50), nullable=True, index=True)

    # (اختیاری) داده‌ی ساخت‌یافته گزارش
    # روی SQLite هم معمولاً به صورت TEXT نگهداری می‌شود ولی از سمت SQLAlchemy JSON است.
    data = db.Column(db.JSON, nullable=True)

    # (اختیاری) سازنده گزارش
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Report id={self.id} title={self.title!r}>"