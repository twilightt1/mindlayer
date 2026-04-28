# Security Evidence — Phase 16 Readiness Audit

This document captures the Phase 16 security and production-hardening audit for
SupportMind.

## Scope

The audit focused on deterministic, repository-local checks that can run before a
portfolio demo or deployment review:

- production settings guardrails
- production compose exposure controls
- admin diagnostics authorization
- secret-safe diagnostics config summary
- production docs exposure
- explicit demo placeholders in `.env.example`

## Automated Command

```powershell
.\.venv\Scripts\python.exe scripts/security_check.py
```

Result:

```text
Security readiness checks
=========================
[PASS] production safe settings: Complete safe production settings are accepted
[PASS] placeholder JWT secret: Rejected unsafe production settings: JWT_SECRET_KEY
[PASS] wildcard CORS: Rejected unsafe production settings: ALLOWED_ORIGINS
[PASS] default MinIO credentials: Rejected unsafe production settings: Default MinIO
[PASS] required provider keys: Rejected unsafe production settings: OPENAI_API_KEY
[PASS] production internal ports: Internal service host ports are removed in prod override
[PASS] flower ops profile: Flower is behind the ops profile in prod override
[PASS] admin diagnostics auth: Diagnostics endpoint depends on require_admin
[PASS] diagnostics secret redaction: Diagnostics summary exposes only secret-safe config
[PASS] production docs disabled: FastAPI docs are disabled when ENVIRONMENT=production
[PASS] env example placeholders: .env.example keeps demo placeholders explicit

All security readiness checks passed.
```

## Guardrails Verified

| Area | Evidence |
| --- | --- |
| JWT secret | Production settings reject placeholder and short values. |
| CORS | Production settings reject wildcard origins. |
| Provider keys | Production settings require OpenRouter, embedding, and Jina keys. |
| MinIO credentials | Production settings reject default `minioadmin` credentials. |
| Internal services | Production compose removes host ports for Postgres, Redis, ChromaDB, MinIO, and Flower. |
| Flower | Production compose places Flower behind the `ops` profile. |
| Admin diagnostics | `/api/v1/admin/diagnostics` depends on `require_admin`. |
| Diagnostics output | Config summary excludes secret-bearing keys and connection URLs. |
| API docs | FastAPI docs are disabled when `ENVIRONMENT=production`. |
| Env template | `.env.example` keeps demo placeholders explicit and non-production. |

## Manual Deploy Checks Still Required

Some items must be verified in the target deployment environment and cannot be
fully proven by repository-local checks:

- Rotate secrets if they were ever shared.
- Use a strong non-default production database password.
- Configure SendGrid and Google OAuth credentials outside git.
- Confirm deployed OAuth redirect URLs and frontend URLs.
- Confirm admin accounts are limited and intentional.
- Put the API behind HTTPS.
- Enforce reverse proxy request body limits.
- Verify MinIO bucket permissions are private.
- Review logs and error reporting for PII handling.
- Rebuild and scan production images on a release cadence.

## Related Files

- [security_check.py](file:///d:/DL/rag-backend/rag-backend/scripts/security_check.py)
- [SECURITY_CHECKLIST.md](file:///d:/DL/rag-backend/rag-backend/docs/SECURITY_CHECKLIST.md)
- [config.py](file:///d:/DL/rag-backend/rag-backend/app/config.py)
- [diagnostics_service.py](file:///d:/DL/rag-backend/rag-backend/app/services/diagnostics_service.py)
- [admin.py](file:///d:/DL/rag-backend/rag-backend/app/api/v1/admin.py)
- [docker-compose.prod.yml](file:///d:/DL/rag-backend/rag-backend/docker-compose.prod.yml)

## Outcome

Phase 16 security readiness passed for automated repository-local controls. The
project now has an executable security gate plus an evidence-backed checklist for
manual deployment review.
