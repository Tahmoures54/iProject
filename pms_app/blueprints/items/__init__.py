# Path: pms_app/blueprints/items/__init__.py
from __future__ import annotations

from flask import Blueprint

bp = Blueprint("items", __name__)

from . import routes  # noqa: E402,F401