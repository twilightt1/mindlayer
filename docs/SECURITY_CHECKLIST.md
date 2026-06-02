# Security Checklist

Use this checklist before deploying MindLayer to a public environment.

Legend:

- **Automated**: covered by [security_check.py](file:///d:/DL/rag-backend/rag-backend/scripts/security_check.py).
- **Runtime guardrail**: enforced by application settings or route dependencies.
- **Manual deploy check**: must be verified in the target hosting environment.

## Secrets

- [x] **Automated / runtime guardrail**: Generate a random `JWT_SECRET_KEY` with at least 32 characters.
- [ ] **Manual deploy check**: Rotate `JWT_SECRET_KEY` if it was ever committed or shared.
- [ ] **Manual deploy check**: Use strong non-default `POSTGRES_PASSWORD`.
- [x] **Automated / runtime guardrail**: Use non-default `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` in production.
- [x] **Automated / runtime guardrail**: Store provider keys outside git and require production values:
  - `OPENROUTER_API_KEY`
  - `OPENAI_API_KEY`
  - `JINA_API_KEY`
- [ ] **Manual deploy check**: Configure `SENDGRID_API_KEY` and Google OAuth credentials outside git.
- [ ] **Manual deploy check**: Do not paste secrets into issue trackers, logs, screenshots, or reports.

## CORS and Frontend Origins

- [x] **Automated / runtime guardrail**: Set `ALLOWED_ORIGINS` to explicit HTTP(S) origins.
- [x] **Automated / runtime guardrail**: Never use `ALLOWED_ORIGINS=*` in production.
- [ ] **Manual deploy check**: Set `FRONTEND_URL` to the real frontend URL.

## Authentication and Authorization

- [ ] **Manual deploy check**: Confirm admin accounts are limited and intentional.
- [ ] **Manual deploy check**: Confirm Google OAuth redirect URLs match deployed URLs.
- [ ] **Manual deploy check**: Confirm password reset and email verification links use production URLs.
- [x] **Automated / runtime guardrail**: Refresh tokens are stored in Redis
      as SHA-256 hashes; the raw token is never used as a key. Each user
      has a per-user index set so revocation is O(1).
- [x] **Automated / runtime guardrail**: `/refresh` and `/logout` hash the
      incoming token before any Redis interaction.
- [x] **Automated / runtime guardrail**: The email mock never logs the
      full HTML body. `EMAIL_MOCK_VERBOSE=True` is the only way to opt
      back in (dev environments only).
- [x] **Automated**: Confirm `/api/v1/admin/diagnostics` requires admin authorization.

## API and Rate Limiting

- [ ] **Manual deploy check**: Keep `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_PER_DAY` conservative for public demos.
- [ ] **Manual deploy check**: Put the API behind HTTPS.
- [ ] **Manual deploy check**: Prefer a reverse proxy with request body size limits.
- [x] **Automated / runtime guardrail**: Keep `/docs` disabled in production.
- [x] **Automated**: Confirm diagnostics responses do not include JWT secrets, provider API keys, DB URLs, Redis URLs, MinIO secrets, access tokens, refresh tokens, or passwords.

## File Uploads

- [ ] **Manual deploy check**: Keep file size limits enforced.
- [ ] **Manual deploy check**: Keep MIME type allow-list narrow.
- [ ] **Manual deploy check**: Treat uploaded documents as sensitive user data.
- [ ] **Manual deploy check**: Verify MinIO bucket permissions are private.

## Infrastructure Exposure

- [x] **Automated**: Do not expose Postgres publicly in the production compose override.
- [x] **Automated**: Do not expose Redis publicly in the production compose override.
- [x] **Automated**: Do not expose ChromaDB publicly in the production compose override.
- [x] **Automated**: Do not expose MinIO console publicly in the production compose override.
- [x] **Automated**: Keep Flower behind the `ops` profile or internal network.

## Logging

- [x] **Automated**: Diagnostics config summary excludes provider keys, JWTs, refresh tokens, passwords, DB URLs, Redis URLs, and MinIO secrets.
- [ ] **Manual deploy check**: Review application logs and error reporting integrations for PII handling.
- [ ] **Manual deploy check**: Avoid logging full uploaded document contents.

## Dependency and Image Hygiene

- [ ] **Manual deploy check**: Rebuild images regularly for base image security updates.
- [ ] **Manual deploy check**: Pin dependencies before a long-lived production deployment.
- [ ] **Manual deploy check**: Scan images if deploying beyond portfolio/demo scope.

## Pre-deploy Checks

```bash
python scripts/security_check.py
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
python eval/run_eval.py --mode offline --output-dir eval/results --top-k 5
```

After deployment:

```bash
curl -fsS https://api.example.com/health
curl -fsS https://api.example.com/ready
curl -fsS -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
  https://api.example.com/api/v1/admin/diagnostics
```

See [SECURITY_EVIDENCE.md](file:///d:/DL/rag-backend/rag-backend/docs/SECURITY_EVIDENCE.md) for Phase 16 evidence.
