"""
RSSConnector — pulls entries from one or more RSS/Atom feeds.

Configuration (`Source.config`):
    {
        "feed_url":  "https://blog.example.com/feed.xml",   # single feed
        # or
        "feed_urls": ["https://a.com/rss", "https://b.com/atom"],
        "max_items": 50,                # cap entries per feed per sync
        "user_agent": "MindLayer/1.0"
    }

Behavior:
    - Fetch each feed with httpx (async), then parse bytes with feedparser
      (feedparser's own URL fetch is blocking, so we do the I/O ourselves).
    - One `ConnectorItem` per entry. ``source_ref`` is the entry's stable id
      (guid/id, falling back to the link), which lets the dispatcher dedup
      across syncs — re-running a sync skips entries already stored.
    - ``captured_at`` comes from the entry's published/updated date.
    - Incremental: ``last_cursor`` is set to the newest entry timestamp seen,
      and on the next sync entries at or before that time are skipped.
    - A single failed feed or unparseable entry is recorded in
      ``self.fetch_errors`` and skipped — it never fails the whole sync.
"""
from __future__ import annotations

import calendar
import logging
from datetime import datetime
from time import struct_time
from urllib.parse import urlparse

import feedparser
import httpx

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem, ItemError

log = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 50
DEFAULT_USER_AGENT = "MindLayer/1.0 (+second-brain)"
HTTP_TIMEOUT = 20.0
MAX_CONTENT_CHARS = 50_000


def _is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except (ValueError, TypeError):
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _struct_to_datetime(value: struct_time | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.utcfromtimestamp(calendar.timegm(value))
    except (ValueError, OverflowError, TypeError):
        return None


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


def _entry_datetime(entry) -> datetime | None:
    return (
        _struct_to_datetime(entry.get("published_parsed"))
        or _struct_to_datetime(entry.get("updated_parsed"))
    )


def _entry_ref(entry) -> str | None:
    """Stable per-entry id used for dedup. Prefer guid/id, fall back to link."""
    ref = entry.get("id") or entry.get("link")
    return ref[:500] if isinstance(ref, str) and ref else None


def _entry_content(entry) -> str:
    # Atom <content> arrives as entry.content (list of dicts); RSS uses summary.
    content_list = entry.get("content")
    if content_list and isinstance(content_list, list):
        value = (content_list[0] or {}).get("value")
        if value:
            return _strip_html(value)
    summary = entry.get("summary")
    if summary:
        return _strip_html(summary)
    return ""


def _strip_html(raw: str) -> str:
    """Lightweight HTML→text. Uses bs4 if available, else returns raw."""
    try:
        from bs4 import BeautifulSoup

        text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
        return text or raw.strip()
    except Exception:  # noqa: BLE001 - degrade gracefully
        return raw.strip()


class RSSConnector(BaseConnector):
    source_type: str = "rss"

    def _feed_urls(self) -> list[str]:
        urls: list[str] = []
        single = self.config.get("feed_url")
        if isinstance(single, str) and single.strip():
            urls.append(single.strip())
        many = self.config.get("feed_urls")
        if isinstance(many, list):
            urls.extend(u.strip() for u in many if isinstance(u, str) and u.strip())
        # Dedup preserving order
        seen: set[str] = set()
        out: list[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    def validate_config(self) -> None:
        urls = self._feed_urls()
        if not urls:
            raise ValueError("RSSConnector requires config['feed_url'] or config['feed_urls']")
        if not all(_is_valid_http_url(url) for url in urls):
            raise ValueError("RSSConnector feed URLs must be valid http(s) URLs")

    async def fetch_items(self) -> list[ConnectorItem]:
        feed_urls = self._feed_urls()
        max_items = int(self.config.get("max_items", DEFAULT_MAX_ITEMS))
        ua = self.config.get("user_agent", DEFAULT_USER_AGENT)
        configured_tags = _config_tags(self.config, "rss")

        # Incremental cutoff from the previous sync.
        cutoff = self._parse_cursor(self.initial_cursor)
        newest_seen = cutoff

        items: list[ConnectorItem] = []
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": ua},
        ) as client:
            for feed_url in feed_urls:
                try:
                    resp = await client.get(feed_url)
                    resp.raise_for_status()
                except Exception as e:  # noqa: BLE001
                    log.warning("RSSConnector: failed to fetch %s — %s", feed_url, e)
                    self.fetch_errors.append(
                        ItemError(source_ref=feed_url, message=f"Failed to fetch feed: {e}")
                    )
                    continue

                parsed = feedparser.parse(resp.content)
                feed_title = (parsed.feed or {}).get("title") or feed_url

                count = 0
                for entry in parsed.entries:
                    if count >= max_items:
                        break
                    item, entry_dt = self._entry_to_item(entry, feed_url, feed_title)
                    if item is None:
                        continue
                    item = item.model_copy(update={"tags": _merge_tags(item.tags, configured_tags)})
                    # Incremental: skip entries at or before the last cursor.
                    if cutoff and entry_dt and entry_dt <= cutoff:
                        continue
                    items.append(item)
                    count += 1
                    if entry_dt and (newest_seen is None or entry_dt > newest_seen):
                        newest_seen = entry_dt

        # Advance the cursor so the next sync only sees newer entries.
        if newest_seen is not None:
            self.last_cursor = newest_seen.isoformat()
        return items

    def _entry_to_item(self, entry, feed_url: str, feed_title: str):
        ref = _entry_ref(entry)
        title = (entry.get("title") or "").strip() or "(untitled)"
        content = _entry_content(entry)
        if not content:
            # Title-only entries are valid memories; use the title as body.
            content = title
        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS] + f"\n\n[truncated at {MAX_CONTENT_CHARS} chars]"

        entry_dt = _entry_datetime(entry)
        link = entry.get("link")

        item = ConnectorItem(
            title=title[:500],
            content=content,
            summary=content[:500],
            source_ref=ref,
            source_url=link if isinstance(link, str) else None,
            source_excerpt=content[:500],
            captured_at=entry_dt or datetime.utcnow(),
            tags=["rss"],
            metadata={
                "feed_url": feed_url,
                "feed_title": feed_title,
                "fetched_with": "httpx+feedparser",
            },
        )
        return item, entry_dt

    @staticmethod
    def _parse_cursor(cursor: str | None) -> datetime | None:
        if not cursor:
            return None
        try:
            return datetime.fromisoformat(cursor)
        except (ValueError, TypeError):
            return None
