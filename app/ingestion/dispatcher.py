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
        graph_memory_ids: list[str] = []

        # 1. Pick the connector (Phase 2.6: pass initial_cursor for incremental sync)
        try:
            connector = get_connector_for_source(
                source.source_type, source.config or {},
                initial_cursor=source.sync_cursor,
            )
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

        # Phase 2.6: save the last pagination token so the next sync
        # resumes here instead of re-fetching everything.
        # Only update if the connector set one (None means exhausted
        # or not applicable — keep existing cursor in that case).
        if connector.last_cursor is not None:
            source.sync_cursor = connector.last_cursor

        # 4. Persist each item, deduping by (source_id, source_ref)
        for item in items:
            try:
                outcome, memory_id = await self._persist_item(source, item)
                if outcome == "added":
                    result.memories_added += 1
                    if memory_id:
                        graph_memory_ids.append(memory_id)
                elif outcome == "updated":
                    result.memories_updated += 1
                elif outcome == "skipped":
                    result.memories_skipped += 1
            except Exception as e:
                log.exception("Persist failed for item %r", item.source_ref)
                result.errors.append(ItemError(source_ref=item.source_ref, message=str(e)))

        finalized = await self._finalize(source, result)
        if graph_memory_ids and not any((err.message or "").startswith("Commit failed") for err in finalized.errors):
            for memory_id in graph_memory_ids:
                _safe_enqueue_graph_build(memory_id)
        return finalized

    # ── internals ────────────────────────────────────────────────────────────

    async def _persist_item(self, source: Source, item: ConnectorItem) -> tuple[str, str | None]:
        """
        Create or update a Memory + MemorySource pair for one item.
        Returns (outcome, memory_id), where outcome is 'added' | 'updated' | 'skipped'.
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
                return "skipped", str(memory.id)
            # Update
            memory.title = item.title
            memory.content = item.content
            memory.summary = item.summary
            memory.tags = item.tags
            memory.extra_metadata = {**(memory.extra_metadata or {}), **item.metadata}
            existing_link.item_excerpt = item.source_excerpt
            existing_link.item_url = item.source_url
            return "updated", str(memory.id)

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
        return "added", str(memory.id)

    async def _finalize(self, source: Source, result: SyncResult) -> SyncResult:
        """Update the Source row to reflect the sync result."""
        source.last_sync_at = result.finished_at
        source.memories_synced = (source.memories_synced or 0) + result.memories_added
        first_err = result.errors[0].message if result.errors else None
        source.sync_error = first_err
        if result.errors:
            source.status = "error"
            # Phase 2.6: also store last error inside the JSONB config
            # so the admin UI / future webhook can inspect it without
            # a separate column. Reassign (not in-place) so SQLAlchemy
            # always sees the change.
            source.config = {
                **(source.config or {}),
                "last_error":    first_err,
                "last_error_at": result.finished_at.isoformat(),
            }
        else:
            source.status = "connected"
            # Clear any previous error from config
            cfg = dict(source.config or {})
            cfg.pop("last_error", None)
            cfg.pop("last_error_at", None)
            source.config = cfg
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


def _safe_enqueue_graph_build(memory_id: str) -> None:
    """Best-effort enqueue for graph extraction after source sync commits."""
    try:
        from app.tasks.graph_tasks import build_memory_graph_task

        build_memory_graph_task.delay(memory_id)
    except Exception as e:  # noqa: BLE001
        log.warning(
            "Graph build enqueue failed for source memory %s: %s",
            memory_id, e,
            extra={"memory_id": memory_id},
        )
