"""
SMS Service
Handles SMS delivery and verifications.
"""
from pms_app.extensions import db
from pms_app.models import SmsLog

class SmsService:
    @staticmethod
    def send_sms(phone_number: str, message: str) -> dict:
        # TODO: Move logic from utils/sms.py
        pass

    @staticmethod
    def send_verification_code(phone_number: str) -> dict:
        # TODO: Move logic from utils/sms.py
        pass
