"""Notion ingestion connector (Phase 2.5 — real impl).

Uses httpx to talk to Notion API v1. Supports:
  - database_id filter via config['database_id']  (POST /databases/{id}/query)
  - workspace search via config['search_query']   (POST /search) if no database
  - page block tree fetching (recursive up to 3 levels)
  - block-to-text conversion (paragraph, headings, lists, to_do, code,
    quote, callout, divider, image, bookmark, embed, child_page, child_database)
  - per-page error isolation
  - pagination via start_cursor

Required Source.config = {
    'token':         'secret_...'  (Notion internal-integration token),
    'database_id':   '...' (optional — if set, query that DB; else search workspace),
    'search_query':  '...' (optional — workspace search filter),
}
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.ingestion.base import BaseConnector
from app.ingestion.backoff import with_retry
from app.ingestion.types import ConnectorItem
from app.services.oauth_service import (
    NOTION_API_BASE,
    NOTION_VERSION,
    get_valid_notion_token,
)

log = logging.getLogger(__name__)

MAX_BLOCK_DEPTH = 3  # safety cap for nested block trees


# ── helpers ──────────────────────────────────────────────────────────────────

async def _get_all_block_children(
    client: httpx.AsyncClient, headers: dict[str, str], block_id: str,
    depth: int = 0,
) -> list[dict[str, Any]]:
    """Recursively fetch block children up to MAX_BLOCK_DEPTH.

    Each block in the returned list is decorated with `_subchildren` key
    containing its own children (already processed recursively).
    """
    if depth >= MAX_BLOCK_DEPTH:
        return []

    children: list[dict] = []
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        resp = await with_retry(
            lambda: client.get(
                f"{NOTION_API_BASE}/blocks/{block_id}/children",
                headers=headers, params=params, timeout=30.0,
            )
        )
        data = resp.json()

        for block in data.get("results", []):
            if block.get("has_children"):
                block["_subchildren"] = await _get_all_block_children(
                    client, headers, block["id"], depth + 1,
                )
            else:
                block["_subchildren"] = []
            children.append(block)

        if not data.get("has_more") or not data.get("next_cursor"):
            break
        cursor = data["next_cursor"]

    return children


def _rich_text_to_str(rich: list[dict]) -> str:
    return "".join(rt.get("plain_text", "") for rt in (rich or []))


def _block_to_text(block: dict[str, Any], depth: int = 0) -> str:
    """Convert a Notion block (with _subchildren) to plain text."""
    indent = "  " * depth
    btype = block.get("type", "")

    # Container blocks
    if btype == "child_page":
        title = block.get("child_page", {}).get("title", "")
        return f"{indent}📄 **{title}**\n"
    if btype == "child_database":
        title = block.get("child_database", {}).get("title", "")
        return f"{indent}🗂 **{title}**\n"

    payload = block.get(btype, {}) or {}
    text = _rich_text_to_str(payload.get("rich_text", []))

    prefix = ""
    suffix = ""

    if btype == "heading_1":
        prefix = "# "
    elif btype == "heading_2":
        prefix = "## "
    elif btype == "heading_3":
        prefix = "### "
    elif btype == "bulleted_list_item":
        prefix = "- "
    elif btype == "numbered_list_item":
        prefix = "1. "
    elif btype == "to_do":
        prefix = "[x] " if payload.get("checked") else "[ ] "
    elif btype == "toggle":
        prefix = "▸ "
    elif btype == "quote":
        prefix = "> "
    elif btype == "callout":
        emoji = (payload.get("icon") or {}).get("emoji", "")
        prefix = f"{emoji} " if emoji else "💡 "
    elif btype == "code":
        lang = payload.get("language", "")
        prefix = f"```{lang}\n"
        suffix = "\n```"
    elif btype == "divider":
        return f"{indent}---\n"
    elif btype == "image":
        url = (payload.get("file") or payload.get("external") or {}).get("url", "")
        caption = _rich_text_to_str(payload.get("caption", []))
        return f"{indent}🖼 ![{caption}]({url})\n"
    elif btype == "video":
        url = (payload.get("file") or payload.get("external") or {}).get("url", "")
        return f"{indent}🎥 {url}\n"
    elif btype == "file":
        url = (payload.get("file") or payload.get("external") or {}).get("url", "")
        return f"{indent}📎 {url}\n"
    elif btype == "bookmark":
        url = payload.get("url", "")
        caption = _rich_text_to_str(payload.get("caption", []))
        return f"{indent}🔖 [{caption or url}]({url})\n"
    elif btype == "embed":
        url = payload.get("url", "")
        return f"{indent}🔗 <{url}>\n"
    elif btype == "equation":
        expr = payload.get("expression", "")
        return f"{indent}📐 {expr}\n"
    elif btype in ("paragraph", "unsupported", ""):
        prefix = ""
    else:
        # Unknown block type — render a placeholder so the user knows it was skipped
        return f"{indent}<!-- unsupported block: {btype} -->\n"

    line = f"{indent}{prefix}{text}{suffix}\n"
    sub = "".join(_block_to_text(c, depth + 1) for c in block.get("_subchildren", []))
    return line + sub


def _page_title(page: dict[str, Any]) -> str:
    """Extract a page's title from its properties (looks for type=='title')."""
    props = page.get("properties", {}) or {}
    for prop in props.values():
        if prop.get("type") == "title":
            return _rich_text_to_str(prop.get("title", [])) or "(untitled)"
    return "(untitled)"


