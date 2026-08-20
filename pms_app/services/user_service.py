"""
User Service
Handles user management, permissions, and roles.
"""
from pms_app.extensions import db
from pms_app.models import User

class UserService:
    @staticmethod
    def get_users(company_id: int = None):
        # TODO: Move logic from users/routes.py
        pass

    @staticmethod
    def update_user(user_id: int, form_data: dict) -> dict:
        # TODO: Move logic from users/routes.py
        pass
