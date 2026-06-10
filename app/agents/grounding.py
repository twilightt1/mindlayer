"""Per-answer grounding confidence (P3).

Turns the signals the pipeline already produces — whether the grader judged the
answer grounded, whether it cited sources, how many sources, how many
self-correction retries it took — into a single [0, 1] confidence score plus a
human label. This is the "trust" signal: it tells the user *how much* to trust
an answer, and it is also persisted in ``agent_trace.grounding`` so the quality
trend endpoint can aggregate it over time.

Pure function (no IO) so it is trivially unit-testable.
"""
from __future__ import annotations

from typing import Any, TypedDict

# Query types that are not grounded retrieval answers — confidence is N/A.
_NON_GROUNDED_TYPES = {"chitchat", "save_note"}


class GroundingConfidence(TypedDict):
    score: float          # 0.0 – 1.0
    label: str            # "high" | "medium" | "low" | "not_applicable"
    signals: dict[str, Any]


def _label(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def compute_grounding_confidence(state: dict[str, Any]) -> GroundingConfidence:
    """Compute a grounding-confidence score from the answer state.

    Heuristic, intentionally simple and explainable:

      - Start from the grader's grounded verdict (0.6 grounded / 0.15 not).
      - +0.25 if the answer cites at least one source.
      - up to +0.15 for having sources to ground in (scaled by count, cap 3).
      - −0.1 per self-correction retry (the pipeline struggled).

    For chitchat / save_note there is nothing to ground against, so the score
    is reported as not_applicable.
    """
    query_type = state.get("query_type", "rag")
    trace = state.get("agent_trace", {}) or {}

    if query_type in _NON_GROUNDED_TYPES:
        return GroundingConfidence(
            score=0.0,
            label="not_applicable",
            signals={"query_type": query_type},
        )

    citation = trace.get("citation", {}) or {}
    hallucination = trace.get("hallucination", {}) or {}

    grounded = bool(hallucination.get("grounded", True))
    has_citation = bool(citation.get("has_citation", False))
    source_count = int(citation.get("source_count", 0) or 0)
    retry_count = int(state.get("retry_count", 0) or 0)

    score = 0.6 if grounded else 0.15
    if has_citation:
        score += 0.25
    score += 0.15 * (min(source_count, 3) / 3.0)
    score -= 0.1 * retry_count

    score = round(max(0.0, min(1.0, score)), 4)

    return GroundingConfidence(
        score=score,
        label=_label(score),
        signals={
            "grounded": grounded,
            "has_citation": has_citation,
            "source_count": source_count,
            "retry_count": retry_count,
            "query_type": query_type,
        },
    )


__all__ = ["compute_grounding_confidence", "GroundingConfidence"]
