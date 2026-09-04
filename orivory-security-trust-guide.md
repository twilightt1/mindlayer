# Orivory Security Architecture

> **Status: factual description of the code in this repository** (what is
> implemented today, not a roadmap or a compliance claim). For responsible
> disclosure see [SECURITY.md](SECURITY.md).

This document previously described aspirational controls (TLS 1.3-only
termination, certificate pinning, AES-256 at rest, anomaly detection,
24-month audit retention) that are **not implemented in this repository** —
several of them belong to a deployment layer that does not live here. It has
been rewritten to describe only what the code actually does.

## 1. Authentication & Sessions

- **Passwords**: bcrypt with per-hash salts (`app/services/auth_service.py`).
  Passwords longer than 72 bytes are pre-hashed with SHA-256 before bcrypt.
  Hashing runs on a worker thread (`asyncio.to_thread`) so it never blocks
  the event loop.
- **Access tokens**: JWTs signed with HS256 via `python-jose`; the algorithm
  is pinned for both sign and verify (no algorithm confusion). Expiry is
  validated on every request (`app/utils/security.py`).
- **Refresh tokens**: 432-bit urlsafe random strings. Only their SHA-256
  hashes are stored (Redis), rotated on every refresh, and invalidated on
  password change/reset and logout.
- **OAuth**: Google sign-in via Authlib with a single-use `state` stored
  server-side. (Known gap: `state` is not yet bound to a browser cookie —
  login-CSRF hardening is tracked as future work.)
- **Email verification**: 6-digit OTPs with a 5-attempt cap, plus
  time-limited link tokens.

## 2. Authorization

- Every object fetch re-checks ownership (`user_id == current_user.id`) at
  the router layer — no known IDOR paths (verified across memories,
  entities, relations, insights, sources, workspaces, admin).
- Admin endpoints chain through `require_admin`.
- Platform-wide aggregates (`/analytics/dau`) are admin-only.
- Per-user quotas are enforced atomically with a single conditional UPDATE
  (TOCTOU-safe), and per-user rate limits guard both chat and every
  LLM-triggering endpoint (insights, discovery, recall).

## 3. Data Protection

- **Connector secrets at rest** (`Source.config`: OAuth tokens, API keys):
  encrypted with Fernet (`EncryptedJSONB`, `app/models/types.py`). A
  production validator requires an explicit `CONFIG_ENCRYPTION_KEY`.
- **In transit**: this repository serves plain HTTP behind uvicorn; TLS
  termination is the deployment's responsibility (reverse proxy / load
  balancer). The compose files are for local development.
- **Postgres**: database-level access; per-user foreign keys with CASCADE.

## 4. Input Handling & Network Egress

- All SQL goes through SQLAlchemy expression language with bound
  parameters; no string-built SQL exists.
- Uploads are MIME-allowlisted and size-checked; object-storage keys are
  server-generated UUIDs plus conversation ids.
- **SSRF guards** (`app/utils/ssrf.py`): user-supplied RSS/web-clipper URLs
  are scheme-validated, resolved and checked against
  private/loopback/link-local/reserved/CGNAT ranges (IPv4+IPv6), redirects
  are re-validated per hop, and response bodies are capped at 5 MB.
- External data fetched by connectors is stored as content and rendered by
  React without `dangerouslySetInnerHTML`. Prompt-injection hardening for
  the LLM pipeline is tracked as future work.

## 5. Configuration Hardening

`app/config.py` fails fast in production (`ENVIRONMENT=production`) when:

- the JWT secret is missing, short, or a known placeholder;
- CORS origins contain `*`;
- MinIO credentials are left at defaults;
- `CONFIG_ENCRYPTION_KEY` is missing;
- required provider keys are absent.

Production deployments also disable the OpenAPI docs endpoints.

## 6. Secrets Handling

- `.env` is gitignored and untracked; `.env.example` documents the shape.
- Celery uses JSON-only serialization (no pickle).
- Refresh tokens, OTPs and reset tokens are passed by id through task
  queues where practical; the broker (Redis) should be network-isolated
  and AUTH-protected in production (compose currently leaves Redis
  unauthenticated on the internal network — do not expose it).

## 7. Known Gaps (honest list)

1. Redis, Flower, and MinIO in the dev compose run unauthenticated — fine
   locally, must be locked down for any shared deployment.
2. OAuth `state` is not bound to a browser cookie (login CSRF hardening).
3. Access tokens are not revocable mid-lifetime (no jti blacklist on
   password change; logout blacklists the jti, but onboarding-scope tokens
   minted with longer expiries can outlive it).
4. Verification/reset link tokens travel as URL query parameters — they
   can leak via access logs/history. Prefer the OTP flow.
5. No dependency scanning (pip-audit/Dependabot) wired up yet.
6. No automated anomaly detection or SIEM integration — audit logging
   covers admin actions only.

## 8. Reporting

Please report vulnerabilities per [SECURITY.md](SECURITY.md). The project
is open source; verified reports will be credited in the changelog.
