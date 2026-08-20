# Path: pms_app/blueprints/contracts/routes.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from pms_app.extensions import db
from pms_app.models.contract import Contract
from pms_app.models.project import Project
from pms_app.utils.entitlements import can_create
from pms_app.utils.security import ensure_rbac_seed, is_owner, permission_required
from pms_app.utils.progress import contract_progress

from . import bp
from .forms import ContractForm


def _current_company_id() -> Optional[int]:
    cid = getattr(current_user, "company_id", None)
    try:
        return int(cid) if cid is not None else None
    except Exception:
        return None


def _reject_inactive_users():
    if hasattr(current_user, "is_active") and not bool(getattr(current_user, "is_active")):
        flash("حساب شما غیرفعال است.", "danger")
        return redirect(url_for("main.dashboard"))
    return None


def _get_project_or_404(project_id: int) -> Project:
    project = db.session.get(Project, int(project_id))
    if not project:
        abort(404)
    if is_owner(current_user):
        return project
    cid = _current_company_id()
    if cid is None:
        abort(403)
    if hasattr(Project, "company_id"):
        if int(getattr(project, "company_id") or 0) != int(cid):
            abort(404)
        return project
    for attr in ("user_id", "owner_id", "created_by_id"):
        if hasattr(Project, attr) and int(getattr(project, attr) or 0) == int(current_user.id):
            return project
    abort(404)


def _get_contract_or_404(contract_id: int) -> Contract:
    contract = db.session.get(Contract, int(contract_id))
    if not contract:
        abort(404)
    if is_owner(current_user):
        return contract
    cid = _current_company_id()
    if cid is None:
        abort(403)
    if hasattr(Contract, "company_id"):
        if int(getattr(contract, "company_id") or 0) != int(cid):
            abort(404)
        return contract
    project = db.session.get(Project, int(getattr(contract, "project_id") or 0))
    if not project:
        abort(404)
    _get_project_or_404(int(project.id))
    return contract


def _contracts_query_scoped(project_id: int):
    q = Contract.query.filter(Contract.project_id == int(project_id))
    if is_owner(current_user):
        return q
    cid = _current_company_id()
    if cid is None:
        abort(403)
    if hasattr(Contract, "company_id"):
        q = q.filter(Contract.company_id == int(cid))
    return q


@bp.before_request
@login_required
def _contracts_guard():
    ensure_rbac_seed(update_existing=True)
    inactive = _reject_inactive_users()
    if inactive is not None:
        return inactive
    return None


