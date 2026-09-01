"""
Insight Cards Agent - Proactive Discovery Feature

Surfaces hidden connections and unexpected insights from user's documents.
"What I Didn't Know I Knew" - proactively finding insights the user forgot they made.

Components:
- Document connection analyzer
- Insight generator (LLM-powered)
- Insight card model
- Preference learning
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

# Shared client seam: tests patch <module>._get_client, which rebinds
# this module attribute and is picked up by all call sites below.
from app.agents.llm_client import get_llm_client as _get_client
from app.config import settings

log = logging.getLogger(__name__)

# ─── LLM Client ───────────────────────────────────────────────────────────────


# ─── Enums ───────────────────────────────────────────────────────────────────

class InsightType(Enum):
    """Types of insights that can be generated."""
    CONNECTION = "connection"           # Unexpected relationship between topics
    CONTRADICTION = "contradiction"    # Conflicting information across sources
    EVOLUTION = "evolution"            # How thinking evolved over time
    PATTERN = "pattern"              # Repeated pattern across documents
    GAP = "gap"                       # Missing information / underexplored area
    CONFIRMATION = "confirmation"     # Evidence supporting user's hypothesis
    SYNTHESIS = "synthesis"           # New insight from combining sources


class InsightSurpriseLevel(Enum):
    """How surprising the insight is to the user."""
    LOW = "low"      # User likely knows this
    MEDIUM = "medium" # User might find this interesting
    HIGH = "high"    # User probably forgot this


class InsightStatus(Enum):
    """Status of an insight card."""
    NEW = "new"              # Newly generated, not yet shown
    SHOWN = "shown"         # Displayed to user
    DISMISSED = "dismissed"  # User dismissed this insight
    SAVED = "saved"          # User saved this insight
    EXPIRED = "expired"      # No longer relevant


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class DocumentReference:
    """Reference to a document that supports an insight."""
    document_id: str
    chunk_id: str | None = None
    title: str = ""
    excerpt: str = ""
    relevance_score: float = 0.5


@dataclass
class InsightCard:
    """
    An insight card representing a discovered connection or pattern.

    This is the core data structure for "What I Didn't Know I Knew" feature.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Insight content
    title: str = ""                          # "You connected X and Y but may not remember"
    insight_type: InsightType = InsightType.CONNECTION
    summary: str = ""                       # Brief description
    detail: str = ""                        # Full explanation

    # Sources
    sources: list[DocumentReference] = field(default_factory=list)
    source_count: int = 1

    # Metadata
    surprise_level: InsightSurpriseLevel = InsightSurpriseLevel.MEDIUM
    confidence: float = 0.5                # 0.0 - 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    shown_at: datetime | None = None
    dismissed_at: datetime | None = None

    # User feedback
    status: InsightStatus = InsightStatus.NEW
    helpful: bool | None = None         # User feedback
    feedback_note: str | None = None

    # Learning
    shown_count: int = 0
    relevance_score: float = 0.5            # Learned from user behavior

    def to_summary(self) -> str:
        """Generate a brief summary for display."""
        type_emoji = {
            InsightType.CONNECTION: "🔗",
            InsightType.CONTRADICTION: "⚡",
            InsightType.EVOLUTION: "📈",
            InsightType.PATTERN: "🔄",
            InsightType.GAP: "❓",
            InsightType.CONFIRMATION: "✅",
            InsightType.SYNTHESIS: "💡",
        }
        emoji = type_emoji.get(self.insight_type, "💡")
        return f"{emoji} {self.title}"


@dataclass
class InsightGenerationRequest:
    """Request to generate insights from a set of documents."""
    user_id: str
    document_ids: list[str]
    focus_topics: list[str] = field(default_factory=list)  # Topics user cares about
    exclude_insights_older_than_days: int = 30


@dataclass
class InsightGenerationResult:
    """Result from insight generation."""
    insights: list[InsightCard]
    generation_time_ms: float
    documents_analyzed: int
    error: str | None = None


# ─── Prompts ─────────────────────────────────────────────────────────────────

