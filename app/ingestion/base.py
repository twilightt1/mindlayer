"""
Base class for all MindLayer source connectors.

A connector is a thin adapter around one source type. It owns the
remote-API logic (or, for stubs, a "not implemented" path) and
yields `ConnectorItem` values for the dispatcher to persist.

Subclasses must:
    1. Set `source_type` to a value from `app.models.source.SOURCE_TYPES`.
    2. Implement `async fetch_items()` to return a list of items.
    3. Optionally override `validate_config()` to check the
       `Source.config` JSONB has the keys the connector needs.

Connectors should NOT touch the database directly. They return items;
the dispatcher writes Memory + MemorySource rows.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import logging

from app.ingestion.types import ConnectorItem

log = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base for source connectors.

    Lifecycle:
        connector = MyConnector(source)
        await connector.validate_config()         # raises if config bad
        items = await connector.fetch_items()     # network/IO happens here
        # dispatcher turns each item into a Memory + MemorySource

    Cursor support (Phase 2.6):
        Connectors that paginate (Drive/Notion/Gmail) read
        ``self.initial_cursor`` at the start of ``fetch_items()`` and
        set ``self.last_cursor`` to the final pagination token (or
        ``None`` if exhausted). The dispatcher reads
        ``connector.last_cursor`` and saves it to
        ``Source.sync_cursor`` for the next sync.
    """

    # Concrete subclasses set this to a value from SOURCE_TYPES.
    source_type: str = ""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        initial_cursor: str | None = None,
    ) -> None:
        self.config: dict[str, Any] = dict(config or {})
        # Where to RESUME from (set by dispatcher from Source.sync_cursor).
        self.initial_cursor: str | None = initial_cursor
        # Where the NEXT sync should resume from (set by connector).
        self.last_cursor: str | None = None

    # ── To be overridden ──────────────────────────────────────────────────────

    @abstractmethod
    async def fetch_items(self) -> list[ConnectorItem]:
        """Pull items from the remote source. May do I/O."""
        raise NotImplementedError

    # ── Helpers (override if needed) ─────────────────────────────────────────

    def validate_config(self) -> None:
        """
        Check that the connector's `config` has what it needs.
        Default is a no-op; subclasses raise on bad config.
        """
        return None

    @property
    def display_name(self) -> str:
        return self.__class__.__name__
