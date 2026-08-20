# Path: pms_app/blueprints/projects/routes.py
from __future__ import annotations
from datetime import datetime
from functools import wraps
from typing import Optional
import secrets
import string

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_

from pms_app.extensions import db
from pms_app.models.project import Project
from pms_app.models.project_membership import ProjectMembership
from pms_app.models.user import User
from pms_app.utils.entitlements import can_create
from pms_app.utils.security import ensure_rbac_seed, is_owner
from pms_app.utils.evm import project_evm, project_s_curve
from . import bp
from .forms import ProjectForm, InviteToProjectForm


def _current_company_id() -> Optional[int]:
    cid = getattr(current_user, "company_id", None)
    try:
        return int(cid) if cid is not None else None
    except (ValueError, TypeError):
        return None


def _reject_inactive_users():
    if not getattr(current_user, "is_active", True):
        flash("حساب شما غیرفعال است.", "danger")
        return redirect(url_for("main.dashboard"))
    return None


def require_permission(perm: str):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.has_permission(perm):
                current_app.logger.warning(
                    f"Permission denied: user={current_user.id} ({current_user.email}), "
                    f"perm={perm}, roles={[r.name for r in current_user.roles or []]}"
                )
                flash(f"شما دسترسی لازم برای این عملیات را ندارید ({perm}).", "danger")
                return redirect(url_for("projects.projects"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def scope_projects_query(base_query):
    if current_user.is_owner:
        return base_query

    cid = _current_company_id()
    if cid is None:
        abort(403, description="کاربر به شرکتی تعلق ندارد")

    base_query = base_query.filter(Project.company_id == cid)

    if current_user.is_company_admin:
        return base_query

    return (
        base_query
        .join(ProjectMembership)
        .filter(ProjectMembership.user_id == current_user.id)
        .filter(ProjectMembership.status == "active")
    )


def get_project_or_403(project_id: int) -> Project:
    project = db.session.get(Project, project_id)
    if not project:
        abort(404)

    if not current_user.can_access_project(project):
        current_app.logger.warning(
            f"Access denied to project {project_id} for user {current_user.id}"
        )
        abort(403, description="شما به این پروژه دسترسی ندارید")

    return project


def set_project_company(project: Project) -> None:
    if not hasattr(project, "company_id"):
        return
    cid = _current_company_id()
    if cid is None and not current_user.is_owner:
        abort(403)
    if getattr(project, "company_id", None) is None:
        project.company_id = cid


def set_owner_fields(project: Project) -> None:
    uid = current_user.id
    for attr in ("created_by_id", "owner_id", "user_id"):
        if hasattr(project, attr) and getattr(project, attr) is None:
            setattr(project, attr, uid)
            break


def current_user_can_manage_members(project: Project) -> bool:
    if current_user.is_company_admin:
        if _current_company_id() != project.company_id and not current_user.is_owner:
            return False
        return True
    membership = ProjectMembership.query.filter_by(
        project_id=project.id,
        user_id=current_user.id,
        status='active'
    ).first()
    return bool(membership and membership.role in ('admin', 'manager'))


def generate_random_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_welcome_email(user, plain_password):
    flash(f"ایمیل خوش‌آمدگویی به {user.email} با رمز موقت {plain_password} ارسال شد.", "info")


@bp.before_request
@login_required
def projects_guard():
    ensure_rbac_seed(update_existing=True)
    inactive_redirect = _reject_inactive_users()
    if inactive_redirect:
        return inactive_redirect


@bp.route("/projects")
@require_permission("projects.read")
def projects():
    q = request.args.get("q", "").strip()
    query = scope_projects_query(Project.query)

    if q:
        like = f"%{q}%"
        filters = []
        if hasattr(Project, "project_code"):
            filters.append(Project.project_code.ilike(like))
        if hasattr(Project, "project_name"):
            filters.append(Project.project_name.ilike(like))
        if filters:
            query = query.filter(or_(*filters))

    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("PER_PAGE", 20)
    order_by = Project.updated_at.desc() if hasattr(Project, "updated_at") else Project.id.desc()

    pagination = query.order_by(order_by).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "projects/projects.html",
        projects=pagination.items,
        pagination=pagination,
        q=q,
    )


@bp.route("/projects/new", methods=["GET", "POST"])
@require_permission("projects.write")
def project_new():
    form = ProjectForm()

    if form.validate_on_submit():
        ok, msg, upgrade_url = can_create("project", current_user.id)
        if not ok:
            flash(msg or "محدودیت پلن اجازه ایجاد پروژه جدید را نمی‌دهد.", "warning")
            if upgrade_url:
                return redirect(upgrade_url)
            return redirect(url_for("billing.pricing"))

        project = Project(
            project_code=(form.project_code.data or "").strip(),
            project_name=form.project_name.data.strip(),
            industry=form.industry.data,
            client_name=form.client_name.data or None,
            location=form.location.data or None,
            base_currency=form.base_currency.data,
            start_date=form.start_date.data,
            finish_date=form.finish_date.data,
            status=form.status.data,
            remarks=form.remarks.data or None,
        )

        set_project_company(project)
        set_owner_fields(project)

        db.session.add(project)
        try:
            db.session.commit()
            membership = ProjectMembership(
                project_id=project.id,
                user_id=current_user.id,
                role="admin",
                status="active",
                invited_by_id=current_user.id,
                joined_at=datetime.utcnow(),
            )
            db.session.add(membership)
            db.session.commit()

            flash("پروژه جدید با موفقیت ایجاد شد.", "success")
            return redirect(url_for("projects.projects"))
        except IntegrityError:
            db.session.rollback()
            if hasattr(form, "project_code"):
                form.project_code.errors.append("این کد پروژه قبلاً استفاده شده است.")
            flash("کد پروژه تکراری است یا خطای یکتایی رخ داده.", "danger")
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("خطا در ایجاد پروژه")
            flash("خطای پایگاه داده هنگام ایجاد پروژه.", "danger")

    return render_template("projects/project_form.html", form=form, title="ایجاد پروژه جدید")


@bp.route("/projects/<int:project_id>")
@require_permission("projects.read")
def project_view(project_id: int):
    project = get_project_or_403(project_id)

    # EVM + S-Curve data
    evm = project_evm(project)
    scurve = project_s_curve(project)

    return render_template(
        "projects/project_view.html",
        project=project,
        evm=evm.as_dict(),
        scurve=scurve,
    )


@bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@require_permission("projects.write")
def project_edit(project_id: int):
    project = get_project_or_403(project_id)
    form = ProjectForm(obj=project, project_id=project_id)

    if form.validate_on_submit():
        project.project_code = (form.project_code.data or "").strip()
        project.project_name = form.project_name.data.strip()
        project.industry = form.industry.data
        project.client_name = form.client_name.data or None
        project.location = form.location.data or None
        project.base_currency = form.base_currency.data
        project.start_date = form.start_date.data
        project.finish_date = form.finish_date.data
        project.status = form.status.data
        project.remarks = form.remarks.data or None

        if hasattr(project, "updated_at"):
            project.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            flash("پروژه با موفقیت بروزرسانی شد.", "success")
            return redirect(url_for("projects.projects"))
        except IntegrityError:
            db.session.rollback()
            if hasattr(form, "project_code"):
                form.project_code.errors.append("این کد پروژه قبلاً استفاده شده است.")
            flash("کد پروژه تکراری است.", "danger")
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("خطا در بروزرسانی پروژه")
            flash("خطای پایگاه داده هنگام بروزرسانی.", "danger")

    return render_template(
        "projects/project_form.html",
        form=form,
        title="ویرایش پروژه",
        project=project
    )


@bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@require_permission("projects.write")
def project_delete(project_id: int):
    project = get_project_or_403(project_id)

    try:
        db.session.delete(project)
        db.session.commit()
        flash("پروژه با موفقیت حذف شد.", "info")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("خطا در حذف پروژه")
        flash("خطای پایگاه داده هنگام حذف پروژه.", "danger")

    return redirect(url_for("projects.projects"))


@bp.route("/projects/<int:project_id>/members")
@require_permission("projects.read")
def project_members(project_id: int):
    project = get_project_or_403(project_id)
    memberships = ProjectMembership.query.filter_by(project_id=project_id).all()
    return render_template(
        "projects/project_members.html",
        project=project,
        memberships=memberships
    )


@bp.route("/projects/<int:project_id>/invite", methods=["GET", "POST"])
@require_permission("projects.write")
def project_invite(project_id: int):
    project = get_project_or_403(project_id)

    if not current_user_can_manage_members(project):
        flash("شما مجوز دعوت عضو به این پروژه را ندارید.", "danger")
        return redirect(url_for("projects.project_members", project_id=project_id))

    form = InviteToProjectForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        role = form.role.data or "member"

        target_user = User.query.filter_by(email=email).first()
        created = False
        plain_password = None

        if not target_user:
            full_name = form.full_name.data.strip() if form.full_name.data else None
            if not full_name:
                flash("برای کاربر جدید، نام و نام خانوادگی الزامی است.", "warning")
                return render_template("projects/invite.html", form=form, project=project)

            plain_password = generate_random_password()
            target_user = User(
                email=email,
                full_name=full_name,
                is_active=True,
                company_id=project.company_id
            )
            target_user.set_password(plain_password)
            db.session.add(target_user)
            try:
                db.session.flush()
                created = True
            except IntegrityError:
                db.session.rollback()
                flash("خطا در ایجاد حساب کاربری.", "danger")
                return render_template("projects/invite.html", form=form, project=project)

        if target_user.company_id != project.company_id:
            flash("کاربر باید از همان شرکت باشد.", "danger")
            return render_template("projects/invite.html", form=form, project=project)

        existing = ProjectMembership.query.filter_by(
            project_id=project.id,
            user_id=target_user.id
        ).first()
        if existing:
            flash("این کاربر قبلاً به پروژه دعوت شده یا عضو است.", "info")
            return redirect(url_for("projects.project_members", project_id=project_id))

        membership = ProjectMembership(
            project_id=project.id,
            user_id=target_user.id,
            role=role,
            status="active",
            invited_by_id=current_user.id,
            invited_at=datetime.utcnow(),
            joined_at=datetime.utcnow()
        )
        db.session.add(membership)

        try:
            db.session.commit()
            if created:
                send_welcome_email(target_user, plain_password)
                flash(f"حساب کاربری برای {email} ایجاد و به پروژه اضافه شد.", "success")
            else:
                flash(f"{target_user.email} به پروژه اضافه شد.", "success")
            return redirect(url_for("projects.project_members", project_id=project_id))
        except IntegrityError:
            db.session.rollback()
            flash("خطا در ذخیره دعوتنامه.", "danger")
        except SQLAlchemyError:
            db.session.rollback()
            flash("خطای پایگاه داده.", "danger")

    return render_template("projects/invite.html", form=form, project=project, title="دعوت به پروژه")


@bp.route("/projects/<int:project_id>/members/<int:membership_id>/approve", methods=["POST"])
@require_permission("projects.write")
def project_approve_member(project_id: int, membership_id: int):
    project = get_project_or_403(project_id)

    if not current_user_can_manage_members(project):
        flash("شما مجوز تأیید عضو را ندارید.", "danger")
        return redirect(url_for("projects.project_members", project_id=project_id))

    membership = ProjectMembership.query.get_or_404(membership_id)
    if membership.project_id != project_id:
        abort(404)

    membership.status = "active"
    membership.joined_at = datetime.utcnow()

    try:
        db.session.commit()
        flash("عضویت با موفقیت تأیید شد.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("خطا در تأیید عضویت.", "danger")

    return redirect(url_for("projects.project_members", project_id=project_id))


@bp.route("/projects/<int:project_id>/members/<int:membership_id>/remove", methods=["POST"])
@require_permission("projects.write")
def project_remove_member(project_id: int, membership_id: int):
    project = get_project_or_403(project_id)

    if not current_user_can_manage_members(project):
        flash("شما مجوز حذف عضو را ندارید.", "danger")
        return redirect(url_for("projects.project_members", project_id=project_id))

    membership = ProjectMembership.query.get_or_404(membership_id)
    if membership.project_id != project_id:
        abort(404)

    if membership.role == "admin":
        admin_count = ProjectMembership.query.filter_by(
            project_id=project_id,
            role="admin",
            status="active"
        ).count()
        if admin_count <= 1:
            flash("نمی‌توان آخرین ادمین پروژه را حذف کرد.", "warning")
            return redirect(url_for("projects.project_members", project_id=project_id))

    db.session.delete(membership)

    try:
        db.session.commit()
        flash("عضو با موفقیت از پروژه حذف شد.", "info")
    except SQLAlchemyError:
        db.session.rollback()
        flash("خطا در حذف عضو.", "danger")

    return redirect(url_for("projects.project_members", project_id=project_id))
