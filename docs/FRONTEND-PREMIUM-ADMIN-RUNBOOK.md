# NutriFit Premium/Admin integration notes

## Frontend changes
- Added `frontend/js/premium-admin.js` for plan listing, checkout creation, payment history, and admin dashboard/users/transactions.
- Added Premium and Admin actions to the existing dashboard navigation; existing screens were preserved.
- `frontend/js/auth.js` now retains `role`, `subscription_status`, and `premium_expires_at` in the client session and emits `nutrifit:session-updated`.
- `frontend/js/api.js` attaches `X-User-Id` from the current local display session and exposes payment/admin API methods.

## Payment safety
- The previous placeholder bank account was not a real verified account. VietQR now requires `NUTRIFIT_BANK_BIN`, `NUTRIFIT_BANK_ACCOUNT_NO`, and `NUTRIFIT_BANK_ACCOUNT_NAME` in the local `.env`; without them checkout returns a configuration error instead of presenting a misleading QR.
- `/api/payment/webhook` now requires `X-Payment-Signature`, an HMAC-SHA256 hex digest of the exact raw request body using `PAYMENT_WEBHOOK_SECRET`. If the secret is absent, the webhook is disabled. Do not set up automatic payment activation until the actual payment provider is configured to sign webhooks.
- This remains a local integration scaffold. Do not treat a transfer screenshot, transaction code, or UI state as proof of payment. Premium must only be enabled by a trusted, verified payment notification.

## Local run
1. Copy `.env.example` to `.env` and set local DB, mail, and Gemini values. Never commit `.env`.
2. Set the three `NUTRIFIT_BANK_*` values only when a real receiving account is confirmed.
3. Keep `PAYMENT_WEBHOOK_SECRET` private. It must match the provider's webhook signing configuration.
4. Restart backend after `.env` changes, then open `http://127.0.0.1:5500/frontend/index.html`.
5. Log out and log back in after updating Frontend files so the stored session refreshes the `role` field.

## Important security limitation
The current backend's `admin_required` trusts `X-User-Id` and looks up that user's role. This is not a strong authentication mechanism because a client can forge the header. It is acceptable only for controlled local testing; before deployment, replace this with server-validated session/JWT authentication and enforce role checks server-side.
