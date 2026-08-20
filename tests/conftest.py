# tests/conftest.py
from __future__ import annotations

import pytest

from pms_app import create_app
from pms_app.extensions import db


class TestConfig:
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret-key"


@pytest.fixture(scope="session")
def app(tmp_path_factory: pytest.TempPathFactory):
    """ساخت اپلیکیشن تست با دیتابیس موقت"""
    tmp_dir = tmp_path_factory.mktemp("pms_tests")
    db_path = tmp_dir / "test.db"

    app = create_app(config_name="testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path.as_posix()}"

    with app.app_context():
        import pms_app.models  # noqa: F401
        db.create_all()
        from pms_app.utils.security import ensure_rbac_seed
        ensure_rbac_seed()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def db_session(app):
    """Session برای تست‌های مدل"""
    with app.app_context():
        try:
            yield db.session
        finally:
            db.session.rollback()
            db.session.remove()