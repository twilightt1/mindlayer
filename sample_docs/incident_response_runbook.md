# Incident Response Runbook

This runbook helps support and engineering teams respond to production incidents
that affect SupportMind customers.

## Severity Levels

| Severity | Description | Response time |
| --- | --- | --- |
| SEV-1 | Full outage or data isolation risk | 15 minutes |
| SEV-2 | Major feature unavailable for many customers | 30 minutes |
| SEV-3 | Degraded performance or partial outage | 4 hours |
| SEV-4 | Minor issue or cosmetic bug | Next business day |

## Escalation Steps

1. Confirm the issue using health checks, logs, and customer reports.
2. Open an incident channel in Slack.
3. Assign an incident commander.
4. Post customer-facing status updates every 30 minutes for SEV-1 and SEV-2.
5. Escalate to engineering if the issue affects authentication, document
   ingestion, retrieval quality, or data isolation.

## Redis Latency Spike

If Redis latency spikes, check connection pool exhaustion, slow commands, worker
queue backlog, and memory pressure. Restart workers only after confirming that
Celery queues are not actively processing critical ingestion jobs.

## ChromaDB Retrieval Issues

If vector retrieval returns empty results for ready documents:

- Confirm the document status is `ready`.
- Check the ChromaDB collection for the conversation.
- Re-run ingestion for the affected document.
- Compare BM25 results to isolate vector-only failures.

## Post-Incident Review

Every SEV-1 and SEV-2 requires a post-incident review within 5 business days.
The review must include impact, timeline, root cause, remediation, and follow-up
owners.
