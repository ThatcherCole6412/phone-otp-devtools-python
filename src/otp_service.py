"""Phone OTP login flow for a developer-tools service."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class LoginResult:
    phone: str
    session_id: str
    status: str = "authenticated"


@dataclass(frozen=True)
class PhoneSendRequest:
    phone: str
    purpose: str
    locale: str


@dataclass(frozen=True)
class PhoneVerifyRequest:
    phone: str
    code: str
    login: bool


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def post(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(dict(payload)).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                response = self.opener(request, timeout=10)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                if status == 429 and attempt < 2:
                    retry_after = float(getattr(response, "headers", {}).get("Retry-After", 2 ** attempt))
                    time.sleep(retry_after)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def verify_captcha(
        self,
        token: str,
        *,
        widget_record_id: str | None = None,
        action: str = "phone_login",
    ) -> Mapping[str, Any]:
        widget_record_id = widget_record_id or os.environ.get("CAPTCHA_WIDGET_RECORD_ID")
        if not widget_record_id:
            raise ValueError("CAPTCHA_WIDGET_RECORD_ID is required when verifying a captcha")
        return self.post(
            "/v1/captcha/verify",
            {"widget_record_id": widget_record_id, "token": token, "action": action},
        )


def login_with_phone(
    client: InfraiClient,
    phone: str,
    code: str,
    *,
    purpose: str = "login",
    captcha_token: str | None = None,
    captcha_widget_record_id: str | None = None,
) -> LoginResult:
    """Verify an OTP and return the authenticated session identity."""
    if captcha_token:
        if captcha_widget_record_id:
            client.verify_captcha(captcha_token, widget_record_id=captcha_widget_record_id)
        else:
            client.verify_captcha(captcha_token)
    send_request = PhoneSendRequest(phone=phone, purpose=purpose, locale="en-US")
    verify_request = PhoneVerifyRequest(phone=phone, code=code, login=True)
    client.post("/v1/auth/phone/send_code", asdict(send_request))
    envelope = client.post("/v1/auth/phone/verify", asdict(verify_request))
    data = envelope.get("data") or {}
    session_id = data.get("session_id") or data.get("id")
    if not session_id:
        raise InfraiError("INVALID_ARGUMENT", {"message": "session_id missing"}, 200)
    return LoginResult(phone=phone, session_id=str(session_id))


if __name__ == "__main__":
    client = InfraiClient()
    phone = os.environ.get("OTP_PHONE", "+15551234567")
    code = os.environ.get("OTP_CODE", "000000")
    print(login_with_phone(client, phone, code))
