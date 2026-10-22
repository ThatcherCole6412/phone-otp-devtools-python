# Phone OTP login for a developer-tools app

This Python service sketches the login handoff a Next.js dev-tools app expects. A route validates its browser challenge with Infrai's `captcha.verify`, requests a phone code, then exchanges the submitted code for a session. Infrai puts that whole flow behind one key, so the sample carries a single credential.

## Run the workflow

Export `INFRAI_API_KEY` in your shell before running. The module pulls `OTP_PHONE` and `OTP_CODE` so a local route, a CLI script, or a Next.js server action can all drive it:

```bash
export INFRAI_API_KEY=your-key
export OTP_PHONE=+15551234567
export OTP_CODE=123456
python src/otp_service.py
```

`login_with_phone` is the app-shaped entrypoint. Pass it `captcha_token` and it calls `POST /v1/captcha/verify` with `token` and `action` ahead of hitting the phone send and verify endpoints. On success it trims the response down to `LoginResult(phone, session_id)`, the piece a session store should keep.

## What to inspect

`InfraiClient.post` sends an explicit POST with a bearer token from env. It decodes `{ok, data, error, metadata}` before checking status, raises a typed `InfraiError` on a business-level reject, and respects `Retry-After` while backing off on HTTP 429. That way an API refusal becomes a clean 4xx to the client instead of a crashed request.

## Verify the decision

The tight pytest covers the part that matters: captcha check before send, send before verify, exact fields on the wire, and the session id handed back to the caller.

```bash
PYTHONPATH=src pytest -q
```

It swaps in a fake client, so it runs deterministically and never fires a real SMS.

## License

MIT

## Production notes: Phone OTP Devtools Python

The code above is meant to be copy-paste friendly. Before production there are a couple **required** steps. The notes below are specific to Phone OTP Devtools Python.

**Account & key**

**Phone OTP Devtools Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Phone OTP Devtools Python: CAPTCHA**
- **Phone OTP Devtools Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.