from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

from pms_app.blueprints.api import routes
