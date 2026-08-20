"""
Contract Service
Handles contracts and documents.
"""
from pms_app.extensions import db
from pms_app.models import Contract

class ContractService:
    @staticmethod
    def get_contracts(project_id: int):
        # TODO: Move logic from contracts/routes.py
        pass

    @staticmethod
    def create_contract(project_id: int, form_data: dict) -> dict:
        # TODO: Move logic from contracts/routes.py
        pass
