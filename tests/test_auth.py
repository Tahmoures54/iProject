# tests/test_auth.py
from __future__ import annotations

from pms_app.models import Role, User


def _create_user(session, email_prefix, password, role_name=None):
    """ساخت کاربر تستی با email معتبر"""
    email = f"{email_prefix}@example.com"
    user = User(email=email, full_name=email_prefix, is_active=True)
    user.set_password(password)

    if role_name:
        role = Role.query.filter_by(name=role_name).first()
        if role:
            user.roles = [role]

    session.add(user)
    session.commit()
    return user


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_forgot_password_page_loads(client):
    response = client.get("/forgot-password")
    assert response.status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code in (302, 401)


def test_register_creates_user_and_redirects_to_login(client):
    # مسیر ثبت‌نام را مطابق blueprint واقعی تنظیم کنید؛ معمولاً /register است
    response = client.post("/register", data={
        "email": "newuser@example.com",
        "password": "securepass123",
        "confirm_password": "securepass123",
        "full_name": "New User",
    }, follow_redirects=False)

    assert response.status_code in (301, 302)


def test_login_success_redirects_to_dashboard(client, db_session):
    _create_user(db_session, "u1", "pass1234", role_name="admin")

    response = client.post("/login", data={
        "email": "u1@example.com",
        "password": "pass1234",
    }, follow_redirects=False)

    assert response.status_code in (301, 302)
    assert "/dashboard" in response.headers.get("Location", "")


def test_login_wrong_password_shows_form_again(client, db_session):
    _create_user(db_session, "u2", "correct-pass", role_name="viewer")

    response = client.post("/login", data={
        "email": "u2@example.com",
        "password": "wrong-pass",
    })

    assert response.status_code == 200


def test_logout_redirects_home(client, db_session):
    _create_user(db_session, "u3", "pass1234", role_name="viewer")

    client.post("/login", data={
        "email": "u3@example.com",
        "password": "pass1234",
    })

    response = client.get("/logout", follow_redirects=False)
    assert response.status_code in (301, 302)