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
    - Yields one `ConnectorItem` per URL that succeeds.
    - A single failed URL is recorded in ``self.fetch_errors`` (surfaced
      by the dispatcher as a sync error) and skipped — it does NOT fail
      the whole sync and does NOT create a junk memory.

This connector lets a user wire a feed of URLs to their second brain
without any external service. ``clip_url()`` is exposed as a helper for
a one-off "save this URL" path.
"""
from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem, ItemError

log = logging.getLogger(__name__)

DEFAULT_MAX_CHARS = 50_000
DEFAULT_USER_AGENT = "MindLayer/1.0 (+second-brain)"
HTTP_TIMEOUT = 20.0
MAX_URLS_PER_SYNC = 100


def _is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except (ValueError, TypeError):
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _merge_tags(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for tag in group:
            clean = str(tag).strip()
            if clean and clean not in merged:
                merged.append(clean)
    return merged[:50]


def _config_tags(config: dict, default: str) -> list[str]:
    raw = config.get("tags") or []
    tags = [default]
    if isinstance(raw, str):
        tags.extend(part.strip() for part in raw.split(","))
    elif isinstance(raw, list):
        tags.extend(str(part).strip() for part in raw)
    return _merge_tags(tags)


class WebClipperConnector(BaseConnector):
    source_type: str = "web_clipper"

    def _urls(self) -> list[str]:
        urls: list[str] = []
        single = self.config.get("url")
        if isinstance(single, str) and single.strip():
            urls.append(single.strip())
        many = self.config.get("urls")
        if isinstance(many, list):
            urls.extend(u.strip() for u in many if isinstance(u, str) and u.strip())

        seen: set[str] = set()
        out: list[str] = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                out.append(url)
        return out

    def validate_config(self) -> None:
        urls = self._urls()
        if not urls:
            raise ValueError("WebClipperConnector requires config['url'] or config['urls']")
        if not any(_is_valid_http_url(u) for u in urls):
            raise ValueError("WebClipperConnector config contains no valid http(s) URLs")

    async def fetch_items(self) -> list[ConnectorItem]:
        raw_urls = self._urls()
        max_chars: int = int(self.config.get("max_chars", DEFAULT_MAX_CHARS))
        ua: str = self.config.get("user_agent", DEFAULT_USER_AGENT)
        source_title = self.config.get("title")
        configured_tags = _config_tags(self.config, "web_clip")

        # Dedup while preserving order; cap the batch size.
        seen: set[str] = set()
        urls: list[str] = []
        for u in raw_urls:
            if not isinstance(u, str) or not _is_valid_http_url(u):
                self.fetch_errors.append(
                    ItemError(source_ref=str(u)[:500], message="Invalid or non-http(s) URL; skipped")
                )
                continue
            if u in seen:
                continue
            seen.add(u)
            urls.append(u)
        urls = urls[:MAX_URLS_PER_SYNC]

        items: list[ConnectorItem] = []
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": ua},
        ) as client:
            for url in urls:
                try:
                    item = await _clip_url(client, url, max_chars)
                    metadata = dict(item.metadata or {})
                    if isinstance(source_title, str) and source_title.strip():
                        metadata["source_title"] = source_title.strip()
                    items.append(item.model_copy(update={
                        "title": source_title.strip()[:500]
                        if isinstance(source_title, str) and source_title.strip() and len(urls) == 1
                        else item.title,
                        "tags": _merge_tags(item.tags, configured_tags),
                        "metadata": metadata,
                    }))
                except Exception as e:  # noqa: BLE001
                    # Record as a sync error and skip — never fabricate a memory.
                    log.warning("WebClipperConnector: failed to clip %s — %s", url, e)
                    self.fetch_errors.append(
                        ItemError(source_ref=url, message=f"Failed to clip: {e}")
                    )
        return items


# ── Public helper used by a one-off "save this URL" path ──────────────────

async def clip_url(url: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> ConnectorItem:
    """Clip a single URL and return a ConnectorItem. Raises on failure."""
    if not _is_valid_http_url(url):
        raise ValueError("clip_url requires an http(s) URL")
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

    content_type = response.headers.get("content-type", "").lower()
    if content_type and "html" not in content_type and "xml" not in content_type:
        raise ValueError(f"Unsupported content-type for web clip: {content_type!r}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Drop noise
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Prefer <article> or <main> for body
    body_el = soup.find("article") or soup.find("main") or soup.body or soup

    # Title
    title_el = soup.find("title")
    title = (title_el.get_text(strip=True) if title_el else "") or urlparse(url).netloc or url

    # Collect text block-by-block so we keep some structure
    blocks: list[str] = []
    for el in body_el.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre"]):
        txt = el.get_text(" ", strip=True)
        if txt:
            blocks.append(txt)
    text = "\n\n".join(blocks).strip() or body_el.get_text(" ", strip=True).strip()

    if not text:
        raise ValueError("No extractable text content on page")

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
        content=text,
        summary=text[:500],
        source_ref=url,
        source_url=url,
        source_excerpt=text[:500],
        captured_at=captured_at,
        tags=["web_clip"],
        metadata={"url": url, "fetched_with": "httpx+bs4", "status_code": response.status_code},
    )