@bp.route("/contracts")
@bp.route("/projects/<int:project_id>/contracts")
@login_required
@permission_required("contracts.read")
def contracts(project_id: int | None = None):
    if project_id is None:
        project_id = request.args.get("project_id", type=int)

    if not project_id:
        flash("لطفاً ابتدا یک پروژه را انتخاب کنید تا قراردادهای آن نمایش داده شود.", "warning")
        return redirect(url_for("projects.projects"))

    project = _get_project_or_404(int(project_id))

    page = request.args.get("page", 1, type=int)
    per_page = int(current_app.config.get("PER_PAGE", 20))

    pagination = (
        _contracts_query_scoped(int(project.id))
        .order_by(Contract.updated_at.desc() if hasattr(Contract, "updated_at") else Contract.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    progress_map = {}
    for c in pagination.items:
        try:
            progress_map[c.id] = contract_progress(c)
        except Exception:
            progress_map[c.id] = {
                "overall_pct": 0,
                "item_count": 0,
                "disciplines": [],
            }

    return render_template(
        "contracts/contracts.html",
        project=project,
        contracts=pagination.items,
        pagination=pagination,
        progress_map=progress_map,
    )


@bp.route("/projects/<int:project_id>/contracts/new", methods=["GET", "POST"])
@login_required
@permission_required("contracts.write")
def contract_new(project_id: int):
    project = _get_project_or_404(int(project_id))
    form = ContractForm()
    if form.validate_on_submit():
        ok, msg, upgrade_url = can_create("contract", int(current_user.id))
        if not ok:
            flash(msg or "محدودیت پلن اجازه ایجاد قرارداد جدید را نمی‌دهد.", "warning")
            return redirect(upgrade_url or url_for("billing.pricing"))

        contract = Contract(
            project_id=int(project.id),
            contract_number=(form.contract_number.data or "").strip(),
            contract_title=form.contract_title.data,
            contractor_name=form.contractor_name.data or None,
            contract_type=form.contract_type.data,
            pricing_model=form.pricing_model.data,
            currency=form.currency.data,
            original_contract_value=form.original_contract_value.data,
            revised_contract_value=form.revised_contract_value.data,
            start_date=form.start_date.data,
            finish_date=form.finish_date.data,
            status=form.status.data,
            remarks=form.remarks.data or None,
        )
        if hasattr(Contract, "company_id") and hasattr(Project, "company_id"):
            contract.company_id = int(getattr(project, "company_id"))

        db.session.add(contract)
        try:
            db.session.commit()
            flash("قرارداد جدید ایجاد شد.", "success")
            return redirect(url_for("contracts.contracts", project_id=int(project.id)))
        except IntegrityError:
            db.session.rollback()
            flash("اطلاعات قرارداد تکراری است یا با محدودیت‌های دیتابیس سازگار نیست.", "danger")
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("DB error while creating contract")
            flash("خطای دیتابیس هنگام ایجاد قرارداد.", "danger")

    return render_template(
        "contracts/contract_form.html",
        project=project,
        form=form,
        title="قرارداد جدید",
    )


@bp.route("/contracts/<int:contract_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("contracts.write")
def contract_edit(contract_id: int):
    contract = _get_contract_or_404(int(contract_id))
    project = _get_project_or_404(int(getattr(contract, "project_id")))
    form = ContractForm(obj=contract)
    if form.validate_on_submit():
        contract.contract_number = (form.contract_number.data or "").strip()
        contract.contract_title = form.contract_title.data
        contract.contractor_name = form.contractor_name.data or None
        contract.contract_type = form.contract_type.data
        contract.pricing_model = form.pricing_model.data
        contract.currency = form.currency.data
        contract.original_contract_value = form.original_contract_value.data
        contract.revised_contract_value = form.revised_contract_value.data
        contract.start_date = form.start_date.data
        contract.finish_date = form.finish_date.data
        contract.status = form.status.data
        contract.remarks = form.remarks.data or None
        if hasattr(contract, "updated_at"):
            contract.updated_at = datetime.utcnow()
        if hasattr(Contract, "company_id") and getattr(contract, "company_id", None) is None and hasattr(project, "company_id"):
            contract.company_id = int(getattr(project, "company_id"))
        try:
            db.session.commit()
            flash("قرارداد بروزرسانی شد.", "success")
            return redirect(url_for("contracts.contracts", project_id=int(project.id)))
        except IntegrityError:
            db.session.rollback()
            flash("اطلاعات قرارداد تکراری است یا با محدودیت‌های دیتابیس سازگار نیست.", "danger")
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("DB error while updating contract")
            flash("خطای دیتابیس هنگام بروزرسانی قرارداد.", "danger")

    return render_template(
        "contracts/contract_form.html",
        project=project,
        form=form,
        title="ویرایش قرارداد",
        contract=contract,
    )


@bp.route("/contracts/<int:contract_id>/delete", methods=["POST"])
@login_required
@permission_required("contracts.write")
def contract_delete(contract_id: int):
    contract = _get_contract_or_404(int(contract_id))
    project_id = int(getattr(contract, "project_id"))
    try:
        db.session.delete(contract)
        db.session.commit()
        flash("قرارداد حذف شد.", "info")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("DB error while deleting contract")
        flash("خطای دیتابیس هنگام حذف قرارداد.", "danger")
    return redirect(url_for("contracts.contracts", project_id=project_id))
