# Path: pms_app/utils/sms.py
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional

from flask import current_app

from pms_app.extensions import db


@dataclass
class SmsSendResult:
    ok: bool
    provider: str
    message_id: Optional[str] = None
    status_code: Optional[int] = None
    response_text: Optional[str] = None
    error: Optional[str] = None


class SmsProvider:
    name: str = "base"

    def send(self, to: str, message: str, *, sender: Optional[str] = None) -> SmsSendResult:
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    name = "console"

    def send(self, to: str, message: str, *, sender: Optional[str] = None) -> SmsSendResult:
        try:
            current_app.logger.info("SMS[console] TO=%s SENDER=%s MSG=%s", to, sender, message)
        except Exception:
            pass
        print(
            f"\n=== SMS (console) ===\nTO: {to}\nSENDER: {sender}\nMSG: {message}\n=====================\n"
        )
        return SmsSendResult(ok=True, provider=self.name, status_code=200, response_text="console")


class KavenegarProvider(SmsProvider):
    """
    پنل کاوه‌نگار — رایج در ایران.
    ENV:
      SMS_PROVIDER=kavenegar
      KAVENEGAR_API_KEY=...
      KAVENEGAR_SENDER=1000...  (اختیاری)
    """

    name = "kavenegar"

    def __init__(self) -> None:
        cfg = current_app.config
        self.api_key = (
            cfg.get("KAVENEGAR_API_KEY") or os.getenv("KAVENEGAR_API_KEY") or ""
        ).strip()
        self.default_sender = (
            cfg.get("KAVENEGAR_SENDER")
            or os.getenv("KAVENEGAR_SENDER")
            or cfg.get("SMS_SENDER")
            or os.getenv("SMS_SENDER")
            or ""
        ).strip()

    def send(self, to: str, message: str, *, sender: Optional[str] = None) -> SmsSendResult:
        try:
            import requests  # type: ignore
        except Exception as e:
            return SmsSendResult(ok=False, provider=self.name, error=f"requests not installed: {e}")

        if not self.api_key:
            return SmsSendResult(ok=False, provider=self.name, error="KAVENEGAR_API_KEY is not set")

        # Kavenegar accepts 09... or 9...
        to_norm = normalize_phone(to).replace("+", "")
        if to_norm.startswith("98") and len(to_norm) == 12:
            to_norm = "0" + to_norm[2:]

        url = f"https://api.kavenegar.com/v1/{self.api_key}/sms/send.json"
        payload: dict[str, Any] = {"receptor": to_norm, "message": message}
        from_line = (sender or self.default_sender or "").strip()
        if from_line:
            payload["sender"] = from_line

        try:
            resp = requests.post(url, data=payload, timeout=15)
            text = resp.text or ""
            msg_id = None
            try:
                data = resp.json()
                entries = (data or {}).get("entries") or []
                if entries and isinstance(entries, list):
                    msg_id = str(entries[0].get("messageid") or entries[0].get("messageId") or "")
                ret = (data or {}).get("return") or {}
                status = int(ret.get("status") or resp.status_code)
                if status != 200:
                    return SmsSendResult(
                        ok=False,
                        provider=self.name,
                        message_id=msg_id,
                        status_code=status,
                        response_text=text[:4000],
                        error=str(ret.get("message") or f"status {status}"),
                    )
            except Exception:
                pass

            ok = 200 <= int(resp.status_code) < 300
            return SmsSendResult(
                ok=ok,
                provider=self.name,
                message_id=msg_id,
                status_code=int(resp.status_code),
                response_text=text[:4000],
                error=None if ok else f"HTTP {resp.status_code}",
            )
        except Exception as e:
            return SmsSendResult(ok=False, provider=self.name, error=str(e))


