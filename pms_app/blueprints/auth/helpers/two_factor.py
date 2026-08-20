# Path: pms_app/blueprints/auth/helpers/two_factor.py
from __future__ import annotations

import base64
from io import BytesIO


def make_qr_data_uri(data: str) -> str:
    import qrcode  # type: ignore
    img = qrcode.make(data)
    bio = BytesIO()
    img.save(bio, format="PNG")
    b64 = base64.b64encode(bio.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def verify_totp(secret: str, code: str) -> bool:
    try:
        import pyotp  # type: ignore
    except ImportError:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_totp_secret() -> str | None:
    try:
        import pyotp  # type: ignore
        return pyotp.random_base32()
    except ImportError:
        return None


def build_provisioning_uri(secret: str, account: str, issuer: str) -> str | None:
    try:
        import pyotp  # type: ignore
        return pyotp.TOTP(secret).provisioning_uri(name=account, issuer_name=issuer)
    except ImportError:
        return None