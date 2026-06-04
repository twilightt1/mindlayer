from __future__ import annotations
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id:             UUID
    user_id:        UUID
    title:          str
    document_count: int
    created_at:     datetime
    updated_at:     datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id:              UUID
    conversation_id: UUID
    filename:        str
    file_size:       int | None
    mime_type:       str | None
    status:          str
    chunk_count:     int
    error_msg:       str | None
    created_at:      datetime
    updated_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id:              UUID
    conversation_id: UUID
    role:            str
    content:         str
    agent_trace:     dict
    token_count:     int | None
    created_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationResponse):
    documents: list[DocumentResponse] = []
    messages:  list[MessageResponse]  = []


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    include_personal_context: bool = True
    include_graph_context: bool = True
    personal_memory_top_k: int = Field(default=5, ge=0, le=10)

    model_config = ConfigDict(str_strip_whitespace=True)