class MeliPayamakProvider(SmsProvider):
    name = "melipayamak"

    def __init__(self) -> None:
        cfg = current_app.config
        self.username = cfg.get("MELIPAYAMAK_USERNAME") or os.getenv("MELIPAYAMAK_USERNAME", "")
        self.password = cfg.get("MELIPAYAMAK_PASSWORD") or os.getenv("MELIPAYAMAK_PASSWORD", "")
        self.api_key = cfg.get("MELIPAYAMAK_API_KEY") or os.getenv("MELIPAYAMAK_API_KEY", "")
        self.default_from = cfg.get("MELIPAYAMAK_FROM") or os.getenv("MELIPAYAMAK_FROM", "")
        self.send_url = cfg.get("MELIPAYAMAK_SEND_URL") or os.getenv("MELIPAYAMAK_SEND_URL", "")
        self.mode = (cfg.get("MELIPAYAMAK_MODE") or os.getenv("MELIPAYAMAK_MODE", "json")).strip().lower()
        self.f_username = cfg.get("MELIPAYAMAK_FIELD_USERNAME") or os.getenv("MELIPAYAMAK_FIELD_USERNAME", "username")
        self.f_password = cfg.get("MELIPAYAMAK_FIELD_PASSWORD") or os.getenv("MELIPAYAMAK_FIELD_PASSWORD", "password")
        self.f_to = cfg.get("MELIPAYAMAK_FIELD_TO") or os.getenv("MELIPAYAMAK_FIELD_TO", "to")
        self.f_from = cfg.get("MELIPAYAMAK_FIELD_FROM") or os.getenv("MELIPAYAMAK_FIELD_FROM", "from")
        self.f_text = cfg.get("MELIPAYAMAK_FIELD_TEXT") or os.getenv("MELIPAYAMAK_FIELD_TEXT", "text")
        self.f_isflash = cfg.get("MELIPAYAMAK_FIELD_ISFLASH") or os.getenv("MELIPAYAMAK_FIELD_ISFLASH", "isFlash")
        self.auth_header = cfg.get("MELIPAYAMAK_AUTH_HEADER") or os.getenv("MELIPAYAMAK_AUTH_HEADER", "")

    def _normalize_to_domestic(self, phone: str) -> str:
        s = normalize_phone(phone).replace("+", "")
        if s.startswith("98") and len(s) == 12:
            return "0" + s[2:]
        if s.startswith("9") and len(s) == 10:
            return "0" + s
        return s

    def send(self, to: str, message: str, *, sender: Optional[str] = None) -> SmsSendResult:
        try:
            import requests  # type: ignore
        except Exception as e:
            return SmsSendResult(ok=False, provider=self.name, error=f"requests not installed: {e}")

        if not self.send_url:
            return SmsSendResult(ok=False, provider=self.name, error="MELIPAYAMAK_SEND_URL is not set")
        if not self.username or not self.password:
            return SmsSendResult(ok=False, provider=self.name, error="MELIPAYAMAK_USERNAME/PASSWORD is not set")

        to_norm = self._normalize_to_domestic(to)
        from_line = (sender or self.default_from or "").strip()
        if not from_line:
            return SmsSendResult(ok=False, provider=self.name, error="Sender is not set (MELIPAYAMAK_FROM or sender)")

        payload: dict[str, Any] = {
            self.f_username: self.username,
            self.f_password: self.password,
            self.f_to: to_norm,
            self.f_from: from_line,
            self.f_text: message,
        }
        if self.f_isflash:
            payload[self.f_isflash] = False

        headers: dict[str, str] = {}
        if self.api_key and self.auth_header:
            headers[self.auth_header] = self.api_key

        try:
            if self.mode == "form":
                resp = requests.post(self.send_url, data=payload, headers=headers, timeout=15)
            else:
                headers.setdefault("Content-Type", "application/json")
                resp = requests.post(self.send_url, json=payload, headers=headers, timeout=15)

            text = resp.text or ""
            ok_http = 200 <= int(resp.status_code) < 300
            msg_id: Optional[str] = None
            try:
                data = resp.json()
                if isinstance(data, dict):
                    for k in ("RecId", "recId", "Value", "value", "id", "messageId", "message_id"):
                        if k in data and data[k] is not None:
                            msg_id = str(data[k])
                            break
            except Exception:
                m = re.search(r"-?\d+", text)
                if m:
                    msg_id = m.group(0)

            if not ok_http:
                return SmsSendResult(
                    ok=False,
                    provider=self.name,
                    message_id=msg_id,
                    status_code=int(resp.status_code),
                    response_text=text[:4000],
                    error=f"HTTP {resp.status_code}",
                )
            return SmsSendResult(
                ok=True,
                provider=self.name,
                message_id=msg_id,
                status_code=int(resp.status_code),
                response_text=text[:4000],
            )
        except Exception as e:
            return SmsSendResult(ok=False, provider=self.name, error=str(e))


