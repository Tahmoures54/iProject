"""
Item Service
Handles project items and tasks.
"""
from pms_app.extensions import db
from pms_app.models import Item

class ItemService:
    @staticmethod
    def get_items(project_id: int):
        # TODO: Move logic from items/routes.py
        pass

    @staticmethod
    def create_item(project_id: int, form_data: dict) -> dict:
        # TODO: Move logic from items/routes.py
        pass