INSIGHT_DISCOVERY_PROMPT = """You are an insight discovery agent for a research assistant.

Given the user's documents and recent queries, discover unexpected insights that
the user may have forgotten they made or never realized they had.

Document Analysis:
{documents}

Recent User Activity:
{activity}

Focus Topics (user is interested in these):
{focus_topics}

Generate insights that:
1. Connect seemingly unrelated concepts across documents
2. Identify contradictions or differing viewpoints
3. Show how the user's thinking evolved over time
4. Reveal patterns the user might have missed
5. Fill gaps in the user's knowledge based on their documents
6. Confirm hypotheses the user has been exploring

Respond with JSON:
{{
    "insights": [
        {{
            "title": "You mentioned Project X in 3 documents but never connected them to Y",
            "insight_type": "connection|contradiction|evolution|pattern|gap|confirmation|synthesis",
            "summary": "Brief 1-sentence description",
            "detail": "Full explanation of why this insight matters and what the user can learn",
            "source_count": 3,
            "surprise_level": "low|medium|high",
            "confidence": 0.85,
            "sources": [
                {{
                    "document_id": "doc-123",
                    "title": "Document Title",
                    "excerpt": "Relevant passage from document",
                    "relevance_score": 0.9
                }}
            ]
        }}
    ]
}}

Generate 3-8 diverse insights. Focus on high-value discoveries, not obvious facts."""


INSIGHT_REFRESH_PROMPT = """Analyze these existing insights and determine which are still relevant.

Existing Insights:
{existing_insights}

Recent User Activity:
{recent_activity}

New Documents Added:
{new_documents}

Respond with JSON:
{{
    "updates": [
        {{
            "insight_id": "existing-id",
            "action": "keep|boost|dismiss|expire",
            "new_insight_score": 0.75
        }}
    ]
}}"""


# ─── Helper Functions ──────────────────────────────────────────────────────────

