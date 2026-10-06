from otp_service import LoginResult, login_with_phone


class FakeClient:
    def __init__(self):
        self.calls = []

    def post(self, path, payload):
        self.calls.append((path, payload))
        if path.endswith("verify"):
            return {"ok": True, "data": {"session_id": "sess_dev_42"}, "error": None, "metadata": {}}
        return {"ok": True, "data": {"sent": True}, "error": None, "metadata": {}}

    def verify_captcha(self, token, *, action="phone_login"):
        self.calls.append(("/v1/captcha/verify", {"token": token, "action": action}))
        return {"ok": True, "data": {"score": 0.9}, "error": None, "metadata": {}}


def test_login_sends_then_verifies_and_returns_session():
    client = FakeClient()
    result = login_with_phone(client, "+15550100", "123456")
    assert result == LoginResult(phone="+15550100", session_id="sess_dev_42")
    assert [path for path, _ in client.calls] == ["/v1/auth/phone/send_code", "/v1/auth/phone/verify"]
    assert client.calls[1][1] == {"phone": "+15550100", "code": "123456", "login": True}


def test_login_checks_captcha_before_sending_code():
    client = FakeClient()
    login_with_phone(client, "+15550100", "123456", captcha_token="captcha-token")
    assert [path for path, _ in client.calls] == [
        "/v1/captcha/verify",
        "/v1/auth/phone/send_code",
        "/v1/auth/phone/verify",
    ]
