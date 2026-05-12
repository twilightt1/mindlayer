# Webhook Troubleshooting Guide

MindLayer can send webhooks for document ingestion, conversation events, and
billing changes. This guide helps support teams troubleshoot delivery issues.

## Webhook Retry Rules

Webhook delivery uses exponential backoff. MindLayer retries failed webhook
requests up to 8 times over 24 hours.

A webhook attempt is considered failed when the destination returns a non-2xx
status code or does not respond within 10 seconds.

## Signature Verification

Every webhook includes an `X-MindLayer-Signature` header. The receiving service
should compute an HMAC SHA-256 signature using the workspace webhook secret and
compare it with the header value.

## Common Failure Causes

- The destination endpoint returns `401` or `403`.
- The endpoint blocks MindLayer IP ranges.
- TLS certificates are expired or misconfigured.
- The server responds after the 10-second timeout.
- Signature verification uses the wrong webhook secret.

## Debugging Failed Webhooks

1. Open **Admin → Integrations → Webhooks**.
2. Select the failed endpoint.
3. Review the latest delivery attempts and response bodies.
4. Confirm the endpoint returns a `2xx` status within 10 seconds.
5. Rotate the webhook secret if signature verification continues to fail.

## Manual Replay

Admins can replay failed webhook events from the delivery log. Manual replay does
not count against normal retry limits.
