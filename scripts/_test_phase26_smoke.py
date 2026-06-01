"""Smoke test for Phase 2.6 — connector hardening (backoff + cursor + error).

Covers:
  1. with_retry: 429 then 200 → retry succeeds
  2. with_retry: 500 then 200 → retry succeeds
  3. with_retry: exhausts after max_retries → raises HTTPStatusError
  4. with_retry: respects Retry-After header
  5. with_retry: transport error (ConnectTimeout) → retry succeeds
  6. BaseConnector: initial_cursor + last_cursor attributes
  7. Registry: passes initial_cursor to all 6 connectors
  8. Drive: incremental sync (cursor passed + last_cursor saved)
  9. Notion: incremental sync (cursor passed + last_cursor saved)
 10. Gmail: incremental sync (cursor passed + last_cursor saved)

Run: python scripts/_test_phase26_smoke.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import json
import time

import httpx

# Save reference to the REAL AsyncClient BEFORE any module monkey-patching.
# Otherwise lambdas/factories that reference `httpx.AsyncClient` would call
# themselves (because `svc.httpx IS httpx` and we patch the same attribute).
_REAL_ASYNC_CLIENT = httpx.AsyncClient

from app.ingestion.backoff import with_retry  # noqa: E402
from app.ingestion.base import BaseConnector  # noqa: E402
from app.ingestion.connectors.registry import get_connector_for_source  # noqa: E402
from app.ingestion.connectors.google_drive import GoogleDriveConnector  # noqa: E402
from app.ingestion.connectors.notion import NotionConnector  # noqa: E402
from app.ingestion.connectors.gmail import GmailConnector  # noqa: E402


def make_patched_client(transport: httpx.MockTransport):
    """Return a factory that builds an httpx.AsyncClient with the given transport."""
    def factory(*a, **kw):
        kw.pop("transport", None)
        return _REAL_ASYNC_CLIENT(transport=transport, **kw)
    return factory


def section(title: str) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


# ── BACKOFF UNIT TESTS ─────────────────────────────────────────────────────

async def test_429_then_200() -> None:
    section("TEST 1: with_retry handles 429 then 200")
    attempts = 0

    async def factory():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, text="ok")

    resp = await with_retry(factory, max_retries=3, base_delay=0.01, max_delay=0.05)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"
    assert attempts == 2, f"expected 2 attempts, got {attempts}"
    print(f"  PASS  (attempts={attempts}, status={resp.status_code})")


async def test_500_then_200() -> None:
    section("TEST 2: with_retry handles 500 then 200")
    attempts = 0

    async def factory():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return httpx.Response(500)
        return httpx.Response(200, text="ok")

    resp = await with_retry(factory, max_retries=3, base_delay=0.01, max_delay=0.05)
    assert resp.status_code == 200
    assert attempts == 2
    print(f"  PASS  (attempts={attempts}, status={resp.status_code})")


async def test_exhausts() -> None:
    section("TEST 3: with_retry exhausts after max_retries")
    attempts = 0

    async def factory():
        nonlocal attempts
        attempts += 1
        return httpx.Response(500)

    try:
        await with_retry(factory, max_retries=2, base_delay=0.01, max_delay=0.05)
        print("  FAIL  (expected HTTPStatusError)")
        raise SystemExit(1)
    except httpx.HTTPStatusError as e:
        assert e.response.status_code == 500
        assert attempts == 3, f"expected 3 attempts (1 + 2 retries), got {attempts}"
        print(f"  PASS  (raised HTTPStatusError after {attempts} attempts)")


async def test_retry_after() -> None:
    section("TEST 4: with_retry respects Retry-After header")
    attempts = 0
    start = time.monotonic()

    async def factory():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return httpx.Response(429, headers={"Retry-After": "0.1"})
        return httpx.Response(200, text="ok")

    resp = await with_retry(factory, max_retries=3, base_delay=0.01, max_delay=1.0)
    elapsed = time.monotonic() - start
    assert resp.status_code == 200
    assert attempts == 2
    assert elapsed >= 0.08, f"expected >= 0.08s (Retry-After=0.1s), got {elapsed:.3f}s"
    print(f"  PASS  (elapsed={elapsed:.3f}s, attempts={attempts})")


async def test_transport_error() -> None:
    section("TEST 5: with_retry handles transport error (ConnectTimeout)")
    attempts = 0

    async def factory():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise httpx.ConnectTimeout("simulated timeout")
        return httpx.Response(200, text="ok")

    resp = await with_retry(factory, max_retries=3, base_delay=0.01, max_delay=0.05)
    assert resp.status_code == 200
    assert attempts == 2
    print(f"  PASS  (retried after ConnectTimeout, attempts={attempts})")


# ── BASE + REGISTRY ─────────────────────────────────────────────────────────

def test_base_cursor() -> None:
    section("TEST 6: BaseConnector sets initial_cursor and last_cursor")

    class DummyConnector(BaseConnector):
        source_type = "dummy"
        async def fetch_items(self): return []

    c1 = DummyConnector(config={"x": 1})
    assert c1.initial_cursor is None, "default initial_cursor should be None"
    assert c1.last_cursor is None, "default last_cursor should be None"

    c2 = DummyConnector(config={"x": 1}, initial_cursor="abc")
    assert c2.initial_cursor == "abc", f"expected 'abc', got {c2.initial_cursor!r}"
    assert c2.last_cursor is None, "last_cursor still None before fetch"

    c2.last_cursor = "xyz"
    assert c2.last_cursor == "xyz"

    print("  PASS  (initial_cursor and last_cursor work)")


def test_registry_passes_initial_cursor() -> None:
    section("TEST 7: Registry passes initial_cursor to all 6 connectors")

    pairs = [
        ("manual",        {"title": "x", "content": "y"},              "C1"),
        ("file_upload",   {"filename": "x", "content": "y"},           "C2"),
        ("web_clipper",   {"url": "http://x"},                          "C3"),
        ("google_drive",  {"credentials": {"access_token": "tok"}},    "C4"),
        ("notion",        {"token": "tok"},                            "C5"),
        ("gmail",         {"credentials": {"access_token": "tok"}},    "C6"),
    ]
    for source_type, config, cursor in pairs:
        c = get_connector_for_source(source_type, config=config, initial_cursor=cursor)
        assert c.initial_cursor == cursor, (
            f"{source_type}: expected {cursor!r}, got {c.initial_cursor!r}"
        )
    print(f"  PASS  (all {len(pairs)} connectors receive initial_cursor)")


# ── CONNECTOR INCREMENTAL SYNC ──────────────────────────────────────────────

async def test_drive_incremental_sync() -> None:
    section("TEST 8: Drive incremental sync via MockTransport")

    list_requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "drive/v3/files" in url and "alt=media" not in url and "/export" not in url:
            params = dict(request.url.params)
            list_requests.append(params)
            page_token = params.get("pageToken")
            if page_token is None:
                # First call (no pageToken) → 1 file + nextPageToken
                return httpx.Response(200, json={
                    "files": [{"id": "f1", "name": "f1.txt", "mimeType": "text/plain",
                               "webViewLink": "https://drive.google.com/f1"}],
                    "nextPageToken": "TOKEN_2",
                })
            elif page_token in ("TOKEN_2", "CUSTOM_TOKEN"):
                # Resumed call → 1 file + no nextPageToken
                return httpx.Response(200, json={
                    "files": [{"id": "f2", "name": "f2.txt", "mimeType": "text/plain",
                               "webViewLink": "https://drive.google.com/f2"}],
                })
            return httpx.Response(200, json={"files": []})
        # File download
        return httpx.Response(200, text="file content")

    import app.ingestion.connectors.google_drive as drv
    orig = drv.httpx.AsyncClient

    # Case A: no initial cursor
    list_requests.clear()
    transport = httpx.MockTransport(handler)
    drv.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = GoogleDriveConnector(config={"credentials": {"access_token": "x"}})
        items_a = await c.fetch_items()
        last_a = c.last_cursor
    finally:
        drv.httpx.AsyncClient = orig

    assert len(items_a) == 2, f"Expected 2 items, got {len(items_a)}"
    assert len(list_requests) == 2, f"Expected 2 list calls, got {len(list_requests)}"
    assert "pageToken" not in list_requests[0], "First request should NOT have pageToken"
    assert list_requests[1].get("pageToken") == "TOKEN_2", "Second request should have pageToken=TOKEN_2"
    # Second call had no nextPageToken → loop exits, last_cursor stays None
    assert last_a is None, f"Expected last_cursor=None (exhausted), got {last_a!r}"
    print(f"  [A: no initial cursor] {len(items_a)} items, 2 list calls, last_cursor={last_a!r}")

    # Case B: with initial cursor
    list_requests.clear()
    transport = httpx.MockTransport(handler)
    drv.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = GoogleDriveConnector(
            config={"credentials": {"access_token": "x"}},
            initial_cursor="CUSTOM_TOKEN",
        )
        items_b = await c.fetch_items()
        last_b = c.last_cursor
    finally:
        drv.httpx.AsyncClient = orig

    assert len(items_b) == 1, f"Expected 1 item (only f2), got {len(items_b)}"
    assert len(list_requests) == 1, f"Expected 1 list call (resumed at TOKEN_2), got {len(list_requests)}"
    assert list_requests[0].get("pageToken") == "CUSTOM_TOKEN", (
        f"First request should have pageToken=CUSTOM_TOKEN, got {list_requests[0].get('pageToken')!r}"
    )
    assert last_b is None, f"Expected last_cursor=None (exhausted after 1 page), got {last_b!r}"
    print(f"  [B: initial_cursor='CUSTOM_TOKEN'] {len(items_b)} items, 1 list call, last_cursor={last_b!r}")

    print("  Drive incremental sync OK")


async def test_notion_incremental_sync() -> None:
    section("TEST 9: Notion incremental sync via MockTransport")

    db_requests: list[dict] = []
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        url = str(request.url)
        method = request.method
        if "/databases/dbid/query" in url and method == "POST":
            body = json.loads(request.content) if request.content else {}
            db_requests.append(body)
            cursor = body.get("start_cursor")
            if cursor is None:
                return httpx.Response(200, json={
                    "results": [{
                        "id": "p1", "object": "page", "url": "https://notion.so/p1",
                        "parent": {"type": "database_id", "database_id": "dbid"},
                        "properties": {"Name": {"type": "title",
                                                "title": [{"plain_text": "Page 1"}]}},
                        "created_time": "2026-05-20T10:00:00Z",
                        "last_edited_time": "2026-05-20T11:00:00Z",
                    }],
                    "has_more": True, "next_cursor": "CURSOR_2",
                })
            elif cursor == "CURSOR_2":
                return httpx.Response(200, json={
                    "results": [{
                        "id": "p2", "object": "page", "url": "https://notion.so/p2",
                        "parent": {"type": "database_id", "database_id": "dbid"},
                        "properties": {"Name": {"type": "title",
                                                "title": [{"plain_text": "Page 2"}]}},
                        "created_time": "2026-05-20T10:00:00Z",
                        "last_edited_time": "2026-05-20T11:00:00Z",
                    }],
                    "has_more": False,
                })
            return httpx.Response(200, json={"results": [], "has_more": False})
        if "/blocks/" in url and "/children" in url and method == "GET":
            return httpx.Response(200, json={"results": [], "has_more": False})
        return httpx.Response(404, text=f"unmocked: {method} {url}")

    import app.ingestion.connectors.notion as nt
    orig = nt.httpx.AsyncClient

    # Case A: no initial cursor
    db_requests.clear()
    call_count = 0
    transport = httpx.MockTransport(handler)
    nt.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = NotionConnector(config={"token": "secret_x", "database_id": "dbid"})
        items_a = await c.fetch_items()
        last_a = c.last_cursor
    finally:
        nt.httpx.AsyncClient = orig

    assert len(items_a) == 2, f"Expected 2 items, got {len(items_a)}"
    assert len(db_requests) == 2, f"Expected 2 db calls, got {len(db_requests)}"
    assert "start_cursor" not in db_requests[0], "First call should NOT have start_cursor"
    assert db_requests[1].get("start_cursor") == "CURSOR_2", (
        f"Second call should have start_cursor=CURSOR_2, got {db_requests[1].get('start_cursor')!r}"
    )
    assert last_a is None, f"Expected last_cursor=None (exhausted), got {last_a!r}"
    print(f"  [A: no initial cursor] {len(items_a)} items, 2 db calls, last_cursor={last_a!r}")

    # Case B: with initial cursor
    db_requests.clear()
    call_count = 0
    transport = httpx.MockTransport(handler)
    nt.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = NotionConnector(
            config={"token": "secret_x", "database_id": "dbid"},
            initial_cursor="CURSOR_2",
        )
        items_b = await c.fetch_items()
        last_b = c.last_cursor
    finally:
        nt.httpx.AsyncClient = orig

    assert len(items_b) == 1, f"Expected 1 item (only p2), got {len(items_b)}"
    assert len(db_requests) == 1, f"Expected 1 db call (resumed at CURSOR_2), got {len(db_requests)}"
    assert db_requests[0].get("start_cursor") == "CURSOR_2", (
        f"First call should have start_cursor=CURSOR_2, got {db_requests[0].get('start_cursor')!r}"
    )
    assert last_b is None
    print(f"  [B: initial_cursor='CURSOR_2'] {len(items_b)} items, 1 db call, last_cursor={last_b!r}")

    print("  Notion incremental sync OK")


async def test_gmail_incremental_sync() -> None:
    section("TEST 10: Gmail incremental sync via MockTransport")

    list_requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/messages?" in url and "/messages/m" not in url:
            params = dict(request.url.params)
            list_requests.append(params)
            page_token = params.get("pageToken")
            if page_token is None:
                return httpx.Response(200, json={
                    "messages": [{"id": "m1"}, {"id": "m2"}],
                    "nextPageToken": "PG_2",
                })
            elif page_token == "PG_2":
                return httpx.Response(200, json={
                    "messages": [{"id": "m3"}],
                })
            return httpx.Response(200, json={"messages": []})
        if "/messages/m" in url:
            msg_id = url.split("/messages/")[1].split("?")[0]
            return httpx.Response(200, json={
                "id": msg_id, "threadId": "t1",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": f"Subj {msg_id}"},
                        {"name": "From",    "value": "a@b.com"},
                        {"name": "To",      "value": "c@d.com"},
                        {"name": "Date",    "value": "Mon, 20 May 2026 10:00:00 +0700"},
                    ],
                },
            })
        return httpx.Response(404)

    import app.ingestion.connectors.gmail as gm
    orig = gm.httpx.AsyncClient

    # Case A: no initial cursor
    list_requests.clear()
    transport = httpx.MockTransport(handler)
    gm.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = GmailConnector(config={"credentials": {"access_token": "x"},
                                   "query": "in:inbox", "max_results": 10})
        items_a = await c.fetch_items()
        last_a = c.last_cursor
    finally:
        gm.httpx.AsyncClient = orig

    assert len(items_a) == 3, f"Expected 3 items, got {len(items_a)}"
    assert len(list_requests) == 2, f"Expected 2 list calls, got {len(list_requests)}"
    assert "pageToken" not in list_requests[0]
    assert list_requests[1].get("pageToken") == "PG_2"
    assert last_a is None
    print(f"  [A: no initial cursor] {len(items_a)} items, 2 list calls, last_cursor={last_a!r}")

    # Case B: with initial cursor
    list_requests.clear()
    transport = httpx.MockTransport(handler)
    gm.httpx.AsyncClient = make_patched_client(transport)
    try:
        c = GmailConnector(
            config={"credentials": {"access_token": "x"},
                    "query": "in:inbox", "max_results": 10},
            initial_cursor="PG_2",
        )
        items_b = await c.fetch_items()
        last_b = c.last_cursor
    finally:
        gm.httpx.AsyncClient = orig

    assert len(items_b) == 1, f"Expected 1 item (only m3), got {len(items_b)}"
    assert len(list_requests) == 1
    assert list_requests[0].get("pageToken") == "PG_2"
    assert last_b is None
    print(f"  [B: initial_cursor='PG_2'] {len(items_b)} items, 1 list call, last_cursor={last_b!r}")

    print("  Gmail incremental sync OK")


# ── MAIN ────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("=" * 64)
    print("PHASE 2.6 — CONNECTOR HARDENING (backoff + cursor + error)")
    print("=" * 64)

    # Backoff unit tests
    await test_429_then_200()
    await test_500_then_200()
    await test_exhausts()
    await test_retry_after()
    await test_transport_error()

    # Base + Registry
    test_base_cursor()
    test_registry_passes_initial_cursor()

    # Connector incremental sync
    await test_drive_incremental_sync()
    await test_notion_incremental_sync()
    await test_gmail_incremental_sync()

    print()
    print("=" * 64)
    print("ALL PHASE 2.6 TESTS PASSED")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(main())
