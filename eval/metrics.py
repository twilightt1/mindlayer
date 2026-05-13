from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

FALLBACK_MARKERS = (
    "i don't know",
    "i do not know",
    "không tìm thấy",
    "không có thông tin",
    "outside the available support documentation",
    "not covered by the mindlayer knowledge base",
)

CITATION_PATTERNS = (
    re.compile(r"\[source\s*\d+\]", re.IGNORECASE),
    re.compile(r"\(source:\s*[^)]+\)", re.IGNORECASE),
    re.compile(r"source\s*:\s*\S+", re.IGNORECASE),
)


def normalize_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").casefold()).strip()


def calculate_source_hit(
    returned_sources: Iterable[str],
    expected_sources: Iterable[str],
) -> float:
    expected = {normalize_text(source) for source in expected_sources if source}
    if not expected:
        return 1.0

    returned = {normalize_text(source) for source in returned_sources if source}
    if not returned:
        return 0.0

    hits = sum(
        1
        for expected_source in expected
        if any(expected_source in source or source in expected_source for source in returned)
    )
    return hits / len(expected)


def calculate_keyword_coverage(text: str, expected_keywords: Iterable[str]) -> float:
    keywords = [keyword for keyword in expected_keywords if keyword]
    if not keywords:
        return 1.0

    normalized = normalize_text(text)
    hits = sum(1 for keyword in keywords if normalize_text(keyword) in normalized)
    return hits / len(keywords)


def has_citation(answer: str, sources: Iterable[str] | None = None) -> bool:
    if any(pattern.search(answer or "") for pattern in CITATION_PATTERNS):
        return True
    return bool(list(sources or []))


def is_fallback_answer(answer: str) -> bool:
    normalized = normalize_text(answer)
    return any(marker in normalized for marker in FALLBACK_MARKERS)


def calculate_fallback_accuracy(should_fallback: bool, answer: str) -> float:
    did_fallback = is_fallback_answer(answer)
    return 1.0 if did_fallback == should_fallback else 0.0


def _mean(items: list[float]) -> float:
    return sum(items) / len(items) if items else 0.0


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    if total == 0:
        return {
            "total_cases": 0,
            "source_hit_rate": 0.0,
            "keyword_coverage": 0.0,
            "citation_rate": 0.0,
            "fallback_accuracy": 0.0,
            "avg_latency_ms": 0.0,
            "hallucination_flag_rate": 0.0,
            "correction_rate": 0.0,
            "passed_cases": 0,
            "failed_cases": 0,
        }

    # Always-reported core metrics
    core: dict[str, Any] = {
        "total_cases": total,
        "source_hit_rate": _mean([result["source_hit"] for result in results]),
        "keyword_coverage": _mean([result["keyword_coverage"] for result in results]),
        "citation_rate": _mean([1.0 if result.get("has_citation") else 0.0 for result in results]),
        "fallback_accuracy": _mean([result["fallback_accuracy"] for result in results]),
        "avg_latency_ms": _mean([result["latency_ms"] for result in results]),
        "hallucination_flag_rate": _mean(
            [1.0 if result.get("hallucination_flagged") else 0.0 for result in results]
        ),
        "correction_rate": _mean(
            [1.0 if result.get("correction_count", 0) > 0 else 0.0 for result in results]
        ),
        "passed_cases": sum(1 for result in results if result.get("passed")),
        "failed_cases": sum(1 for result in results if not result.get("passed")),
    }

    # Optional RAGAS-style metrics — aggregate only those present in all results
    ragas_keys: set[str] = set().union(
        *(set(result.get("ragas", {}).keys()) for result in results)
    )
    ragas_summary: dict[str, float] = {}
    for key in sorted(ragas_keys):
        values = [
            result["ragas"][key]
            for result in results
            if "ragas" in result and key in result["ragas"]
        ]
        if values:
            ragas_summary[key] = _mean(values)
    if ragas_summary:
        core["ragas"] = ragas_summary
    return core

