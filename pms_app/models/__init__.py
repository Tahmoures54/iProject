# Path: pms_app/models/__init__.py
"""
Central models package initializer.

Ensures correct import order so that SQLAlchemy metadata contains all tables
before create_all() or Alembic operations are run.

Import rules:
1. Association tables first (no direct FKs, just helper tables).
2. RBAC / Role & Plan models (roles, plans) for FK references.
3. Company after Plan (companies.plan_id -> plans.id).
4. ProjectMembership (association object) before Project/User.
5. Project and User (relationships may reference each other by string).
6. Domain models (Contract, ContractItem, Report, SMSLog, Subscription, etc.).
"""

# ---------------------------
# Core association tables
# ---------------------------
from .association import user_roles  # noqa: F401

# ---------------------------
# Core RBAC models
# ---------------------------
from .role import Role  # noqa: F401

# ---------------------------
# Plan & Company dependencies
# ---------------------------
from .plan import Plan  # noqa: F401
from .company import Company  # noqa: F401

# ---------------------------
# Project / User association
# ---------------------------
from .project_membership import ProjectMembership  # noqa: F401
from .project import Project  # noqa: F401
from .user import User  # noqa: F401

# ---------------------------
# Domain models
# ---------------------------
from .contract import Contract  # noqa: F401
from .item import ContractItem  # noqa: F401
from .report import Report  # noqa: F401
from .sms_log import SMSLog  # noqa: F401
from .subscription import Subscription  # noqa: F401

# ---------------------------
# Public API
# ---------------------------
__all__ = [
    "user_roles",
    "Role",
    "Plan",
    "Company",
    "ProjectMembership",
    "Project",
    "User",
    "Contract",
    "ContractItem",
    "Report",
    "SMSLog",
    "Subscription",
]