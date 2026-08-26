"""
Feedback Pipeline Agent for Orivory v2.0

Implements Pistis-RAG closed-loop learning:
- Collect user feedback on answers
- Update document relevance weights
- Track feedback patterns
- Trigger periodic retraining

Reference: Pistis-RAG framework
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

if TYPE_CHECKING:
    from app.agents.state import AgentState
    from app.models.feedback import Feedback

log = logging.getLogger(__name__)

# ─── Enums and Dataclasses ────────────────────────────────────────────────────

class FeedbackType(str, Enum):
    """Types of user feedback."""
    POSITIVE = "positive"  # User thumbs up / correct
    NEGATIVE = "negative"  # User thumbs down / incorrect
    CORRECTION = "correction"  # User provided correction
    CITATION = "citation"  # User pointed to specific citation
    IGNORED = "ignored"  # User didn't use this answer


@dataclass
class FeedbackRecord:
    """A single feedback record."""
    feedback_id: str
    user_id: str
    conversation_id: str
    message_id: str
    feedback_type: str
    query_hash: str
    doc_ids: list[str]
    content: str | None
    created_at: datetime


@dataclass
class DocumentWeight:
    """Updated document weight based on feedback."""
    doc_id: str
    original_weight: float
    new_weight: float
    feedback_count: int
    positive_ratio: float


@dataclass
class FeedbackStats:
    """Aggregated feedback statistics."""
    total_feedback: int
    positive_count: int
    negative_count: int
    correction_count: int
    positive_ratio: float
    top_docs: list[dict]  # doc_id, weight, feedback_count


# ─── Feedback Processing ───────────────────────────────────────────────────────

def hash_query(query: str) -> str:
    """Create a hash of the query for anonymization."""
    return hashlib.sha256(query.encode()).hexdigest()[:16]


async def process_feedback(
    db: AsyncSession,
    user_id: str,
    conversation_id: str,
    message_id: str,
    feedback_type: str,
    query: str,
    doc_ids: list[str],
    content: str | None = None,
) -> FeedbackRecord:
    """
    Process incoming user feedback.
    
    Args:
        db: Database session
        user_id: User ID
        conversation_id: Conversation ID
        message_id: Message ID
        feedback_type: Type of feedback
        query: Original query
        doc_ids: IDs of documents used in answer
        content: Optional user-provided text (for corrections)
    
    Returns:
        FeedbackRecord with processing details
    """
    # Create feedback record
    feedback = Feedback(
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        feedback_type=feedback_type,
        query_hash=hash_query(query),
        doc_ids=doc_ids,
        content=content,
        created_at=datetime.utcnow(),
    )
    
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    log.info(
        f"Feedback processed: {feedback_type.value} for user {user_id[:8]}, "
        f"{len(doc_ids)} docs"
    )
    
    return FeedbackRecord(
        feedback_id=str(feedback.id),
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        feedback_type=feedback_type,
        query_hash=feedback.query_hash,
        doc_ids=doc_ids,
        content=content,
        created_at=feedback.created_at,
    )


async def get_document_weights(
    db: AsyncSession,
    doc_ids: list[str],
) -> list[DocumentWeight]:
    """
    Get current weights for documents based on feedback history.
    
    Args:
        db: Database session
        doc_ids: Document IDs to get weights for
    
    Returns:
        List of DocumentWeight with calculated weights
    """
    # Query feedback for these documents
    stmt = select(Feedback).where(Feedback.doc_ids.overlap(doc_ids))
    result = await db.execute(stmt)
    feedbacks = result.scalars().all()
    
    # Calculate weights per document
    doc_stats: dict[str, dict] = {}
    for fb in feedbacks:
        for doc_id in fb.doc_ids:
            if doc_id not in doc_stats:
                doc_stats[doc_id] = {
                    "positive": 0,
                    "negative": 0,
                    "total": 0,
                }
            doc_stats[doc_id]["total"] += 1
            if fb.feedback_type == FeedbackType.POSITIVE.value:
                doc_stats[doc_id]["positive"] += 1
            elif fb.feedback_type == FeedbackType.NEGATIVE.value:
                doc_stats[doc_id]["negative"] += 1
    
    weights = []
    for doc_id in doc_ids:
        stats = doc_stats.get(doc_id, {"positive": 0, "negative": 0, "total": 0})
        total = stats["total"]
        positive = stats["positive"]
        
        # Calculate weight: base 1.0, +0.1 per positive, -0.1 per negative
        # Clamped between 0.5 and 2.0
        base_weight = 1.0
        positive_bonus = 0.1 * positive
        negative_penalty = 0.1 * stats["negative"]
        new_weight = max(0.5, min(2.0, base_weight + positive_bonus - negative_penalty))
        
        positive_ratio = positive / total if total > 0 else 0.5
        
        weights.append(DocumentWeight(
            doc_id=doc_id,
            original_weight=1.0,
            new_weight=new_weight,
            feedback_count=total,
            positive_ratio=positive_ratio,
        ))
    
    return weights


async def get_feedback_stats(
    db: AsyncSession,
    user_id: str | None = None,
    days: int = 30,
) -> FeedbackStats:
    """
    Get aggregated feedback statistics.
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        days: Number of days to look back
    
    Returns:
        FeedbackStats with aggregated data
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    stmt = select(Feedback).where(Feedback.created_at >= cutoff)
    if user_id:
        stmt = stmt.where(Feedback.user_id == user_id)
    
    result = await db.execute(stmt)
    feedbacks = result.scalars().all()
    
    total = len(feedbacks)
    positive = sum(1 for f in feedbacks if f.feedback_type == FeedbackType.POSITIVE.value)
    negative = sum(1 for f in feedbacks if f.feedback_type == FeedbackType.NEGATIVE.value)
    corrections = sum(1 for f in feedbacks if f.feedback_type == FeedbackType.CORRECTION.value)
    
    # Calculate top docs
    doc_scores: dict[str, dict] = {}
    for fb in feedbacks:
        weight = 1.0
        if fb.feedback_type == FeedbackType.POSITIVE.value:
            weight = 1.2
        elif fb.feedback_type == FeedbackType.NEGATIVE.value:
            weight = 0.8
        
        for doc_id in fb.doc_ids:
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"weight": 0, "count": 0}
            doc_scores[doc_id]["weight"] += weight
            doc_scores[doc_id]["count"] += 1
    
    top_docs = sorted(
        [{"doc_id": k, **v} for k, v in doc_scores.items()],
        key=lambda x: x["weight"],
        reverse=True,
    )[:10]
    
    return FeedbackStats(
        total_feedback=total,
        positive_count=positive,
        negative_count=negative,
        correction_count=corrections,
        positive_ratio=positive / total if total > 0 else 0.0,
        top_docs=top_docs,
    )


