from __future__ import annotations

import inspect
import os
import sys
import logging
from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules

from flask import Blueprint, Flask


def create_app(config_name: str | None = None, env: str | None = None) -> Flask:
    # در Vercel سیستم‌فایل فقط‌خواندنی است → مسیر instance را به /tmp می‌بریم
    instance_path = "/tmp/instance" if os.getenv("VERCEL") == "1" else None
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)

    # ----------------------------
    # Load .env (optional)
    # ----------------------------
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass

    cfg = (
        config_name
        or env
        or os.getenv("PMS_ENV")
        or os.getenv("FLASK_ENV")
        or "development"
    ).strip().lower()

    # ----------------------------
    # Logging setup (Vercel → stdout)
    # ----------------------------
    _setup_logging(app)

    # ----------------------------
    # Load config
    # ----------------------------
    try:
        if cfg == "production":
            app.config.from_object("pms_app.config.production.ProductionConfig")
        elif cfg == "testing":
            app.config.from_object("pms_app.config.testing.TestingConfig")
        else:
            app.config.from_object("pms_app.config.development.DevelopmentConfig")
    except Exception as e:
        app.logger.warning("Config load skipped: %s", e)

    # ----------------------------
    # Init extensions
    # ----------------------------
    from . import extensions as ext

    init_extensions = getattr(ext, "init_extensions", None)
    if callable(init_extensions):
        init_extensions(app)
    else:
        for name, obj in vars(ext).items():
            if name.startswith("_"):
                continue
            if inspect.ismodule(obj) or inspect.isfunction(obj) or inspect.isclass(obj):
                continue
            init_app = getattr(obj, "init_app", None)
            if callable(init_app):
                init_app(app)

    # 🔥 بسیار مهم: همه مدل‌ها باید قبل از create_all / migrate import شوند
    import pms_app.models  # noqa: F401

    # ----------------------------
    # Ensure DB & Seed (dev only)
    # ----------------------------
    _ensure_db_schema_and_seed(app, cfg=cfg)

    # ----------------------------
    # Register blueprints
    # ----------------------------
    _register_blueprints(app)

    # ----------------------------
    # Fallback & Debug routes
    # ----------------------------
    _ensure_debug_routes(app)
    _ensure_root_route(app)

    return app


# ============================================================
# Helpers
# ============================================================

def _setup_logging(app: Flask) -> None:
    """Set logging handler: stdout on Vercel, file locally."""
    app.logger.handlers.clear()

    if os.getenv("VERCEL") == "1":
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
    else:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
            )
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
        except OSError:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            app.logger.addHandler(handler)


def _is_debug(app: Flask) -> bool:
    return bool(app.config.get("DEBUG", False))


def _ensure_db_schema_and_seed(app: Flask, *, cfg: str) -> None:
    """
    Development safety net:
    - If DB is empty → create_all()
    - Then run ensure_rbac_seed()

    Controlled by:
        PMS_AUTO_CREATE_DB=1
    """
    if app.config.get("TESTING") is True:
        return

    auto_flag = (os.getenv("PMS_AUTO_CREATE_DB") or "").strip().lower()
    force_auto = auto_flag in {"1", "true", "yes", "on"}

    should_run = force_auto or (cfg != "production")
    if not should_run:
        return

    try:
        from sqlalchemy import inspect as sa_inspect
        from pms_app.extensions import db
        from pms_app.utils.security import ensure_rbac_seed

        with app.app_context():
            inspector = sa_inspect(db.engine)
            existing_tables = set(inspector.get_table_names())

            if not existing_tables or existing_tables == {"alembic_version"}:
                app.logger.warning(
                    "Database is empty (tables=%s). Running db.create_all() ...",
                    sorted(existing_tables),
                )
                db.create_all()

            ensure_rbac_seed()

    except Exception:
        app.logger.exception("Failed to ensure DB schema / RBAC seed")
        if _is_debug(app):
            raise


def _register_blueprints(app: Flask) -> None:
    from . import blueprints as bp_pkg

    registered_total = 0

    for m in iter_modules(bp_pkg.__path__):
        bp_name = m.name
        if bp_name.startswith("_"):
            continue

        module = None
        last_exc: Exception | None = None

        for mod_path in (
            f"pms_app.blueprints.{bp_name}.routes",
            f"pms_app.blueprints.{bp_name}",
        ):
            try:
                module = import_module(mod_path)
                last_exc = None
                break
            except Exception as e:
                last_exc = e
                app.logger.exception("Blueprint import failed: %s", mod_path)

        if module is None:
            if _is_debug(app) and last_exc is not None:
                raise last_exc
            continue

        blueprints = [v for v in vars(module).values() if isinstance(v, Blueprint)]

        for attr in ("bp", "blueprint"):
            v = getattr(module, attr, None)
            if isinstance(v, Blueprint) and v not in blueprints:
                blueprints.append(v)

        if not blueprints:
            app.logger.warning(
                "No Blueprint object found for '%s' in %s",
                bp_name,
                module.__name__,
            )
            continue

        for bp in blueprints:
            app.register_blueprint(bp)
            registered_total += 1
            app.logger.info(
                "Registered blueprint: name=%s url_prefix=%s",
                bp.name,
                bp.url_prefix,
            )

    app.logger.info("Total registered blueprints: %s", registered_total)


def _ensure_root_route(app: Flask) -> None:
    has_root = any(rule.rule == "/" for rule in app.url_map.iter_rules())
    if has_root:
        return

    @app.get("/")
    def _index_fallback():
        try:
            from flask import render_template
            return render_template("main/home.html")
        except Exception:
            rules = sorted({rule.rule for rule in app.url_map.iter_rules()})
            return (
                "App is running, but no '/' route was registered.<br>"
                "Available routes:<br><pre>"
                + "\n".join(rules)
                + "</pre>",
                200,
            )


def _ensure_debug_routes(app: Flask) -> None:
    if not _is_debug(app):
        return

    @app.get("/__routes")
    def _routes():
        rules = []
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            methods = ",".join(
                sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
            )
            rules.append(
                f"{rule.rule:30s}  [{methods:10s}]  -> {rule.endpoint}"
            )
        return "<pre>" + "\n".join(rules) + "</pre>", 200
