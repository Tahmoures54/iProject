# Path: pms_app/blueprints/reports/routes.py
from __future__ import annotations

from flask import current_app, render_template, request
from flask_login import login_required

from pms_app.models.report import Report
from pms_app.utils.security import permission_required

from . import bp


@bp.route("/reports")
@login_required
@permission_required("reports.read")
def reports():
    q = request.args.get("q", "").strip()

    query = Report.query

    # فیلتر ساده اگر ستون title یا name وجود داشته باشد
    title_col = getattr(Report, "title", None) or getattr(Report, "name", None)
    if q and title_col is not None:
        like = f"%{q}%"
        query = query.filter(title_col.ilike(like))

    # مرتب‌سازی امن: اگر updated_at/created_at نبود، با id
    order_col = getattr(Report, "updated_at", None) or getattr(Report, "created_at", None) or getattr(Report, "id")
    query = query.order_by(order_col.desc())

    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("PER_PAGE", 20)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "reports/reports.html",
        reports=pagination.items,
        pagination=pagination,
        q=q,
    )