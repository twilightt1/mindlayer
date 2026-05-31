"""
Chat router — conversations, messages, documents (nested), SSE streaming.
All document operations are scoped to the parent conversation.
"""
from __future__ import annotations
import asyncio
import logging
from contextlib import suppress
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.dependencies import get_current_active_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationDetail, DocumentResponse, MessageResponse, ChatRequest,
)
from app.services import document_service
from app.services.quota_service import check_and_increment
from app.agents.state import AgentState
from app.middleware.rate_limiter import check_rate_limit
from app.config import settings
from app.api.v1.sse import format_sse

router = APIRouter(prefix="/chat", tags=["chat"])
log    = logging.getLogger(__name__)


def _source_event_payload(chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = chunk.get("metadata") or {}
    return {
        "content": chunk.get("content", "")[:200],
        "filename": metadata.get("filename", ""),
        "score": round(chunk.get("rerank_score", chunk.get("score", 0)), 4),
        "source_type": metadata.get("source_type"),
        "memory_id": metadata.get("memory_id"),
        "entity_names": metadata.get("entity_names"),
    }


                                                                                
async def _get_conversation(
    conversation_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    conv = await db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    if not conv:
        raise HTTPException(404, detail="Conversation not found.")
    return conv


                                                                                
@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    conv = Conversation(user_id=current_user.id, title=body.title, document_count=0)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    docs = await document_service.list_documents(db, conversation.id)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return ConversationDetail(
        **ConversationResponse.model_validate(conversation).model_dump(),
        documents=[DocumentResponse.model_validate(d) for d in docs],
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    body: ConversationUpdate,
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    conversation.title = body.title
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    from app.retrieval.vector_retriever import delete_conversation_collection
    from app.retrieval.bm25_retriever import bm25_retriever

    conv_id = str(conversation.id)
    await db.delete(conversation)
    await db.commit()
    await delete_conversation_collection(conv_id)
    bm25_retriever.invalidate(conv_id)


                                                                                
@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def list_messages(
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()


                                                                                
@router.post("/conversations/{conversation_id}/message")
async def send_message(
    body: ChatRequest,
    conversation: Conversation = Depends(_get_conversation),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
                        
    await check_rate_limit(str(current_user.id), window_seconds=60, limit=settings.RATE_LIMIT_PER_MINUTE)
    await check_and_increment(current_user.id, db)

    state = AgentState(
        user_id=str(current_user.id),
        conversation_id=str(conversation.id),
        query=body.query,
        query_type="",
        history=[],
        bm25_results=[],
        vector_results=[],
        fused_chunks=[],
        reranked_chunks=[],
        response="",
        token_count=0,
        agent_trace={},
        error=None,
        should_stream=True,
        has_documents=conversation.document_count > 0,
        document_count=conversation.document_count,
        personal_memory_enabled=body.include_personal_context,
        graph_context_enabled=body.include_graph_context,
        personal_memory_top_k=body.personal_memory_top_k,
        doc_context_chunks=[],
        personal_memory_chunks=[],
        graph_context_chunks=[],
        grounding_context_chunks=[],
    )

    async def event_stream():
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        final_state: dict[str, Any] = {}
        final_response_emitted = False

        async def emit(data: dict[str, Any], event: str | None = None) -> None:
            await queue.put({"event": event, "data": data})

        async def stream_token(delta: str) -> None:
            return

        state["_stream_callback"] = stream_token

        async def run_graph() -> None:
            nonlocal final_response_emitted
            try:
                from app.agents.graph import rag_graph

                await emit({"type": "status", "stage": "started"}, event="status")
                async for event in rag_graph.astream(state):
                    node, data = next(iter(event.items()))
                    if isinstance(data, dict):
                        final_state.update(data)

                    retry_count = final_state.get("retry_count", 0)
                    is_retry_stage = node.startswith("retry_") or node.startswith("record_")
                    await emit(
                        {
                            "type": "status",
                            "stage": node,
                            "retry_count": retry_count,
                            "attempt": retry_count + 1,
                            "category": "retry" if is_retry_stage else "progress",
                        },
                        event="status",
                    )

                    if node == "save":
                        response = final_state.get("response", "")
                        if response and not final_response_emitted:
                            final_response_emitted = True
                            await emit(
                                {
                                    "type": "token",
                                    "content": response,
                                    "retry_count": final_state.get("retry_count", 0),
                                    "mode": "final_evaluated_response",
                                },
                                event="token",
                            )

                        sources = [
                            _source_event_payload(c)
                            for c in final_state.get("reranked_chunks", [])
                        ]
                        await emit({"type": "sources", "sources": sources}, event="sources")
                        await emit(
                            {
                                "type": "trace",
                                "agent_trace": final_state.get("agent_trace", {}),
                            },
                            event="trace",
                        )
                        await emit(
                            {
                                "type": "done",
                                "sources": sources,
                                "token_count": final_state.get("token_count", 0),
                                "retry_count": final_state.get("retry_count", 0),
                            },
                            event="done",
                        )
                if "response" not in final_state:
                    await emit({"type": "done", "sources": []}, event="done")
            except Exception as e:
                log.error("Stream error", extra={"error": str(e)})
                await emit(
                    {"type": "error", "message": "An error occurred."},
                    event="error",
                )
            finally:
                await queue.put(None)

        graph_task = asyncio.create_task(run_graph())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield format_sse(item["data"], event=item.get("event"))
        finally:
            if not graph_task.done():
                graph_task.cancel()
                with suppress(asyncio.CancelledError):
                    await graph_task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


                                                                                
@router.get(
    "/conversations/{conversation_id}/documents",
    response_model=list[DocumentResponse],
)
async def list_documents(
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.list_documents(db, conversation.id)


@router.post(
    "/conversations/{conversation_id}/documents",
    response_model=DocumentResponse,
    status_code=202,
)
async def upload_document(
    file: UploadFile = File(...),
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.upload_document(db, conversation, file)


@router.get(
    "/conversations/{conversation_id}/documents/{document_id}",
    response_model=DocumentResponse,
)
async def get_document_status(
    document_id: UUID,
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.get_document(db, document_id, conversation.id)


@router.delete(
    "/conversations/{conversation_id}/documents/{document_id}",
    status_code=204,
)
async def delete_document(
    document_id: UUID,
    conversation: Conversation = Depends(_get_conversation),
    db: AsyncSession = Depends(get_db),
):
    doc = await document_service.get_document(db, document_id, conversation.id)
    await document_service.delete_document(db, doc, conversation)