async def _query_database(
    client: httpx.AsyncClient, headers: dict[str, str], database_id: str,
    initial_cursor: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """POST /v1/databases/{id}/query with pagination.

    Phase 2.6 incremental sync:
      - If `initial_cursor` is provided, resume from that start_cursor.
      - Returns ``(pages, last_cursor)`` (last_cursor = last next_cursor
        seen, or None if exhausted).
    """
    url = f"{NOTION_API_BASE}/databases/{database_id}/query"
    pages: list[dict] = []
    cursor: str | None = initial_cursor
    last_cursor: str | None = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor

        resp = await with_retry(
            lambda: client.post(url, headers=headers, json=body, timeout=30.0)
        )
        data = resp.json()
        pages.extend(data.get("results", []))
        next_cursor = data.get("next_cursor")
        if not data.get("has_more") or not next_cursor:
            # Exhausted → next sync restarts from beginning
            last_cursor = None
            break
        last_cursor = next_cursor
        cursor = next_cursor
    return pages, last_cursor


async def _search_workspace(
    client: httpx.AsyncClient, headers: dict[str, str], query: str | None = None,
    initial_cursor: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """POST /v1/search — list all pages in the integration's workspace.

    Phase 2.6: same cursor behavior as `_query_database`.
    """
    url = f"{NOTION_API_BASE}/search"
    pages: list[dict] = []
    cursor: str | None = initial_cursor
    last_cursor: str | None = None
    while True:
        body: dict[str, Any] = {
            "page_size": 100,
            "filter": {"value": "page", "property": "object"},
        }
        if query:
            body["query"] = query
        if cursor:
            body["start_cursor"] = cursor

        resp = await with_retry(
            lambda: client.post(url, headers=headers, json=body, timeout=30.0)
        )
        data = resp.json()
        pages.extend(data.get("results", []))
        next_cursor = data.get("next_cursor")
        if not data.get("has_more") or not next_cursor:
            # Exhausted → next sync restarts from beginning
            last_cursor = None
            break
        last_cursor = next_cursor
        cursor = next_cursor
    return pages, last_cursor


# ── connector ────────────────────────────────────────────────────────────────

class NotionConnector(BaseConnector):
    source_type = "notion"

    def __init__(
        self, config: dict, initial_cursor: str | None = None,
    ) -> None:
        super().__init__(config=config, initial_cursor=initial_cursor)

    def validate_config(self) -> None:
        if not self.config.get("token"):
            raise ValueError("NotionConnector requires config['token']")

    async def fetch_items(self) -> list[ConnectorItem]:
        try:
            token = await get_valid_notion_token(self.config)
        except ValueError as e:
            log.error("Notion: %s", e)
            return []

        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
        }

        items: list[ConnectorItem] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1) List pages
            try:
                if self.config.get("database_id"):
                    pages, last_cursor = await _query_database(
                        client, headers, self.config["database_id"],
                        initial_cursor=self.initial_cursor,
                    )
                else:
                    pages, last_cursor = await _search_workspace(
                        client, headers, self.config.get("search_query"),
                        initial_cursor=self.initial_cursor,
                    )
            except httpx.HTTPError:
                log.exception("Notion: list pages failed")
                raise

            # Phase 2.6: remember where the next sync should resume.
            self.last_cursor = last_cursor

            # 2) For each page, fetch its block tree and convert to text
            for page in pages:
                page_id = page.get("id", "unknown")
                try:
                    blocks = await _get_all_block_children(client, headers, page_id)
                    text = "".join(_block_to_text(b) for b in blocks).strip()
                    title = _page_title(page)
                    if not text:
                        text = "(empty page)"

                    parent = page.get("parent", {}) or {}
                    items.append(ConnectorItem(
                        title=title,
                        content=text,
                        source_ref=page_id,
                        source_url=page.get("url"),
                        source_excerpt=text[:300],
                        tags=["notion"],
                        metadata={
                            "page_id":          page_id,
                            "parent_type":      parent.get("type"),
                            "parent_id":        parent.get("page_id") or parent.get("database_id"),
                            "created_time":     page.get("created_time"),
                            "last_edited_time": page.get("last_edited_time"),
                            "block_count":      len(blocks),
                        },
                    ))
                except Exception as e:
                    log.warning("Notion: failed to fetch page %s: %s", page_id, e)
                    items.append(ConnectorItem(
                        title=f"Failed: {page_id}",
                        content=f"[Error fetching page: {e}]",
                        source_ref=page_id,
                        source_url=page.get("url"),
                        source_excerpt=str(e)[:500],
                        tags=["notion", "error"],
                        metadata={"error": str(e)},
                    ))

        return items
