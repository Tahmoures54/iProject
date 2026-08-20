"""
Project Service
Handles project CRUD and project membership management.
"""
from pms_app.extensions import db
from pms_app.models import Project, ProjectMembership

class ProjectService:
    @staticmethod
    def get_user_projects(user_id: int, page: int = 1, per_page: int = 20):
        # TODO: Move logic from projects/routes.py
        pass

    @staticmethod
    def create_project(owner_id: int, form_data: dict) -> dict:
        # TODO: Move logic from projects/routes.py
        pass

    @staticmethod
    def update_project(project_id: int, form_data: dict) -> dict:
        # TODO: Move logic from projects/routes.py
        pass

    @staticmethod
    def delete_project(project_id: int) -> dict:
        # TODO: Move logic from projects/routes.py
        pass
