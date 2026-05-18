"""
Shared types for the ingestion layer.

A `ConnectorItem` is the output of a single fetch from a connector:
one piece of knowledge, normalized. The dispatcher then converts it
to a `Memory` + `MemorySource` row pair.

A `SyncResult` is what the dispatcher returns to the API: counts
of what happened, with a per-item error log.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ConnectorItem(BaseModel):
    """One normalized item produced by a connector."""

    title:         str             = Field(min_length=1, max_length=500)
    content:       str             = Field(min_length=1)
    summary:       str | None      = None
    source_ref:    str | None      = Field(default=None, max_length=500)
    source_url:    str | None      = Field(default=None, max_length=1000)
    source_excerpt: str | None     = Field(default=None, max_length=2000)
    captured_at:   datetime        = Field(default_factory=datetime.utcnow)
    tags:          list[str]       = Field(default_factory=list, max_length=50)
    metadata:      dict[str, Any]  = Field(default_factory=dict)


class ItemError(BaseModel):
    """One failed item inside a sync run."""

    source_ref: str | None = None
    message:     str
    raised_at:   datetime  = Field(default_factory=datetime.utcnow)


class SyncResult(BaseModel):
    """What a single `Source.sync` call produced."""

    source_id:        str
    started_at:       datetime
    finished_at:      datetime
    items_yielded:    int            = 0
    memories_added:   int            = 0
    memories_updated: int            = 0
    memories_skipped: int            = 0
    errors:           list[ItemError] = Field(default_factory=list)
    notes:            list[str]      = Field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return not self.errors and (self.memories_added + self.memories_updated + self.memories_skipped) > 0
