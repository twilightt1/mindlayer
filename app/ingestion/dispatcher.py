"""
SourceSyncService — the dispatcher that turns connector output into Memory rows.

For one Source row:
    1. Pick the right connector from the registry.
    2. Validate config.
    3. Call `connector.fetch_items()`.
    4. For each item, check if a memory with the same
       `(source_id, source_ref)` already exists:
         - skip if it does (idempotent re-sync)
         - update if the upstream content changed
         - create otherwise
    5. Update Source's `last_sync_at`, `memories_synced`, and `status`.

Returns a `SyncResult` with counts and per-item errors.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.models.memory import Memory
from app.models.source import MemorySource
from app.ingestion.types import ConnectorItem, ItemError, SyncResult
from app.ingestion.connectors.registry import get_connector_for_source

log = logging.getLogger(__name__)


class SourceSyncService:
    """Coordinates one `Source.sync()` invocation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def sync(self, source: Source) -> SyncResult:
        started_at = datetime.utcnow()
        result = SyncResult(
            source_id=str(source.id),
            started_at=started_at,
            finished_at=started_at,  # updated at the end
        )

        # 1. Pick the connector
        try:
            connector = get_connector_for_source(source.source_type, source.config or {})
        except KeyError as e:
            result.errors.append(ItemError(message=str(e)))
            result.notes.append("No connector registered for this source_type.")
            return await self._finalize(source, result)

        # 2. Validate
        try:
            connector.validate_config()
        except ValueError as e:
            result.errors.append(ItemError(message=f"Config invalid: {e}"))
            result.notes.append("Source config is missing required fields.")
            return await self._finalize(source, result)

        # 3. Fetch
        try:
            items = await connector.fetch_items()
        except NotImplementedError as e:
            result.errors.append(ItemError(message=str(e) or "Connector not yet implemented."))
            result.notes.append("This connector is a stub in Phase 2 v0.")
            return await self._finalize(source, result)
        except Exception as e:
            log.exception("Connector fetch failed for source %s", source.id)
            result.errors.append(ItemError(message=f"Fetch failed: {e}"))
            return await self._finalize(source, result)

        result.items_yielded = len(items)

        # 4. Persist each item, deduping by (source_id, source_ref)
        for item in items:
            try:
                outcome = await self._persist_item(source, item)
                if outcome == "added":
                    result.memories_added += 1
                elif outcome == "updated":
                    result.memories_updated += 1
                elif outcome == "skipped":
                    result.memories_skipped += 1
            except Exception as e:
                log.exception("Persist failed for item %r", item.source_ref)
                result.errors.append(ItemError(source_ref=item.source_ref, message=str(e)))

        return await self._finalize(source, result)

    # ── internals ────────────────────────────────────────────────────────────

    async def _persist_item(self, source: Source, item: ConnectorItem) -> str:
        """
        Create or update a Memory + MemorySource pair for one item.
        Returns 'added' | 'updated' | 'skipped'.
        """
        # Find an existing memory linked to this (source, ref)
        existing_link = await self.db.scalar(
            select(MemorySource)
            .where(
                MemorySource.source_id == source.id,
                MemorySource.item_ref == item.source_ref,
            )
        )

        if existing_link and existing_link.memory:
            # Idempotency: same source_ref => skip unless content changed
            memory = existing_link.memory
            if (memory.title == item.title and
                memory.content == item.content and
                memory.summary == item.summary):
                return "skipped"
            # Update
            memory.title = item.title
            memory.content = item.content
            memory.summary = item.summary
            memory.tags = item.tags
            memory.extra_metadata = {**(memory.extra_metadata or {}), **item.metadata}
            existing_link.item_excerpt = item.source_excerpt
            existing_link.item_url = item.source_url
            return "updated"

        # Create new memory
        memory = Memory(
            user_id=source.user_id,
            title=item.title,
            content=item.content,
            summary=item.summary,
            source_type=_memory_source_type_for(source.source_type),
            source_ref=item.source_ref,
            source_url=item.source_url,
            tags=item.tags,
            captured_at=item.captured_at,
            extra_metadata=item.metadata,
        )
        self.db.add(memory)
        await db_flush(self.db)

        link = MemorySource(
            memory_id=memory.id,
            source_id=source.id,
            item_ref=item.source_ref,
            item_url=item.source_url,
            item_excerpt=item.source_excerpt,
        )
        self.db.add(link)
        return "added"

    async def _finalize(self, source: Source, result: SyncResult) -> SyncResult:
        """Update the Source row to reflect the sync result."""
        source.last_sync_at = result.finished_at
        source.memories_synced = (source.memories_synced or 0) + result.memories_added
        source.sync_error = result.errors[0].message if result.errors else None
        if result.errors:
            source.status = "error"
        else:
            source.status = "connected"
        result.finished_at = datetime.utcnow()
        try:
            await self.db.commit()
        except Exception as e:
            log.exception("Failed to commit sync result for source %s", source.id)
            await self.db.rollback()
            result.errors.append(ItemError(message=f"Commit failed: {e}"))
        return result


# ── helpers ────────────────────────────────────────────────────────────────

async def db_flush(db: AsyncSession) -> None:
    """Flush pending writes so we can read server-generated values (id, etc.)."""
    await db.flush()


def _memory_source_type_for(connector_source_type: str) -> str:
    """Map a Source.source_type to a Memory.source_type."""
    mapping = {
        "manual":      "manual_note",
        "file_upload": "file_upload",
        "web_clipper": "web_clipper",
        "google_drive": "google_drive",
        "notion":      "notion",
        "gmail":       "gmail",
    }
    return mapping.get(connector_source_type, "other")
