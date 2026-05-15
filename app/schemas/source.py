"""Pydantic schemas for Source (connected accounts)."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


SOURCE_TYPES = (
    "manual",
    "file_upload",
    "google_drive",
    "notion",
    "gmail",
    "web_clipper",
    "rss",
    "calendar",
    "twitter",
    "other",
)

SOURCE_STATUS = (
    "connected",
    "syncing",
    "error",
    "paused",
    "disconnected",
)


class SourceCreate(BaseModel):
    source_type:  Literal["manual", "file_upload", "google_drive", "notion",
                           "gmail", "web_clipper", "rss", "calendar", "twitter", "other"] = "manual"
    display_name: str = Field(min_length=1, max_length=255)
    description:  str | None = Field(default=None, max_length=4000)
    config:       dict       = Field(default_factory=dict)


class SourceUpdate(BaseModel):
    display_name: str | None  = Field(default=None, min_length=1, max_length=255)
    description:  str | None  = Field(default=None, max_length=4000)
    config:       dict | None = None
    status:       Literal["connected", "syncing", "error", "paused", "disconnected"] | None = None


class SourceResponse(BaseModel):
    id:              UUID
    user_id:         UUID
    source_type:     str
    display_name:    str
    description:     str | None
    status:          str
    last_sync_at:    datetime | None
    sync_error:      str | None
    memories_synced: int
    created_at:      datetime
    updated_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class SourceListResponse(BaseModel):
    items:  list[SourceResponse]
    total:  int
    limit:  int
    offset: int


class SourceSyncResponse(BaseModel):
    source_id:    UUID
    memories_added: int
    memories_updated: int
    errors:         int
    finished_at:  datetime
