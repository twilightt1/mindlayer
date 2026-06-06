"""P1.2 connector tests: web clipper hardening + RSS.

CI-safe: httpx clients are faked (no network); feedparser parses inline bytes.
"""
from __future__ import annotations

import pytest

from app.ingestion.connectors.registry import REGISTRY, get_connector_for_source
from app.ingestion.connectors.rss import RSSConnector
from app.ingestion.connectors.web_clipper import WebClipperConnector, _is_valid_http_url

pytestmark = pytest.mark.rag


# ── fakes ────────────────────────────────────────────────────────────────────


class FakeResponse:
    def __init__(self, *, text="", content=b"", status_code=200, headers=None):
        self.text = text
        self.content = content or text.encode("utf-8")
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeClient:
    """Stands in for httpx.AsyncClient as an async context manager."""

    def __init__(self, by_url):
        self._by_url = by_url

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url):
        result = self._by_url.get(url)
        if isinstance(result, Exception):
            raise result
        if result is None:
            raise RuntimeError("not found")
        return result


def _patch_client(monkeypatch, module, by_url):
    monkeypatch.setattr(module, "httpx", _HttpxShim(by_url))


class _HttpxShim:
    def __init__(self, by_url):
        self._by_url = by_url

    def AsyncClient(self, **kwargs):  # noqa: N802 - mimic httpx API
        return FakeClient(self._by_url)


# ── registry ─────────────────────────────────────────────────────────────────


def test_rss_registered():
    assert "rss" in REGISTRY
    conn = get_connector_for_source("rss", {"feed_url": "https://x.com/feed"})
    assert isinstance(conn, RSSConnector)


# ── web clipper ──────────────────────────────────────────────────────────────


class TestWebClipper:
    def test_url_validation(self):
        assert _is_valid_http_url("https://example.com/a")
        assert _is_valid_http_url("http://example.com")
        assert not _is_valid_http_url("ftp://example.com")
        assert not _is_valid_http_url("javascript:alert(1)")
        assert not _is_valid_http_url("not a url")

    def test_validate_config_rejects_no_valid_urls(self):
        conn = WebClipperConnector(config={"urls": ["ftp://nope"]})
        with pytest.raises(ValueError):
            conn.validate_config()

    @pytest.mark.asyncio
    async def test_clips_valid_url(self, monkeypatch):
        import app.ingestion.connectors.web_clipper as wc

        html = "<html><head><title>Hello</title></head><body><article><p>Body text here.</p></article></body></html>"
        _patch_client(monkeypatch, wc, {"https://ex.com/a": FakeResponse(text=html)})

        conn = WebClipperConnector(config={"urls": ["https://ex.com/a"]})
        items = await conn.fetch_items()

        assert len(items) == 1
        assert items[0].title == "Hello"
        assert "Body text here." in items[0].content
        assert items[0].source_ref == "https://ex.com/a"
        assert not conn.fetch_errors

    @pytest.mark.asyncio
    async def test_failed_url_becomes_error_not_memory(self, monkeypatch):
        import app.ingestion.connectors.web_clipper as wc

        _patch_client(monkeypatch, wc, {"https://ex.com/bad": RuntimeError("boom")})

        conn = WebClipperConnector(config={"urls": ["https://ex.com/bad"]})
        items = await conn.fetch_items()

        # The anti-pattern fix: NO fabricated memory, a real fetch error instead.
        assert items == []
        assert len(conn.fetch_errors) == 1
        assert conn.fetch_errors[0].source_ref == "https://ex.com/bad"

    @pytest.mark.asyncio
    async def test_dedups_and_skips_invalid_urls(self, monkeypatch):
        import app.ingestion.connectors.web_clipper as wc

        html = "<html><title>T</title><body><p>content body</p></body></html>"
        _patch_client(monkeypatch, wc, {"https://ex.com/a": FakeResponse(text=html)})

        conn = WebClipperConnector(
            config={"urls": ["https://ex.com/a", "https://ex.com/a", "ftp://bad"]}
        )
        items = await conn.fetch_items()

        assert len(items) == 1  # deduped
        assert any("Invalid" in e.message for e in conn.fetch_errors)  # ftp skipped


# ── RSS ──────────────────────────────────────────────────────────────────────


_RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Test Feed</title>
<item><title>First</title><link>https://ex.com/1</link><guid>guid-1</guid>
<description>First body</description><pubDate>Tue, 10 Jun 2025 09:00:00 GMT</pubDate></item>
<item><title>Second</title><link>https://ex.com/2</link>
<description>Second body</description><pubDate>Wed, 11 Jun 2025 09:00:00 GMT</pubDate></item>
</channel></rss>"""


class TestRSS:
    def test_validate_config_requires_feed(self):
        with pytest.raises(ValueError):
            RSSConnector(config={}).validate_config()
        RSSConnector(config={"feed_url": "https://x.com/feed"}).validate_config()

    @pytest.mark.asyncio
    async def test_parses_entries_with_stable_source_ref(self, monkeypatch):
        import app.ingestion.connectors.rss as rss_mod

        _patch_client(monkeypatch, rss_mod, {"https://x.com/feed": FakeResponse(content=_RSS)})

        conn = RSSConnector(config={"feed_url": "https://x.com/feed"})
        items = await conn.fetch_items()

        assert len(items) == 2
        # guid → source_ref; link fallback for the entry without guid.
        assert items[0].source_ref == "guid-1"
        assert items[1].source_ref == "https://ex.com/2"
        assert "First body" in items[0].content
        assert items[0].tags == ["rss"]
        # cursor advanced to the newest entry time
        assert conn.last_cursor is not None

    @pytest.mark.asyncio
    async def test_incremental_skips_old_entries(self, monkeypatch):
        import app.ingestion.connectors.rss as rss_mod

        _patch_client(monkeypatch, rss_mod, {"https://x.com/feed": FakeResponse(content=_RSS)})

        # Cursor set to the first entry's time → only the second (newer) returns.
        conn = RSSConnector(
            config={"feed_url": "https://x.com/feed"},
            initial_cursor="2025-06-10T09:00:00",
        )
        items = await conn.fetch_items()

        assert len(items) == 1
        assert items[0].title == "Second"

    @pytest.mark.asyncio
    async def test_feed_fetch_failure_is_error_not_crash(self, monkeypatch):
        import app.ingestion.connectors.rss as rss_mod

        _patch_client(monkeypatch, rss_mod, {"https://x.com/feed": RuntimeError("down")})

        conn = RSSConnector(config={"feed_url": "https://x.com/feed"})
        items = await conn.fetch_items()

        assert items == []
        assert len(conn.fetch_errors) == 1
        assert "Failed to fetch feed" in conn.fetch_errors[0].message
