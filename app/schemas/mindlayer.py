"""Pydantic schemas for MindLayer Memory, Entity, Relation, Source."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


# ─── Memory ─────────────────────────────────────────────────────────────────

class MemoryCreate(BaseModel):
    title:         str | None        = Field(default=None, max_length=500)
    content:       str               = Field(min_length=1, max_length=100_000)
    summary:       str | None        = Field(default=None, max_length=4000)
    source_type:   Literal["manual_note", "file_upload", "google_drive", "notion",
                            "gmail", "web_clipper", "conversation_excerpt", "other"] = "manual_note"
    source_ref:    str | None        = Field(default=None, max_length=500)
    source_url:    str | None        = Field(default=None, max_length=1000)
    tags:          list[str]         = Field(default_factory=list, max_length=50)
    captured_at:   datetime | None   = None
    parent_id:     UUID | None       = None
    pinned:        bool              = False
    metadata:      dict              = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    title:         str | None        = Field(default=None, max_length=500)
    summary:       str | None        = Field(default=None, max_length=4000)
    tags:          list[str] | None  = Field(default=None, max_length=50)
    salience:      float | None      = Field(default=None, ge=0.0, le=1.0)
    pinned:        bool | None       = None
    metadata:      dict | None       = None


class MemoryEntityLink(BaseModel):
    id:        UUID
    entity_id: UUID
    salience:  float
    model_config = ConfigDict(from_attributes=True)


class MemoryResponse(BaseModel):
    id:          UUID
    user_id:     UUID
    parent_id:   UUID | None
    source_type: str
    source_ref:  str | None
    source_url:  str | None
    title:       str | None
    content:     str
    summary:     str | None
    tags:        list[str]
    salience:    float
    pinned:      bool
    captured_at: datetime
    indexed_at:  datetime
    updated_at:  datetime
    metadata:    dict

    model_config = ConfigDict(from_attributes=True)


class MemoryListResponse(BaseModel):
    items:  list[MemoryResponse]
    total:  int
    limit:  int
    offset: int


# ─── Entity ─────────────────────────────────────────────────────────────────

class EntityResponse(BaseModel):
    id:            UUID
    name:          str
    entity_type:   str
    aliases:       list[str]
    description:   str | None
    first_seen_at: datetime
    last_seen_at:  datetime
    mention_count: int
    metadata:      dict
    created_at:    datetime
    updated_at:    datetime

    model_config = ConfigDict(from_attributes=True)


class EntityListResponse(BaseModel):
    items:  list[EntityResponse]
    total:  int
    limit:  int
    offset: int


# ─── Relation ───────────────────────────────────────────────────────────────

class RelationResponse(BaseModel):
    id:                UUID
    user_id:           UUID
    source_entity_id:  UUID
    target_entity_id:  UUID
    relation:          str
    weight:            float
    evidence_count:    int
    last_evidence_at:  datetime
    metadata:          dict
    created_at:        datetime
    updated_at:        datetime

    model_config = ConfigDict(from_attributes=True)


class GraphEdge(BaseModel):
    source: str           # entity name
    target: str           # entity name
    relation: str
    weight: float


class GraphNode(BaseModel):
    id:   str             # entity name
    type: str
    mentions: int


class GraphSnapshot(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    generated_at: datetime
