# Path: pms_app/blueprints/concerns/__init__.py
from __future__ import annotations

from flask import Blueprint

bp = Blueprint("concerns", __name__, url_prefix="/concerns")

from . import routes  # noqa: E402,F401
