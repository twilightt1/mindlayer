"""
GmailConnector — STUB.

Planned Phase 2.5+ behavior:
    - Use the Gmail API (oauth credentials in `Source.config['credentials']`).
    - Fetch messages from `Source.config['label_ids']` (default INBOX)
      since `Source.config['last_history_id']` (incremental sync).
    - For each message, yield a `ConnectorItem` with the body,
      subject, sender, and message id.

For Phase 2 v0 this connector returns an empty list.
"""
from __future__ import annotations

import logging

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem

log = logging.getLogger(__name__)


class GmailConnector(BaseConnector):
    source_type: str = "gmail"

    def validate_config(self) -> None:
        creds = self.config.get("credentials") or {}
        if not creds.get("access_token") and not creds.get("refresh_token"):
            raise ValueError(
                "GmailConnector requires config['credentials']['access_token'] "
                "or config['credentials']['refresh_token']."
            )

    async def fetch_items(self) -> list[ConnectorItem]:
        log.info("GmailConnector: not yet implemented (returns 0 items). Phase 2.5 will wire the Gmail API.")
        return []
