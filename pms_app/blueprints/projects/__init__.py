# Path: pms_app/blueprints/projects/__init__.py
from __future__ import annotations
from flask import Blueprint
bp = Blueprint("projects", __name__)
from . import routes  # noqa: E402,F401