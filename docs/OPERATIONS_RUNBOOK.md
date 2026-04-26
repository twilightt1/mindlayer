# Operations Runbook

This runbook covers common SupportMind production-like operations.

## Quick Status

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/ready
```

`/health` checks API liveness. `/ready` checks Postgres, Redis, MinIO, and ChromaDB.

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
curl -fsS http://localhost:8001/api/v1/heartbeat
curl -fsS http://localhost:9000/minio/health/live
```

In the production overlay, ChromaDB and MinIO ports are internal by default. Temporarily expose them only when direct host checks are needed.

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
