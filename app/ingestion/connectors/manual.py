"""
ManualNoteConnector — placeholder for `source_type='manual'`.

Manual memories are written directly via the API (`POST /memories`)
or as one-off web clips / file uploads. They do not need a background
sync, so this connector is intentionally a no-op.

A `Source` row with `source_type='manual'` can still be created (so the
UI has a place to show "manual notes" in the Sources list), but calling
`fetch_items()` returns an empty list. The dispatcher handles this
gracefully — a sync on a manual source is a 0-item, 0-error no-op.
"""
from __future__ import annotations

import logging

from app.ingestion.base import BaseConnector
from app.ingestion.types import ConnectorItem

log = logging.getLogger(__name__)


class ManualNoteConnector(BaseConnector):
    source_type: str = "manual"

    async def fetch_items(self) -> list[ConnectorItem]:
        log.debug("ManualNoteConnector: no-op (manual memories are written via the API)")
        return []