def _is_enabled() -> bool:
    raw = current_app.config.get("SMS_ENABLED")
    if raw is None:
        raw = os.getenv("SMS_ENABLED", "false")
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _provider_name() -> str:
    return (current_app.config.get("SMS_PROVIDER") or os.getenv("SMS_PROVIDER") or "console").strip().lower()


def _default_sender() -> Optional[str]:
    return (current_app.config.get("SMS_SENDER") or os.getenv("SMS_SENDER") or "").strip() or None


def get_provider() -> SmsProvider:
    name = _provider_name()
    if name in {"console", "dev", "print"}:
        return ConsoleSmsProvider()
    if name in {"kavenegar", "kaveh", "kavenegar.com"}:
        return KavenegarProvider()
    if name in {"melipayamak", "meli", "payamak"}:
        return MeliPayamakProvider()
    return ConsoleSmsProvider()


def normalize_phone(phone: str) -> str:
    fa_to_en = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    s = (phone or "").strip().translate(fa_to_en)
    s = re.sub(r"[^\d+]", "", s)
    if s.count("+") > 1:
        s = s.replace("+", "")
    if s.startswith("+"):
        plus, rest = "+", s[1:]
    else:
        plus, rest = "", s
    if rest.startswith("0") and len(rest) == 11:
        rest, plus = "98" + rest[1:], "+"
    elif rest.startswith("98") and len(rest) == 12:
        plus = "+"
    elif rest.startswith("9") and len(rest) == 10:
        rest, plus = "98" + rest, "+"
    return f"{plus}{rest}"


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_message(template: str, context: Optional[Mapping[str, Any]] = None) -> str:
    try:
        return template.format_map(_SafeDict(**dict(context or {})))
    except Exception:
        return template


def _get_sms_log_model():
    """SMSLog is the canonical model class."""
    try:
        from pms_app.models.sms_log import SMSLog
        return SMSLog
    except Exception:
        return None


def send_sms(
    to: str,
    message: Optional[str] = None,
    *,
    template: Optional[str] = None,
    context: Optional[Mapping[str, Any]] = None,
    purpose: Optional[str] = None,
    user_id: Optional[int] = None,
    sender: Optional[str] = None,
) -> SmsSendResult:
    if not to:
        return SmsSendResult(ok=False, provider="none", error="Missing recipient")

    if message is None:
        if template is None:
            return SmsSendResult(ok=False, provider="none", error="Missing message/template")
        message = render_message(template, context=context)

    provider = get_provider()
    provider_name = getattr(provider, "name", "unknown")
    sender_final = sender or _default_sender()
    phone_norm = normalize_phone(to)

    sms_log = None
    SMSLog = _get_sms_log_model()
    if SMSLog is not None:
        try:
            sms_log = SMSLog(
                user_id=int(user_id) if user_id is not None else None,
                phone=phone_norm,
                purpose=(purpose or "").strip() or None,
                template=(template or "").strip() or None,
                message=message,
                provider=provider_name,
                status="queued",
                attempts=1,
            )
            db.session.add(sms_log)
            db.session.commit()
        except Exception:
            sms_log = None
            try:
                db.session.rollback()
            except Exception:
                pass

    if not _is_enabled():
        res = SmsSendResult(ok=False, provider=provider_name, error="SMS is disabled (SMS_ENABLED=false)")
        if sms_log is not None:
            try:
                sms_log.status = "skipped"
                sms_log.error = res.error
                sms_log.updated_at = datetime.utcnow()
                db.session.commit()
            except Exception:
                db.session.rollback()
        return res

    res = provider.send(to=to, message=message, sender=sender_final)

    if sms_log is not None:
        try:
            sms_log.status = "sent" if res.ok else "failed"
            sms_log.sent_at = datetime.utcnow() if res.ok else None
            sms_log.provider_message_id = res.message_id
            sms_log.provider_status_code = res.status_code
            sms_log.provider_response = res.response_text
            sms_log.error = res.error
            sms_log.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception:
            db.session.rollback()

    try:
        if res.ok:
            current_app.logger.info("SMS sent. provider=%s to=%s purpose=%s", provider_name, phone_norm, purpose)
        else:
            current_app.logger.warning(
                "SMS failed. provider=%s to=%s purpose=%s err=%s", provider_name, phone_norm, purpose, res.error
            )
    except Exception:
        pass

    return res


def send(to: str, message: str, **kwargs: Any) -> SmsSendResult:
    return send_sms(to=to, message=message, **kwargs)
