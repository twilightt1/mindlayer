# Operations Runbook

This runbook covers common MindLayer production-like operations.

## Quick Status

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/ready
```

`/health` checks API liveness. `/ready` checks Postgres, Redis, MinIO, and ChromaDB.

## Admin Diagnostics

Use the admin-only diagnostics endpoint when `/ready` is degraded or ingestion appears stuck:

```bash
curl -fsS -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
  http://localhost:8000/api/v1/admin/diagnostics
```

The response includes:

- dependency checks for Postgres, Redis, MinIO, ChromaDB, and Celery
- secret-safe config summary such as model names, rate limits, and MinIO bucket
- ingestion counts by status
- recent failed documents
- documents stuck in `pending` or `processing` longer than the configured threshold

`status: degraded` means at least one dependency check failed. The endpoint intentionally excludes secrets such as JWT keys, provider API keys, DB URLs, Redis URLs, and MinIO secret keys.

## Logs

API logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f app
```

Celery worker logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f celery_worker
```

Infrastructure logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f postgres redis chromadb minio
```

## Restart Services

Restart API only:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart app
```

Restart ingestion worker:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart celery_worker
```

Restart all app services without deleting data:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d app celery_worker celery_beat
```

## Investigate `/ready` Degraded

1. Call `/ready` and inspect the failing dependency name.
2. Check logs for that dependency.
3. Verify service health:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec redis redis-cli ping
curl -fsS http://localhost:8001/api/v2/heartbeat
curl -fsS http://localhost:9000/minio/health/live
```

In the production overlay, ChromaDB and MinIO ports are internal by default. Temporarily expose them only when direct host checks are needed.

## Source Sync Failures

Symptoms:

- `POST /api/v1/sources/{id}/sync` returns errors > 0
- `Source.status` flips to `error` instead of returning to `connected`
- Newly ingested memories do not show up in chat retrieval

Checklist:

1. Inspect `Source.sync_error` from the admin diagnostics endpoint or a
   direct DB read — the message includes the failing connector or stage
   (config validation, fetch, persist, etc.).
2. Confirm the source config still matches the registered connector
   requirements (e.g. OAuth token is not expired, RSS URL is reachable).
3. Re-run a sync through the API or admin endpoint after the fix:

```bash
curl -fsS -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8000/api/v1/sources/$SOURCE_ID/sync
```

4. The dispatcher (`SourceSyncService`) is idempotent on
   `(source_id, source_ref)`: re-running the same sync after a fix
   updates rather than duplicates items.

## Stuck Document Ingestion

Symptoms:

- uploaded document stays `pending` or `processing`
- chat does not retrieve newly uploaded content

Checklist:

1. Check Celery worker logs.
2. Confirm Redis is healthy.
3. Confirm MinIO object exists.
4. Confirm ChromaDB health.
5. Confirm provider keys are configured.
6. Restart `celery_worker` if the worker is wedged.

Useful commands:

```bash
curl -fsS -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
  http://localhost:8000/api/v1/admin/diagnostics

docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=200 celery_worker
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart celery_worker
```

## Run Operational Smoke Evaluation

Offline smoke:

```bash
python eval/run_eval.py --mode offline --output-dir eval/results --top-k 5
```

Live API smoke after login/token setup:

```bash
python eval/run_eval.py --mode live-api \
  --api-base-url http://localhost:8000 \
  --access-token "$ACCESS_TOKEN" \
  --sample-docs sample_docs \
  --output-dir eval/results
```

## Flower

Flower is behind the `ops` profile in production compose.

Start it only when needed:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile ops up -d flower
```

Stop it after use:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop flower
```
