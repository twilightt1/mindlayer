# Changelog

All notable changes to MindLayer are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/) and the
project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] — Phase 1-3 remediation (2026-06-01 → 2026-06-02)

### Security

- **Refresh tokens are now hashed in Redis** (see `auth_service`).
  - Tokens are stored under `refresh:{sha256(token)}` instead of
    `refresh:{raw}`, so a Redis snapshot no longer yields a list of
    usable tokens.
  - A per-user index set `refresh_user:{user_id}` is maintained so
    `_invalidate_all_refresh()` runs in O(N_user_tokens) instead of
    scanning the full `refresh:*` keyspace.
  - New `auth_service._invalidate_one_refresh()` revokes a single
    token (used by `/logout` and refresh-rotation).
  - The `/api/v1/auth/refresh` and `/api/v1/auth/logout` endpoints
    hash incoming tokens before any Redis interaction.
- **Email mock no longer logs token-bearing bodies**. The mock
  implementation that runs when `SENDGRID_API_KEY` is empty previously
  printed the full HTML (containing OTP and password-reset tokens)
  to stdout. The new behaviour logs only recipient, subject, and
  body length. Set `EMAIL_MOCK_VERBOSE=True` to opt back in to the
  full body at `DEBUG` level (dev environments only).
- **Graph snapshot empty-state hardening**: `graph_snapshot` returns
  an empty snapshot when the user has no entities, avoiding an
  empty `IN (...)` SQL clause that depended on dialect tolerance.

### Added

- `Settings.EMAIL_MOCK_VERBOSE: bool = False` — opt-in verbose
  logging for the email mock (gates full HTML body output).
- `auth_service._hash_refresh_token()` — internal helper that returns
  the SHA-256 hex of a refresh token.
- `auth_service._invalidate_one_refresh()` — single-token revocation
  helper used by `/logout` and refresh-rotation.

### Changed

- **Source sync endpoint** (`/api/v1/sources/{id}/sync`) now calls
  `SourceSyncService.sync()` instead of returning a stub.
  - Errors surface as `Source.status = "error"` with
    `Source.sync_error` populated, never as an unhandled 500.
  - Module docstring updated to reflect the real behaviour.
- **Module-level `rag_graph`** in `app.api.v1.chat` so test code can
  monkeypatch the compiled graph. The SSE stream resolves the graph
  through a lazy accessor.
- **Embedder module**: `embedder.async_client` and
  `embedder.sync_client` are exposed via module `__getattr__` for
  lazy resolution and test injection. Production callers see a
  normal module attribute.
- **Graph re-exports**: `MAX_RETRIES`, `route_from_router`,
  `route_after_grade_docs`, and `route_after_grade_gen` are now
  re-exported from `app.agents.graph` with an explicit `__all__`.

### Fixed

- **Prompt construction test** aligned with the actual renderer
  output: `[Source N] (source_type - filename)`.
- **Unauthenticated chat test** now accepts 401 or 403, since 401 is
  the correct RFC response for missing credentials.
- **Test fixtures** in `tests/rag/test_graph_routing.py` now provide
  non-empty `grounding_context_chunks` so retry branches in the
  routing helpers are actually exercised.
- **Linter**: dropped unused imports across `app/`, `tests/`,
  `eval/`, and `scripts/`; replaced lambdas assigned to names
  (`E731`), unwrapped one-line `try/except` chains (`E701`), and
  annotated intentional late imports in smoke scripts with
  `# noqa: E402`. Final ruff run reports zero issues.

## Historical Releases

Phase 16 (prior) — Security readiness audit added
`scripts/security_check.py` and the production guardrails enforced by
`Settings._validate_production_settings()`. The audit covers
JWT-secret strength, CORS, default MinIO credentials, provider key
requirements, production-internal port stripping, Flower under the
`ops` profile, admin-only diagnostics authorization, secret-safe
diagnostics output, FastAPI docs disabled in production, and
explicit demo placeholders in `.env.example`.
