import pytest

from eval.metrics import (
    calculate_fallback_accuracy,
    calculate_keyword_coverage,
    calculate_source_hit,
    has_citation,
    is_fallback_answer,
    normalize_text,
    summarize_results,
)

pytestmark = pytest.mark.eval


def test_normalize_text_casefolds_and_collapses_whitespace():
    assert normalize_text("  API\nKey   Rotation ") == "api key rotation"


def test_calculate_source_hit_matches_expected_source_names():
    assert calculate_source_hit(["api_authentication_guide.md"], ["api_authentication_guide.md"]) == 1.0
    assert calculate_source_hit(["api_authentication_guide.md"], ["billing_and_plans_faq.md"]) == 0.0


def test_calculate_source_hit_returns_one_when_no_source_expected():
    assert calculate_source_hit([], []) == 1.0


def test_calculate_keyword_coverage_is_case_insensitive():
    text = "Enterprise customers can configure SAML or OIDC SSO."

    coverage = calculate_keyword_coverage(text, ["enterprise", "SAML", "missing"])

    assert coverage == pytest.approx(2 / 3)


def test_has_citation_detects_source_marker_or_sources():
    assert has_citation("Answer with [Source 1].") is True
    assert has_citation("Answer without marker.", ["manual.md"]) is True
    assert has_citation("Answer without marker.", []) is False


def test_fallback_detection_and_accuracy():
    fallback = "I don't know based on the available SupportMind documentation."
    normal = "Use Settings → Developer → API Keys. [Source 1]"

    assert is_fallback_answer(fallback) is True
    assert calculate_fallback_accuracy(True, fallback) == 1.0
    assert calculate_fallback_accuracy(False, normal) == 1.0
    assert calculate_fallback_accuracy(True, normal) == 0.0


def test_summarize_results_aggregates_metrics():
    results = [
        {
            "source_hit": 1.0,
            "keyword_coverage": 0.75,
            "has_citation": True,
            "fallback_accuracy": 1.0,
            "latency_ms": 10.0,
            "hallucination_flagged": False,
            "correction_count": 1,
            "passed": True,
        },
        {
            "source_hit": 0.0,
            "keyword_coverage": 0.25,
            "has_citation": False,
            "fallback_accuracy": 0.0,
            "latency_ms": 30.0,
            "hallucination_flagged": True,
            "correction_count": 0,
            "passed": False,
        },
    ]

    summary = summarize_results(results)

    assert summary["total_cases"] == 2
    assert summary["source_hit_rate"] == 0.5
    assert summary["keyword_coverage"] == 0.5
    assert summary["citation_rate"] == 0.5
    assert summary["fallback_accuracy"] == 0.5
    assert summary["avg_latency_ms"] == 20.0
    assert summary["hallucination_flag_rate"] == 0.5
    assert summary["correction_rate"] == 0.5
    assert summary["passed_cases"] == 1
    assert summary["failed_cases"] == 1
