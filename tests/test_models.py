# tests/test_models.py
from __future__ import annotations

from pms_app.models.contract import Contract
from pms_app.models.item import ContractItem
from pms_app.models.project import Project
from pms_app.models.company import Company
from pms_app.models import Role, User
from pms_app.utils.security import ensure_rbac_seed


def test_user_password_hashing(db_session):
    u = User(email="alice@example.com", full_name="Alice", is_active=True)
    u.set_password("secret1234")
    db_session.add(u)
    db_session.commit()
    assert u.password_hash
    assert u.check_password("secret1234") is True
    assert u.check_password("wrong") is False


def test_role_permission_parsing_and_admin_override(db_session):
    ensure_rbac_seed()
    viewer = Role.query.filter_by(name="viewer").first()
    assert viewer is not None
    assert viewer.has_permission("projects.read") is True
    assert viewer.has_permission("items.read") is True
    assert viewer.has_permission("projects.write") is False

    admin = Role.query.filter_by(name="admin").first()
    assert admin is not None
    assert admin.has_permission("anything.at.all") is True


def test_user_has_permission_via_roles(db_session):
    ensure_rbac_seed()
    viewer = Role.query.filter_by(name="viewer").first()
    manager = Role.query.filter_by(name="manager").first()
    assert viewer is not None
    assert manager is not None

    u = User(email="bob@example.com", full_name="Bob", is_active=True)
    u.set_password("pass1234")
    u.roles = [viewer]
    db_session.add(u)
    db_session.commit()
    assert u.has_permission("projects.read") is True
    assert u.has_permission("projects.write") is False

    u.roles = [viewer, manager]
    db_session.commit()
    assert u.has_permission("projects.write") is True
    assert u.has_permission("contracts.write") is True


def test_project_contract_relationship(db_session):
    company = Company(name="Test Company")
    db_session.add(company)
    db_session.flush()

    p = Project(
        company_id=company.id,
        project_code="PRJ-001",
        project_name="Test Project",
        industry="construction",
        base_currency="IRR",
        status="active",
    )
    db_session.add(p)
    db_session.commit()

    c = Contract(
        company_id=company.id,
        project_id=p.id,
        contract_number="CNT-001",
        contract_title="Contract One",
        contract_type="EPC",
        pricing_model="lumpsum",
        currency="IRR",
        status="active",
    )
    db_session.add(c)
    db_session.commit()

    assert c.project_id == p.id
    assert c.project is not None
    assert c.project.id == p.id
    assert p.contracts.count() == 1
    assert p.contracts.first().id == c.id


def test_contract_item_relationship_and_audit_users(db_session):
    ensure_rbac_seed()
    role = Role.query.filter_by(name="admin").first()
    assert role is not None

    u1 = User(email="creator@example.com", full_name="Creator", is_active=True)
    u1.set_password("pass1234")
    u1.roles = [role]
    u2 = User(email="editor@example.com", full_name="Editor", is_active=True)
    u2.set_password("pass1234")
    u2.roles = [role]

    company = Company(name="Test Company 2")
    db_session.add(company)
    db_session.flush()

    p = Project(
        company_id=company.id,
        project_code="PRJ-002",
        project_name="Project 2",
        industry="oil_gas",
        base_currency="USD",
        status="active",
    )
    db_session.add_all([u1, u2, p])
    db_session.commit()

    c = Contract(
        company_id=company.id,
        project_id=p.id,
        contract_number="CNT-002",
        contract_title="Contract Two",
        contract_type="EPCM",
        pricing_model="unit_rate",
        currency="USD",
        status="active",
    )
    db_session.add(c)
    db_session.commit()

    item = ContractItem(
        company_id=company.id,          # مهم
        contract_id=c.id,
        title="Item A",
        status="open",
        priority="medium",
        created_by_id=u1.id,
        updated_by_id=u2.id,
    )
    db_session.add(item)
    db_session.commit()

    assert item.contract_id == c.id
    assert c.items.count() == 1
    assert c.items.first().id == item.id
    assert item.created_by.email == "creator@example.com"
    assert item.updated_by.email == "editor@example.com"