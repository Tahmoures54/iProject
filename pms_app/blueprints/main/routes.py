# Path: pms_app/blueprints/main/routes.py

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any

from flask import (
    current_app,
    flash,
    render_template,
    request,
    url_for,
    send_from_directory,
    abort,
    jsonify
)
from flask_login import current_user, login_required

from pms_app.extensions import db
from pms_app.models.project import Project
from pms_app.models.project_membership import ProjectMembership
from pms_app.models.subscription import Subscription
from pms_app.utils.security import permission_required
from . import bp
from .forms import PremiumActivateForm, SettingsForm


# ═══════════════════════════════════════════════════════════════════════════
# 🔧 HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _settings_file() -> Path:
    """مسیر فایل تنظیمات"""
    Path(current_app.instance_path).mkdir(parents=True, exist_ok=True)
    return Path(current_app.instance_path) / "settings.json"


def _load_settings() -> Dict[str, Any]:
    """بارگذاری تنظیمات از فایل"""
    p = _settings_file()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return {}


def _save_settings(data: Dict[str, Any]) -> None:
    """ذخیره تنظیمات در فایل"""
    p = _settings_file()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_user_plan(user) -> str:
    """دریافت نام پلن کاربر"""
    user_plan = "رایگان"

    if not hasattr(user, 'company_id') or not user.company_id:
        return user_plan

    subscription = Subscription.query.filter_by(
        company_id=user.company_id
    ).first()

    if not subscription:
        return user_plan

    # بررسی فعال بودن اشتراک
    active = False
    if hasattr(subscription, 'is_active'):
        active = subscription.is_active
    elif hasattr(subscription, 'status'):
        active = (subscription.status == 'active')
    else:
        active = True

    if not active:
        return user_plan

    # تشخیص نام پلن
    if hasattr(subscription, 'plan_name') and subscription.plan_name:
        user_plan = subscription.plan_name
    elif hasattr(subscription, 'plan') and subscription.plan:
        if isinstance(subscription.plan, str):
            user_plan = subscription.plan
        elif hasattr(subscription.plan, 'name'):
            user_plan = subscription.plan.name
        else:
            user_plan = "پلن فعال"
    else:
        user_plan = "پلن فعال"

    return user_plan


