# Path: pms/blueprints/auth/__init__.py
from __future__ import annotations

from flask import Blueprint

bp = Blueprint("auth", __name__)

from . import routes  # noqa: E402,F401