async def should_trigger_retraining(db: AsyncSession) -> tuple[bool, str]:
    """
    Check if feedback threshold is met for retraining.
    
    Args:
        db: Database session
    
    Returns:
        Tuple of (should_retrain, reason)
    """
    stats = await get_feedback_stats(db, days=7)
    
    # Check minimum feedback count
    if stats.total_feedback < settings.FEEDBACK_MIN_SAMPLES:
        return False, f"Only {stats.total_feedback} feedback, need {settings.FEEDBACK_MIN_SAMPLES}"
    
    # Check positive ratio (should be above threshold)
    if stats.positive_ratio < 0.6:
        return True, f"Low positive ratio: {stats.positive_ratio:.1%}"
    
    # Check if enough corrections
    if stats.correction_count >= settings.FEEDBACK_MIN_CORRECTIONS:
        return True, f"Found {stats.correction_count} corrections"
    
    return True, f"Feedback threshold met: {stats.total_feedback} samples"


# ─── Feedback Agent Node ───────────────────────────────────────────────────────

async def feedback_agent(state: AgentState) -> AgentState:
    """
    Feedback agent node for LangGraph workflow.
    
    Records feedback on the generated answer for future improvement.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state
    """
    state.setdefault("agent_trace", {})
    state.setdefault("feedback_trace", {})
    
    # This node is typically called after answer generation
    # to record any implicit feedback (user accepted/rejected answer)
    
    # The actual feedback recording happens via API endpoint
    # This node just ensures feedback infrastructure is ready
    
    state["feedback_trace"]["ready"] = True
    state["feedback_trace"]["timestamp"] = datetime.utcnow().isoformat()
    
    return state


# ─── Document Weight Adjuster ─────────────────────────────────────────────────

async def adjust_retrieval_scores(
    db: AsyncSession,
    chunks: list[dict],
) -> list[dict]:
    """
    Adjust retrieval scores based on feedback weights.
    
    Args:
        db: Database session
        chunks: Retrieved document chunks
    
    Returns:
        Chunks with adjusted scores
    """
    if not chunks:
        return chunks
    
    doc_ids = [c.get("id", c.get("chunk_id", f"chunk_{i}")) for i, c in enumerate(chunks)]
    
    weights = await get_document_weights(db, doc_ids)
    weight_map = {w.doc_id: w for w in weights}
    
    adjusted = []
    for chunk in chunks:
        doc_id = chunk.get("id", chunk.get("chunk_id", ""))
        weight_info = weight_map.get(doc_id)
        
        if weight_info:
            original_score = chunk.get("score", chunk.get("rerank_score", 1.0))
            adjusted_score = original_score * weight_info.new_weight
            
            chunk = {
                **chunk,
                "feedback_weight": weight_info.new_weight,
                "adjusted_score": adjusted_score,
                "feedback_count": weight_info.feedback_count,
            }
        
        adjusted.append(chunk)
    
    # Re-sort by adjusted score
    adjusted.sort(key=lambda x: x.get("adjusted_score", 0), reverse=True)
    
    return adjusted
