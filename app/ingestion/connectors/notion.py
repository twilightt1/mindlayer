"""
NotionConnector — STUB.

Planned Phase 2.5+ behavior:
    - Use the Notion API (token in `Source.config['token']`).
    - For each database/page in `Source.config['database_ids']` /
      `page_ids`, fetch the page contents (recursively) and yield
      a `ConnectorItem` per page.

For Phase 2 v0 this connector returns an empty list.
"""
from __future__ import annotations

import logging

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem

log = logging.getLogger(__name__)


class NotionConnector(BaseConnector):
    source_type: str = "notion"

    def validate_config(self) -> None:
        if not self.config.get("token"):
            raise ValueError("NotionConnector requires config['token'].")

    async def fetch_items(self) -> list[ConnectorItem]:
        log.info("NotionConnector: not yet implemented (returns 0 items). Phase 2.5 will wire the Notion API.")
        return []
