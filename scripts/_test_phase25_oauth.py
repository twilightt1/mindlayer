"""Smoke test for Phase 2.5 — unit tests (no network, no fetch).

Covers:
  1. GoogleTokenRefresher (cached / refresh / empty creds)
  2. Notion block-to-text helpers (paragraph, headings, lists, to_do, code, child_page, divider, nested)
  3. Gmail b64url decode + header lookup
  4. validate_config for Drive / Gmail / Notion connectors

For connector fetch tests with mocked vendor APIs, see:
  scripts/_test_phase25_connectors.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import time

import httpx

from app.ingestion.connectors.google_drive import GoogleDriveConnector
from app.ingestion.connectors.gmail import GmailConnector, _decode_b64url
from app.ingestion.connectors.notion import (
    NotionConnector,
    _block_to_text,
)
from app.services.oauth_service import google_token_refresher


def section(title: str) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


# ── TOKEN REFRESHER ───────────────────────────────────────────────────────────

async def test_token_refresher() -> None:
    section("TEST 1: GoogleTokenRefresher")

    # 1a) Cached access_token still valid → no refresh
    future = int(time.time()) + 3600
    cfg = {"credentials": {"access_token": "cached", "expires_at": future}}
    tok = await google_token_refresher.get_valid_token("drive", cfg)
    assert tok == "cached", f"Expected 'cached', got {tok!r}"
    print("  1a. cached valid token returned OK")

    # 1b) Expired access_token + valid refresh_token → refresh via mocked endpoint
    async def fake_handler(request: httpx.Request) -> httpx.Response:
        if "oauth2.googleapis.com/token" in str(request.url):
            return httpx.Response(200, json={"access_token": "REFRESHED", "expires_in": 3600})
        return httpx.Response(404)

    # Save real reference BEFORE patching to avoid infinite recursion
    real_async_client = httpx.AsyncClient
    def factory(*a, **kw):
        kw.pop("transport", None)
        return real_async_client(transport=httpx.MockTransport(fake_handler), **kw)

    cfg = {"credentials": {"access_token": "old", "refresh_token": "rt",
                           "expires_at": 1, "client_id": "cid", "client_secret": "csec"}}
    import app.services.oauth_service as svc
    orig = svc.httpx.AsyncClient
    svc.httpx.AsyncClient = factory
    try:
        tok = await google_token_refresher.get_valid_token("drive", cfg)
    finally:
        svc.httpx.AsyncClient = orig
    assert tok == "REFRESHED", f"Expected 'REFRESHED', got {tok!r}"
    print("  1b. expired token refreshed via refresh_token OK")

    # 1c) No credentials → ValueError
    try:
        await google_token_refresher.get_valid_token("drive", {})
    except ValueError as e:
        print(f"  1c. empty creds rejected: {e}")
    else:
        raise AssertionError("Expected ValueError for empty creds")


# ── NOTION HELPERS ────────────────────────────────────────────────────────────

def test_notion_helpers() -> None:
    section("TEST 2: Notion block-to-text")

    # 2a) paragraph
    assert _block_to_text({"type": "paragraph",
                           "paragraph": {"rich_text": [{"plain_text": "Hello"}]}}) == "Hello\n"
    print("  2a. paragraph OK")

    # 2b) heading_1
    assert _block_to_text({"type": "heading_1",
                           "heading_1": {"rich_text": [{"plain_text": "Title"}]}}) == "# Title\n"
    print("  2b. heading_1 OK")

    # 2c) bulleted_list_item
    assert _block_to_text({"type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": [{"plain_text": "item"}]}}) == "- item\n"
    print("  2c. bulleted list OK")

    # 2d) to_do unchecked + checked
    assert _block_to_text({"type": "to_do",
                           "to_do": {"rich_text": [{"plain_text": "task"}], "checked": False}}) == "[ ] task\n"
    assert _block_to_text({"type": "to_do",
                           "to_do": {"rich_text": [{"plain_text": "task"}], "checked": True}}) == "[x] task\n"
    print("  2d. to_do OK (checked + unchecked)")

    # 2e) code with language
    assert _block_to_text({"type": "code",
                           "code": {"rich_text": [{"plain_text": "print(1)"}],
                                    "language": "python"}}) == "```python\nprint(1)\n```\n"
    print("  2e. code block OK")

    # 2f) child_page
    assert _block_to_text({"type": "child_page",
                           "child_page": {"title": "My Page"}}) == "📄 **My Page**\n"
    print("  2f. child_page OK")

    # 2g) divider
    assert _block_to_text({"type": "divider", "divider": {}}) == "---\n"
    print("  2g. divider OK")

    # 2h) nested list (parent with child)
    out = _block_to_text({
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"plain_text": "parent"}]},
        "_subchildren": [{
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"plain_text": "child"}]},
            "_subchildren": [],
        }],
    })
    assert out == "- parent\n  - child\n", f"Got: {out!r}"
    print("  2h. nested list OK")


# ── GMAIL HELPERS ─────────────────────────────────────────────────────────────

def test_gmail_helpers() -> None:
    section("TEST 3: Gmail b64url decode + header lookup")

    # 3a) b64url decode (round-trip)
    from base64 import urlsafe_b64encode
    encoded = urlsafe_b64encode(b"Hello world").rstrip(b"=").decode()
    assert _decode_b64url(encoded) == "Hello world"
    print("  3a. _decode_b64url OK")

    # 3b) _get_header (case-insensitive)
    from app.ingestion.connectors.gmail import _get_header
    headers = [
        {"name": "Subject", "value": "Test Subject"},
        {"name": "From",    "value": "foo@bar.com"},
    ]
    assert _get_header(headers, "Subject") == "Test Subject"
    assert _get_header(headers, "subject") == "Test Subject"
    assert _get_header(headers, "X-Missing") == ""
    print("  3b. _get_header OK (case-insensitive)")


# ── VALIDATE CONFIG ───────────────────────────────────────────────────────────

def test_validate_config() -> None:
    section("TEST 4: validate_config for all 3 connectors")

    try: GoogleDriveConnector(config={}).validate_config()
    except ValueError as e: print(f"  Drive empty: rejected ({e})")
    GoogleDriveConnector(config={"credentials": {"access_token": "x"}}).validate_config()
    print("  Drive with access_token: OK")

    try: GmailConnector(config={}).validate_config()
    except ValueError as e: print(f"  Gmail empty: rejected ({e})")
    GmailConnector(config={"credentials": {"refresh_token": "x"}}).validate_config()
    print("  Gmail with refresh_token: OK")

    try: NotionConnector(config={}).validate_config()
    except ValueError as e: print(f"  Notion empty: rejected ({e})")
    NotionConnector(config={"token": "secret_xyz"}).validate_config()
    print("  Notion with token: OK")


# ── MAIN ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("=" * 64)
    print("PHASE 2.5 — UNIT TESTS (no network, no fetch)")
    print("=" * 64)

    await test_token_refresher()
    test_notion_helpers()
    test_gmail_helpers()
    test_validate_config()

    print()
    print("=" * 64)
    print("ALL PHASE 2.5 UNIT TESTS PASSED")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(main())
