"""
GoogleDriveConnector — STUB.

Planned Phase 2.5+ behavior:
    - Use the Google Drive API v3 (oauth credentials in
      `Source.config['credentials']`) to list files under a
      configured folder.
    - For each file, download its content, route to the right text
      extractor (Docs API for Google Docs, Sheets API for Sheets,
      raw download for PDFs, etc.), and yield a `ConnectorItem`.

For Phase 2 v0 this connector returns an empty list with an
informative note so the user can wire a Drive source in the UI
without seeing a 500 from the sync endpoint.
"""
from __future__ import annotations

import logging

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem

log = logging.getLogger(__name__)


class GoogleDriveConnector(BaseConnector):
    source_type: str = "google_drive"

    def validate_config(self) -> None:
        creds = self.config.get("credentials") or {}
        if not creds.get("access_token") and not creds.get("refresh_token"):
            raise ValueError(
                "GoogleDriveConnector requires config['credentials']['access_token'] "
                "or config['credentials']['refresh_token']."
            )

    async def fetch_items(self) -> list[ConnectorItem]:
        log.info(
            "GoogleDriveConnector: not yet implemented (returns 0 items). "
            "Phase 2.5 will wire the Drive API."
        )
        return []
