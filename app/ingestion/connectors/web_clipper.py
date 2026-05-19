"""
WebClipperConnector — fetches a list of URLs and turns each into a memory.

Configuration (`Source.config`):
    {
        "urls": [
            "https://example.com/article-1",
            "https://example.com/article-2"
        ],
        "max_chars": 50_000,            # truncate huge pages
        "user_agent": "MindLayer/1.0"
    }

Behavior:
    - For each URL, GET the page with httpx.
    - Extract the main text with a BeautifulSoup-based heuristic
      (drop <script>, <style>, <nav>, <header>, <footer>, <aside>).
    - Title from <title> tag, fallback to URL hostname.
    - Yields one `ConnectorItem` per URL.
    - Soft errors: a single failed URL produces an `ItemError`
      rather than failing the whole sync.

This connector is the one with the most "real" behavior in Phase 2
v0 — it lets a user wire a feed of URLs to their second brain
without any external service. Real "save this URL now" actions
go through the dedicated `POST /sources/{id}/web-clip` endpoint
which is a thin wrapper around `clip_url()`.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem, ItemError

log = logging.getLogger(__name__)

DEFAULT_MAX_CHARS = 50_000
DEFAULT_USER_AGENT = "MindLayer/1.0 (+second-brain)"
HTTP_TIMEOUT = 20.0


class WebClipperConnector(BaseConnector):
    source_type: str = "web_clipper"

    def validate_config(self) -> None:
        urls = self.config.get("urls")
        if not urls or not isinstance(urls, list):
            raise ValueError("WebClipperConnector requires config['urls'] to be a non-empty list")

    async def fetch_items(self) -> list[ConnectorItem]:
        urls: list[str] = self.config.get("urls", [])
        max_chars: int  = int(self.config.get("max_chars", DEFAULT_MAX_CHARS))
        ua: str         = self.config.get("user_agent", DEFAULT_USER_AGENT)

        items: list[ConnectorItem] = []
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": ua},
        ) as client:
            for url in urls:
                try:
                    items.append(await _clip_url(client, url, max_chars))
                except Exception as e:
                    # Bubble as ItemError; dispatcher logs the rest.
                    log.warning("WebClipperConnector: failed to clip %s — %s", url, e)
                    # We can't return ItemError from fetch_items (it returns
                    # items, not errors), so we surface a tiny placeholder
                    # memory tagged with the error so the user sees it.
                    items.append(ConnectorItem(
                        title=f"[Failed] {url}",
                        content=f"Could not clip this URL: {e}",
                        source_ref=url,
                        source_url=url,
                        tags=["error", "web_clip_failed"],
                        metadata={"error": str(e), "url": url},
                    ))
        return items


# ── Public helper used by the one-off web-clip API endpoint ────────────────

async def clip_url(url: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> ConnectorItem:
    """Clip a single URL synchronously and return a ConnectorItem."""
    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    ) as client:
        return await _clip_url(client, url, max_chars)


# ── Internals ───────────────────────────────────────────────────────────────

async def _clip_url(client: httpx.AsyncClient, url: str, max_chars: int) -> ConnectorItem:
    response = await client.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Drop noise
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Prefer <article> or <main> for body
    body_el = soup.find("article") or soup.find("main") or soup.body or soup

    # Title
    title_el = soup.find("title")
    title = (title_el.get_text(strip=True) if title_el else "") or urlparse(url).netloc

    # Collect text block-by-block so we keep some structure
    blocks: list[str] = []
    for el in body_el.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre"]):
        txt = el.get_text(" ", strip=True)
        if txt:
            blocks.append(txt)
    text = "\n\n".join(blocks).strip() or body_el.get_text(" ", strip=True)

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[truncated at {max_chars} chars]"

    # Try to capture a publication date from common meta tags
    captured_at = datetime.utcnow()
    for meta_name in ("article:published_time", "og:published_time", "date", "DC.date.issued"):
        meta = soup.find("meta", attrs={"property": meta_name}) or soup.find("meta", attrs={"name": meta_name})
        if meta and meta.get("content"):
            try:
                captured_at = datetime.fromisoformat(meta["content"].replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass
            break

    return ConnectorItem(
        title=title[:500],
        content=text or "(empty page)",
        summary=text[:500] if text else None,
        source_ref=url,
        source_url=url,
        source_excerpt=text[:500] if text else None,
        captured_at=captured_at,
        tags=["web_clip"],
        metadata={"url": url, "fetched_with": "httpx+bs4", "status_code": response.status_code},
    )
