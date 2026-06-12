# API Authentication Guide

MindLayer APIs use bearer tokens for authenticated requests. Users,
admins, and integrations must authenticate before uploading memories or asking
recall questions.

## Login

Send email and password to `/api/v1/auth/login`. The response includes an
`access_token`, `refresh_token`, and `token_type`.

Access tokens expire after 15 minutes by default. Refresh tokens expire after 7
days by default.

## Authorization Header

Include the access token in every protected request:

```http
Authorization: Bearer <access_token>
```

## API Key Rotation

Workspace admins can rotate API keys from **Settings → Developer → API Keys**.
A newly generated key becomes active immediately. The previous key remains valid
for 10 minutes to allow safe deployment rollovers.

Recommended rotation steps:

1. Generate a new API key in the dashboard.
2. Update the key in your secret manager.
3. Restart or redeploy affected services.
4. Confirm successful API traffic with the new key.
5. Revoke the old key after the 10-minute grace period.

## 401 Unauthorized

A `401 Unauthorized` response usually means the access token is missing,
expired, revoked, or malformed.

Troubleshooting checklist:

- Confirm the `Authorization` header uses the `Bearer` scheme.
- Refresh the token through `/api/v1/auth/refresh` using the request body.
- Check that the user account is active and not soft-deleted.
- Verify the token was issued by the current environment.

## 403 Forbidden

A `403 Forbidden` response means the token is valid but the user lacks the
required permission. Admin endpoints require the `admin` role.
