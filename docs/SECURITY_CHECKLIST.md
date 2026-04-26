# Security Checklist

Use this checklist before deploying SupportMind to a public environment.

## Secrets

- [ ] Generate a random `JWT_SECRET_KEY` with at least 32 characters.
- [ ] Rotate `JWT_SECRET_KEY` if it was ever committed or shared.
- [ ] Use strong non-default `POSTGRES_PASSWORD`.
- [ ] Use non-default `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`.
- [ ] Store provider keys outside git:
  - `OPENROUTER_API_KEY`
  - `OPENAI_API_KEY`
  - `JINA_API_KEY`
  - `SENDGRID_API_KEY`
  - Google OAuth credentials
- [ ] Do not paste secrets into issue trackers, logs, screenshots, or reports.

## CORS and Frontend Origins

- [ ] Set `ALLOWED_ORIGINS` to explicit HTTP(S) origins.
- [ ] Never use `ALLOWED_ORIGINS=*` in production.
- [ ] Set `FRONTEND_URL` to the real frontend URL.

## Authentication and Authorization

- [ ] Confirm admin accounts are limited and intentional.
- [ ] Confirm Google OAuth redirect URLs match deployed URLs.
- [ ] Confirm password reset and email verification links use production URLs.
- [ ] Confirm refresh token storage/expiration policy matches product expectations.

## API and Rate Limiting

- [ ] Keep `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_PER_DAY` conservative for public demos.
- [ ] Put the API behind HTTPS.
- [ ] Prefer a reverse proxy with request body size limits.
- [ ] Keep `/docs` disabled in production unless intentionally exposed.

## File Uploads

- [ ] Keep file size limits enforced.
- [ ] Keep MIME type allow-list narrow.
- [ ] Treat uploaded documents as sensitive user data.
- [ ] Verify MinIO bucket permissions are private.

## Infrastructure Exposure

- [ ] Do not expose Postgres publicly.
- [ ] Do not expose Redis publicly.
- [ ] Do not expose ChromaDB publicly unless protected by network controls.
- [ ] Do not expose MinIO console publicly unless protected.
- [ ] Keep Flower behind the `ops` profile or internal network.

## Logging

- [ ] Do not log provider keys, JWTs, refresh tokens, or passwords.
- [ ] Avoid logging full uploaded document contents.
- [ ] Review error reporting integrations for PII handling.

## Dependency and Image Hygiene

- [ ] Rebuild images regularly for base image security updates.
- [ ] Pin dependencies before a long-lived production deployment.
- [ ] Scan images if deploying beyond portfolio/demo scope.

## Pre-deploy Checks

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
python eval/run_eval.py --mode offline --output-dir eval/results --top-k 5
```

After deployment:

```bash
curl -fsS https://api.example.com/health
curl -fsS https://api.example.com/ready
```
