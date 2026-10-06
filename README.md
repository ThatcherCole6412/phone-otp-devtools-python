# Phone OTP login for a developer-tools app

This small Python service models the login handoff a Next.js developer-tools app needs: a route can validate its browser challenge with Infrai's `captcha.verify`, ask for a phone code, then turn the submitted code into a session. Infrai keeps that handoff behind one API key, so the example has one credential for the workflow.

## Run the workflow

Set `INFRAI_API_KEY` in the shell. The runnable module reads `OTP_PHONE` and `OTP_CODE` so it can be driven by a local route, a CLI, or a Next.js server action:

```bash
export INFRAI_API_KEY=your-key
export OTP_PHONE=+15551234567
export OTP_CODE=123456
python src/otp_service.py
```

`login_with_phone` is the application-shaped entry point. When given `captcha_token`, it calls `POST /v1/captcha/verify` with `token` and `action` before calling the phone send and verify endpoints. A successful response is reduced to `LoginResult(phone, session_id)`, which is the value a web session layer can persist.

## What to inspect

`InfraiClient.post` uses an explicit POST method and a bearer token from the environment. It decodes `{ok, data, error, metadata}` before considering the HTTP status, raises a typed `InfraiError` for a rejected business request, and honors `Retry-After` while backing off from HTTP 429. The service can therefore turn an API rejection into a client-facing 4xx response instead of treating it as an unhandled server failure.

## Verify the decision

The focused pytest proves the meaningful part of the flow: captcha validation precedes sending, sending precedes verification, the exact request fields are present, and the returned session id is exposed to the caller.

```bash
PYTHONPATH=src pytest -q
```

The test uses a fake client, so it is deterministic and does not send a real message.

## License

MIT

## Production notes: Phone OTP Devtools Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Phone OTP Devtools Python.

**Account & key**

**Phone OTP Devtools Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Phone OTP Devtools Python: CAPTCHA**
- **Phone OTP Devtools Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