async def generate_insights(
    documents: list[dict],
    recent_activity: list[str],
    focus_topics: list[str],
) -> list[dict]:
    """
    Generate insights from documents using LLM.

    Args:
        documents: List of document dicts with id, title, content, created_at
        recent_activity: Recent queries/activity
        focus_topics: Topics user is interested in

    Returns:
        List of insight dicts
    """
    import json

    client = _get_client()

    # Format documents for prompt
    doc_text = "\n\n".join([
        f"[{i+1}] {doc.get('title', 'Untitled')}\n"
        f"    Created: {doc.get('created_at', 'Unknown')}\n"
        f"    Content: {doc.get('content', '')[:500]}..."
        for i, doc in enumerate(documents[:10])  # Limit to 10 docs
    ])

    activity_text = "\n".join([f"- {a}" for a in recent_activity[-10:]]) or "No recent activity"
    focus_text = ", ".join(focus_topics) or "No specific focus topics"

    prompt = INSIGHT_DISCOVERY_PROMPT.format(
        documents=doc_text,
        activity=activity_text,
        focus_topics=focus_text,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return result.get("insights", [])

    except Exception as e:
        log.warning(f"Insight generation failed: {e}")
        return []


async def refresh_insights(
    existing_insights: list[dict],
    recent_activity: list[str],
    new_documents: list[dict],
) -> list[dict]:
    """
    Refresh existing insights based on new activity.

    Args:
        existing_insights: Current insights
        recent_activity: Recent user activity
        new_documents: Newly added documents

    Returns:
        List of update recommendations
    """
    import json

    client = _get_client()

    existing_text = "\n".join([
        f"- {ins.get('title', 'Unknown')}: {ins.get('summary', '')}"
        for ins in existing_insights[:10]
    ])

    activity_text = "\n".join([f"- {a}" for a in recent_activity[-5:]]) or "No recent activity"

    new_docs_text = "\n".join([
        f"- {doc.get('title', 'Untitled')}" for doc in new_documents
    ]) or "No new documents"

    prompt = INSIGHT_REFRESH_PROMPT.format(
        existing_insights=existing_text,
        recent_activity=activity_text,
        new_documents=new_docs_text,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return result.get("updates", [])

    except Exception as e:
        log.warning(f"Insight refresh failed: {e}")
        return []


def calculate_insight_relevance(
    insight: InsightCard,
    user_preferences: dict,
) -> float:
    """
    Calculate personalized relevance score based on user preferences.

    Args:
        insight: The insight to score
        user_preferences: Learned user preferences

    Returns:
        Relevance score 0.0 - 1.0
    """
    base_score = insight.relevance_score

    # Boost for user's focus topics
    topic_boost = 0.0
    if user_preferences.get("focus_topics"):
        insight_lower = insight.title.lower() + insight.summary.lower()
        for topic in user_preferences["focus_topics"]:
            if topic.lower() in insight_lower:
                topic_boost += 0.15

    # Boost for insight type preference
    type_preference = user_preferences.get("insight_types", {})
    type_boost = type_preference.get(insight.insight_type.value, 0.0) * 0.1

    # Boost for surprise level (medium surprises often most valuable)
    surprise_boost = 0.05 if insight.surprise_level == InsightSurpriseLevel.MEDIUM else 0.0

    # Penalize if already shown many times without saving
    shown_penalty = -0.1 if insight.shown_count > 3 and insight.status != InsightStatus.SAVED else 0.0

    # Combine scores
    final_score = base_score + topic_boost + type_boost + surprise_boost + shown_penalty

    return max(0.0, min(1.0, final_score))


# ─── Insight Card Generator ────────────────────────────────────────────────────

async def create_insight_card(
    insight_data: dict,
    user_id: str,
) -> InsightCard:
    """
    Create an InsightCard from LLM output.

    Args:
        insight_data: Dict from LLM insight generation
        user_id: User ID

    Returns:
        InsightCard instance
    """
    # Parse insight type
    type_str = insight_data.get("insight_type", "connection")
    try:
        insight_type = InsightType(type_str)
    except ValueError:
        insight_type = InsightType.CONNECTION

    # Parse surprise level
    surprise_str = insight_data.get("surprise_level", "medium")
    try:
        surprise_level = InsightSurpriseLevel(surprise_str)
    except ValueError:
        surprise_level = InsightSurpriseLevel.MEDIUM

    # Parse sources
    sources = []
    for src in insight_data.get("sources", []):
        sources.append(DocumentReference(
            document_id=src.get("document_id", ""),
            title=src.get("title", ""),
            excerpt=src.get("excerpt", ""),
            relevance_score=src.get("relevance_score", 0.5),
        ))

    return InsightCard(
        user_id=user_id,
        title=insight_data.get("title", "Interesting connection found"),
        insight_type=insight_type,
        summary=insight_data.get("summary", ""),
        detail=insight_data.get("detail", ""),
        sources=sources,
        source_count=insight_data.get("source_count", len(sources)),
        surprise_level=surprise_level,
        confidence=insight_data.get("confidence", 0.5),
        relevance_score=insight_data.get("confidence", 0.5),
    )


# ─── Preference Learning ────────────────────────────────────────────────────────

async def update_user_preferences(
    user_id: str,
    insight_feedback: list[dict],
) -> dict:
    """
    Update user preferences based on insight feedback.

    Args:
        user_id: User ID
        insight_feedback: List of feedback dicts with insight_id, helpful, type

    Returns:
        Updated user preferences
    """
    preferences = {
        "focus_topics": [],
        "insight_types": {},  # type -> score
        "last_updated": datetime.now(UTC).isoformat(),
    }

    # Count helpful/dismissed by type
    type_stats: dict[str, dict[str, int]] = {}

    for feedback in insight_feedback:
        insight_type = feedback.get("insight_type", "connection")
        is_helpful = feedback.get("helpful")

        if insight_type not in type_stats:
            type_stats[insight_type] = {"helpful": 0, "dismissed": 0}

        if is_helpful:
            type_stats[insight_type]["helpful"] += 1
        elif is_helpful is False:
            type_stats[insight_type]["dismissed"] += 1

    # Calculate preference scores
    for insight_type, stats in type_stats.items():
        total = stats["helpful"] + stats["dismissed"]
        if total > 0:
            # Score from -1 to 1, normalized to 0-1
            score = (stats["helpful"] - stats["dismissed"]) / total
            preferences["insight_types"][insight_type] = (score + 1) / 2

    return preferences


# ─── Batch Insight Generation ────────────────────────────────────────────────

async def generate_insight_batch(
    request: InsightGenerationRequest,
    documents: list[dict],
    recent_activity: list[str],
) -> InsightGenerationResult:
    """
    Generate a batch of insights for a user.

    This is the main entry point for insight generation.

    Args:
        request: Generation request parameters
        documents: User's documents
        recent_activity: Recent queries/activity

    Returns:
        InsightGenerationResult with generated insights
    """
    import time
    start_time = time.time()

    try:
        # Generate insights using LLM
        insight_data_list = await generate_insights(
            documents=documents,
            recent_activity=recent_activity,
            focus_topics=request.focus_topics,
        )

        # Convert to InsightCard objects
        insights = []
        for insight_data in insight_data_list:
            card = await create_insight_card(
                insight_data=insight_data,
                user_id=request.user_id,
            )
            insights.append(card)

        generation_time_ms = (time.time() - start_time) * 1000

        return InsightGenerationResult(
            insights=insights,
            generation_time_ms=generation_time_ms,
            documents_analyzed=len(documents),
        )

    except Exception as e:
        log.error(f"Insight batch generation failed: {e}")
        return InsightGenerationResult(
            insights=[],
            generation_time_ms=(time.time() - start_time) * 1000,
            documents_analyzed=0,
            error=str(e),
        )
