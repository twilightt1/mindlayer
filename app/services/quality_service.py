"""Quality trend aggregation (P3).

Every assistant message persists an ``agent_trace`` JSON blob with the
pipeline's self-reported quality signals (citation presence, the grader's
grounded verdict, self-correction retries, grounding confidence, latency).
This service reduces those blobs over a time window into rates a reviewer can
watch — turning the per-request observability that already exists into a
trend, without any new data collection.

Pure-ish: one read query, then in-Python reduction that tolerates missing or
malformed trace keys (older messages predate some signals).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def aggregate_traces(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce a list of agent_trace dicts into quality metrics.

    Rates are computed only over the messages where the signal is meaningful
    (e.g. citation-rate over answers that actually retrieved sources), so a
    flood of chitchat doesn't dilute the numbers. Each rate reports its own
    denominator for honesty.
    """
    total = len(traces)

    grounded_yes = grounded_total = 0
    cited_yes = cited_total = 0
    retried_yes = 0
    confidence_sum = 0.0
    confidence_n = 0
    latency_sum = 0.0
    latency_n = 0

    for trace in traces:
        trace = _as_dict(trace)

        citation = _as_dict(trace.get("citation"))
        # Only count answers where grounding was expected (sources present).
        if citation.get("required") or citation.get("source_count"):
            cited_total += 1
            if citation.get("has_citation"):
                cited_yes += 1

        hallucination = _as_dict(trace.get("hallucination"))
        if "grounded" in hallucination:
            grounded_total += 1
            if hallucination.get("grounded"):
                grounded_yes += 1

        # Self-correction: any retry recorded for this turn.
        corrections = trace.get("correction")
        if isinstance(corrections, list) and corrections:
            retried_yes += 1

        grounding = _as_dict(trace.get("grounding"))
        if grounding.get("label") not in (None, "not_applicable") and "score" in grounding:
            confidence_sum += float(grounding.get("score") or 0.0)
            confidence_n += 1

        answer = _as_dict(trace.get("answer"))
        latency = answer.get("latency_ms")
        if isinstance(latency, (int, float)):
            latency_sum += float(latency)
            latency_n += 1

    def _rate(num: int, den: int) -> float:
        return round(num / den, 4) if den else 0.0

    return {
        "sample_size": total,
        "citation_rate": _rate(cited_yes, cited_total),
        "citation_sample": cited_total,
        "grounded_rate": _rate(grounded_yes, grounded_total),
        "grounded_sample": grounded_total,
        "hallucination_flag_rate": round(1.0 - _rate(grounded_yes, grounded_total), 4) if grounded_total else 0.0,
        "self_correction_rate": _rate(retried_yes, total),
        "avg_grounding_confidence": round(confidence_sum / confidence_n, 4) if confidence_n else 0.0,
        "grounding_confidence_sample": confidence_n,
        "avg_answer_latency_ms": round(latency_sum / latency_n, 2) if latency_n else 0.0,
        "latency_sample": latency_n,
    }


async def build_quality_trend(
    db: AsyncSession,
    *,
    hours: int = 24,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Aggregate assistant-message quality signals over the last ``hours``."""
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    rows = (
        await db.execute(
            select(Message.agent_trace)
            .where(
                Message.role == "assistant",
                Message.created_at >= since,
            )
        )
    ).scalars().all()

    metrics = aggregate_traces([_as_dict(r) for r in rows])
    metrics["window_hours"] = hours
    metrics["generated_at"] = now.isoformat()
    return metrics


__all__ = ["build_quality_trend", "aggregate_traces"]
