"""Async retry helper with exponential backoff for vendor API calls.

Handles 429 (rate limit) and 5xx (server error) responses with
exponential backoff and jitter. Respects `Retry-After` header if the
vendor sends one.

Usage:
    from app.ingestion.backoff import with_retry

    resp = await with_retry(lambda: client.get(url, headers=h))
    # instead of:
    # resp = await client.get(url, headers=h)
    # resp.raise_for_status()

Why a coro_factory (zero-arg callable) instead of the coroutine itself?
Because `httpx.Response` cannot be re-used — if we passed the same
coroutine twice, the second await would fail. The factory builds a
fresh request on each retry.
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Awaitable, Callable

import httpx

log = logging.getLogger(__name__)

# HTTP status codes that should trigger a retry.
#   408 Request Timeout
#   425 Too Early
#   429 Too Many Requests
#   500 Internal Server Error
#   502 Bad Gateway
#   503 Service Unavailable
#   504 Gateway Timeout
RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})


async def with_retry(
    coro_factory: Callable[[], Awaitable[httpx.Response]],
    *,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> httpx.Response:
    """Execute ``coro_factory()`` with exponential backoff on retryable errors.

    Args:
        coro_factory: Zero-arg callable returning a fresh
            ``Awaitable[httpx.Response]``. Called once per attempt.
        max_retries: Max retries AFTER the initial attempt. Default 5
            means up to 6 total attempts.
        base_delay: Initial delay in seconds (doubled each attempt).
        max_delay: Cap on delay between retries.

    Returns:
        The successful ``httpx.Response`` (status < 400 or non-retryable 4xx).

    Raises:
        httpx.HTTPStatusError: If all attempts returned a retryable status.
        httpx.TransportError: If all attempts errored at transport level.
        httpx.TimeoutException: If all attempts timed out.
    """
    last_exc: Exception | None = None
    last_resp: httpx.Response | None = None
    last_status: int | None = None

    for attempt in range(max_retries + 1):
        try:
            resp = await coro_factory()
            last_resp = resp
            if resp.status_code not in RETRYABLE_STATUS_CODES:
                return resp
            last_status = resp.status_code
            last_exc = None
        except (httpx.TransportError, httpx.TimeoutException) as e:
            last_exc = e
            last_resp = None
            last_status = None

        # If this was the last attempt, surface the failure.
        if attempt == max_retries:
            if last_resp is not None:
                # We know last_resp.status_code is in RETRYABLE_STATUS_CODES.
                # Raise HTTPStatusError directly so this works even when
                # the response is a mock (no .request attached, which
                # would make `raise_for_status()` raise RuntimeError).
                raise httpx.HTTPStatusError(
                    f"HTTP {last_resp.status_code} after {max_retries} retries",
                    request=httpx.Request("GET", "http://mock"),
                    response=last_resp,
                )
            assert last_exc is not None  # for type-checkers
            raise last_exc

        # Otherwise, sleep with backoff and try again.
        delay = _compute_delay(attempt, last_resp, base_delay, max_delay)
        if last_status is not None:
            status_desc = f"status {last_status}"
        elif last_exc is not None:
            status_desc = type(last_exc).__name__
        else:
            status_desc = "?"
        log.warning(
            "with_retry: attempt %d/%d failed (%s), sleeping %.2fs before retry",
            attempt + 1, max_retries + 1, status_desc, delay,
        )
        await asyncio.sleep(delay)

    # Unreachable: the loop always either returns or raises.
    raise RuntimeError("with_retry: exited loop unexpectedly")


def _compute_delay(
    attempt: int,
    last_resp: httpx.Response | None,
    base_delay: float,
    max_delay: float,
) -> float:
    """Compute the delay before the next retry.

    Priority:
      1. If vendor sent a valid `Retry-After` header, honor it (capped).
      2. Otherwise, exponential backoff with 50%-150% jitter.
    """
    if last_resp is not None:
        retry_after = last_resp.headers.get("Retry-After")
        if retry_after:
            try:
                # Retry-After can be a number of seconds OR an HTTP date.
                # We only handle the seconds form (most common).
                return min(float(retry_after), max_delay)
            except (ValueError, TypeError):
                pass  # malformed → fall through to exponential

    delay = min(base_delay * (2 ** attempt), max_delay)
    delay *= 0.5 + random.random()  # 50%-150% of computed delay
    return delay