# ═══════════════════════════════════════════════════════════════════════════
# 🏠 MAIN ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@bp.route("/")
def home():
    """صفحه اصلی سایت"""
    return render_template("main/home.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    """داشبورد کاربر"""
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("PER_PAGE", 20)

    # پایه کوئری پروژه‌ها
    query = Project.query

    if current_user.is_owner:
        pass
    elif current_user.is_company_admin:
        cid = getattr(current_user, "company_id", None)
        if cid:
            query = query.filter(Project.company_id == cid)
        else:
            flash("حساب شما به شرکتی متصل نیست.", "warning")
            query = query.filter(Project.id == -1)
    else:
        query = (
            query
            .join(ProjectMembership)
            .filter(ProjectMembership.user_id == current_user.id)
            .filter(ProjectMembership.status == "active")
        )

    query = query.order_by(Project.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "main/dashboard.html",
        projects=pagination.items,
        pagination=pagination,
        total_projects=pagination.total,
        user_plan=_get_user_plan(current_user),
    )


# ═══════════════════════════════════════════════════════════════════════════
# 📄 STATIC PAGES
# ═══════════════════════════════════════════════════════════════════════════

@bp.route("/about")
def about():
    """صفحه درباره ما"""
    return render_template("main/about.html")


# ✅ استفاده از endpoint="help" برای حفظ سازگاری با تمپلیت‌ها
@bp.route("/help", endpoint="help")
def help_page():
    """
    صفحه راهنما
    نام تابع help_page است ولی endpoint همان help می‌ماند
    پس url_for('main.help') کار می‌کند
    """
    return render_template("main/help.html")


@bp.route("/terms-of-service")
def terms_of_service():
    """شرایط استفاده از خدمات"""
    return render_template("main/terms_of_service.html")


@bp.route("/privacy-policy")
def privacy_policy():
    """سیاست حریم خصوصی"""
    return render_template("main/privacy_policy.html")


# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

@bp.route("/settings", methods=["GET", "POST"])
@login_required
@permission_required("users.admin")
def settings():
    """تنظیمات سیستم"""
    form = SettingsForm()
    data = _load_settings()

    if request.method == "GET":
        form.document_types.data = data.get("document_types", "")
        form.disciplines.data = data.get("disciplines", "")
        form.companies.data = data.get("companies", "")
        form.task_statuses.data = data.get("task_statuses", "")

    if form.validate_on_submit():
        new_data = {
            "document_types": (form.document_types.data or "").strip(),
            "disciplines": (form.disciplines.data or "").strip(),
            "companies": (form.companies.data or "").strip(),
            "task_statuses": (form.task_statuses.data or "").strip(),
        }
        _save_settings(new_data)
        flash("تنظیمات با موفقیت ذخیره شد.", "success")

    return render_template("main/settings.html", form=form)


# ═══════════════════════════════════════════════════════════════════════════
# 💎 PREMIUM ACTIVATION
# ═══════════════════════════════════════════════════════════════════════════

@bp.route("/premium-activate", methods=["GET", "POST"])
@login_required
def premium_activate():
    """صفحه فعال‌سازی اشتراک پریمیوم"""
    form = PremiumActivateForm()
    
    if form.validate_on_submit():
        flash("کلید بررسی شد (این فقط یک نمونه است).", "info")

    return render_template("main/premium_activate.html", form=form)


# ═══════════════════════════════════════════════════════════════════════════
# 🖼️ IMAGE DEBUG & TESTING
# ═══════════════════════════════════════════════════════════════════════════

@bp.route("/test-images")
def test_images():
    """
    صفحه تست برای بررسی بارگذاری تصاویر
    URL: http://127.0.0.1:5000/test-images
    """
    static_folder = current_app.static_folder
    hero_path = os.path.join(static_folder, 'img', 'hero') if static_folder else None
    
    info = {
        'static_folder': static_folder,
        'static_folder_exists': os.path.exists(static_folder) if static_folder else False,
        'hero_path': hero_path,
        'hero_path_exists': os.path.exists(hero_path) if hero_path else False,
        'hero_files': [],
        'all_img_files': [],
    }
    
    if hero_path and os.path.exists(hero_path):
        info['hero_files'] = os.listdir(hero_path)
    
    if static_folder:
        img_path = os.path.join(static_folder, 'img')
        if os.path.exists(img_path):
            for root, dirs, files in os.walk(img_path):
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), static_folder)
                    info['all_img_files'].append(rel_path.replace('\\', '/'))
    
    return render_template("main/test_images.html", info=info)


@bp.route("/debug-static")
def debug_static():
    """
    خروجی JSON برای debug مسیر static
    URL: http://127.0.0.1:5000/debug-static
    """
    static_folder = current_app.static_folder
    hero_path = os.path.join(static_folder, 'img', 'hero') if static_folder else None
    
    result = {
        'static_folder': static_folder,
        'static_url_path': current_app.static_url_path,
        'hero_path': hero_path,
        'hero_exists': os.path.exists(hero_path) if hero_path else False,
        'files': [],
        'urls': [],
    }
    
    if hero_path and os.path.exists(hero_path):
        files = os.listdir(hero_path)
        result['files'] = files
        result['urls'] = [
            url_for('static', filename=f'img/hero/{f}') 
            for f in files
        ]
    
    return jsonify(result)


@bp.route("/serve-img/<path:filename>")
def serve_image(filename: str):
    """
    سرو کردن تصاویر به صورت مستقیم (در صورت نیاز)
    URL: /serve-img/hero/slide-1.jpg
    """
    if not current_app.static_folder:
        abort(404)
    
    img_folder = os.path.join(current_app.static_folder, 'img')
    full_path = os.path.join(img_folder, filename)
    
    if not os.path.exists(full_path):
        abort(404)
    
    if not os.path.abspath(full_path).startswith(os.path.abspath(img_folder)):
        abort(403)
    
    directory = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    
    return send_from_directory(directory, file_name)