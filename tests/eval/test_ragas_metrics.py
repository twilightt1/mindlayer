"""Unit tests for RAGAS-style evaluation metrics."""
from __future__ import annotations

import pytest

from eval.ragas_metrics import (
    answer_correctness,
    answer_relevancy,
    answer_similarity,
    context_entity_recall,
    context_precision_at_k,
    context_recall_at_k,
    faithfulness_nli,
    faithfulness_simple,
    hallucination_token_rate,
    mean_reciprocal_rank,
    ndcg_at_k,
    ragas_evaluate,
    summarize_ragas,
)


# ---------------------------------------------------------------------------
# Context quality
# ---------------------------------------------------------------------------

class TestContextPrecision:
    def test_full_precision(self) -> None:
        # 1 expected, 1 retrieved, k=5 → 1/1
        score = context_precision_at_k(
            ["api_authentication_guide.md"],
            ["api_authentication_guide.md"],
            k=5,
        )
        assert score == 1.0

    def test_partial_precision(self) -> None:
        # 1 relevant among 2 retrieved, k=2 → 0.5
        score = context_precision_at_k(
            ["api_authentication_guide.md", "billing.md"],
            ["api_authentication_guide.md"],
            k=2,
        )
        assert score == 0.5

    def test_no_expected_is_perfect(self) -> None:
        assert context_precision_at_k(["a.md"], [], k=3) == 1.0

    def test_no_retrieved_is_zero(self) -> None:
        assert context_precision_at_k([], ["a.md"], k=3) == 0.0

    def test_k_caps_top(self) -> None:
        score = context_precision_at_k(
            ["a.md", "b.md", "c.md", "d.md", "e.md"],
            ["a.md"],
            k=3,
        )
        # Top 3 contains a.md → 1/3
        assert score == pytest.approx(1 / 3)


class TestContextRecall:
    def test_full_recall(self) -> None:
        score = context_recall_at_k(
            ["api_authentication_guide.md", "billing.md"],
            ["api_authentication_guide.md"],
            k=5,
        )
        assert score == 1.0

    def test_partial_recall(self) -> None:
        score = context_recall_at_k(
            ["unrelated.md"],
            ["api_authentication_guide.md", "billing.md"],
            k=5,
        )
        assert score == 0.0

    def test_no_expected_is_perfect(self) -> None:
        assert context_recall_at_k(["a.md"], [], k=3) == 1.0


class TestMRR:
    def test_first_relevant(self) -> None:
        assert mean_reciprocal_rank(["a.md", "b.md"], ["a.md"]) == 1.0

    def test_second_relevant(self) -> None:
        assert mean_reciprocal_rank(["x.md", "a.md"], ["a.md"]) == 0.5

    def test_no_relevant(self) -> None:
        assert mean_reciprocal_rank(["x.md", "y.md"], ["a.md"]) == 0.0


class TestNDCG:
    def test_perfect_ranking(self) -> None:
        assert ndcg_at_k(
            ["a.md", "b.md", "c.md"],
            ["a.md", "b.md"],
            k=3,
        ) == pytest.approx(1.0)

    def test_poor_ranking(self) -> None:
        score = ndcg_at_k(
            ["x.md", "y.md", "a.md"],
            ["a.md", "b.md"],
            k=3,
        )
        assert 0.0 < score < 1.0


class TestContextEntityRecall:
    def test_full_recall(self) -> None:
        ctx = "The API key rotation uses Settings and Developer panels"
        gt = "Settings Developer panels"
        assert context_entity_recall(ctx, gt) == 1.0

    def test_partial_recall(self) -> None:
        ctx = "The API key rotation uses Settings"
        gt = "Settings Developer panels"
        # Tokens in gt (>2 chars): settings, developer, panels
        # Found in ctx: settings only
        # 1 of 3 found → ~0.333
        score = context_entity_recall(ctx, gt)
        assert 0.0 < score < 1.0
        assert score == pytest.approx(1 / 3)

    def test_empty_gt_is_perfect(self) -> None:
        assert context_entity_recall("anything", "") == 1.0


# ---------------------------------------------------------------------------
# Answer quality
# ---------------------------------------------------------------------------

class TestAnswerRelevancy:
    def test_relevant_answer_scores_higher(self) -> None:
        relevant = answer_relevancy(
            "How do I rotate an API key?",
            "Go to Settings, then Developer, then rotate the API key.",
            embed_model=None,
        )
        irrelevant = answer_relevancy(
            "How do I rotate an API key?",
            "Pizza is delicious with extra cheese.",
            embed_model=None,
        )
        assert relevant > irrelevant

    def test_empty_returns_zero(self) -> None:
        assert answer_relevancy("", "answer", embed_model=None) == 0.0
        assert answer_relevancy("question", "", embed_model=None) == 0.0


class TestAnswerSimilarity:
    def test_high_similarity(self) -> None:
        a = "The warranty is 12 months from the date of purchase."
        b = "12 months of warranty starting from the purchase date."
        score = answer_similarity(a, b, embed_model=None)
        assert score > 0.3

    def test_low_similarity(self) -> None:
        a = "API key rotation instructions"
        b = "Pasta carbonara recipe"
        score = answer_similarity(a, b, embed_model=None)
        assert score < 0.1


class TestAnswerCorrectness:
    def test_perfect_match(self) -> None:
        gt = "12 months warranty from purchase date"
        ans = "12 months warranty from purchase date"
        assert answer_correctness(ans, gt, embed_model=None) == pytest.approx(1.0)

    def test_partial_credit(self) -> None:
        gt = "12 months warranty from purchase date"
        ans = "12 months warranty from some other date"
        score = answer_correctness(ans, gt, embed_model=None)
        assert 0.0 < score < 1.0

    def test_no_gt_is_perfect(self) -> None:
        assert answer_correctness("any answer", "", embed_model=None) == 1.0


# ---------------------------------------------------------------------------
# Faithfulness
# ---------------------------------------------------------------------------

class TestFaithfulnessSimple:
    def test_fully_grounded(self) -> None:
        ctx = "The API key can be rotated from Settings page"
        ans = "You can rotate the API key from the Settings page."
        assert faithfulness_simple(ans, ctx) == 1.0

    def test_partial_grounding(self) -> None:
        ctx = "The API key can be rotated from Settings page"
        # Second sentence is made up
        ans = "The API key can be rotated from the Settings page. Pizza is tasty."
        assert 0.0 < faithfulness_simple(ans, ctx) < 1.0

    def test_empty_answer_is_perfect(self) -> None:
        assert faithfulness_simple("", "some context") == 1.0

    def test_empty_context_is_zero(self) -> None:
        assert faithfulness_simple("some answer", "") == 0.0


class TestHallucinationTokenRate:
    def test_no_hallucination(self) -> None:
        ctx = "API key rotation happens in Settings Developer"
        ans = "API key rotation Settings Developer"
        assert hallucination_token_rate(ans, ctx) == 0.0

    def test_full_hallucination(self) -> None:
        ctx = ""
        ans = "pizza pasta carbonara delicious"
        # No context to ground anything → 1.0
        assert hallucination_token_rate(ans, ctx) == 1.0

    def test_partial_hallucination(self) -> None:
        ctx = "API key rotation happens in Settings"
        # Answer tokens >2 chars: api, key, rotation, settings, pizza, pasta
        # Ungrounded (not in ctx): pizza, pasta
        # 2 of 6 ungrounded → ~0.333
        ans = "API key rotation Settings pizza pasta"
        score = hallucination_token_rate(ans, ctx)
        assert score == pytest.approx(2 / 6)


class TestFaithfulnessNLI:
    def test_returns_none_when_no_model(self, monkeypatch) -> None:
        # Patch the lazy loader to return None
        import eval.ragas_metrics as mod

        monkeypatch.setattr(mod, "_get_nli", lambda *a, **kw: None)
        result = faithfulness_nli("any answer", "any context")
        assert result is None


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

class TestRagasEvaluate:
    def test_basic(self) -> None:
        metrics = ragas_evaluate(
            question="How to rotate an API key?",
            answer="Use Settings → Developer to rotate the API key.",
            context="Settings → Developer page contains rotate API key option.",
            retrieved_sources=["api_authentication_guide.md"],
            expected_sources=["api_authentication_guide.md"],
            k=5,
        )
        assert "context_precision@k" in metrics
        assert "context_recall@k" in metrics
        assert "mrr" in metrics
        assert "ndcg@k" in metrics
        assert "answer_relevancy" in metrics
        assert "faithfulness_simple" in metrics
        assert "hallucination_token_rate" in metrics
        assert metrics["context_precision@k"] == 1.0
        assert metrics["context_recall@k"] == 1.0
        assert metrics["mrr"] == 1.0

    def test_with_ground_truth_adds_more(self) -> None:
        metrics = ragas_evaluate(
            question="Q?",
            answer="A.",
            context="ctx",
            retrieved_sources=["a.md"],
            ground_truth_answer="A.",
            expected_sources=["a.md"],
        )
        assert "answer_similarity" in metrics
        assert "answer_correctness" in metrics
        assert "context_entity_recall" in metrics


class TestSummarizeRagas:
    def test_average(self) -> None:
        per_case = [
            {"a": 0.5, "b": 0.8},
            {"a": 0.7, "b": 0.6},
        ]
        out = summarize_ragas(per_case)
        assert out["a"] == pytest.approx(0.6)
        assert out["b"] == pytest.approx(0.7)

    def test_handles_missing_keys(self) -> None:
        per_case = [
            {"a": 0.5},
            {"a": 0.7, "b": 0.9},
        ]
        out = summarize_ragas(per_case)
        # 'a' is in both, 'b' only in one — summarize_ragas averages whatever's present
        assert "a" in out
        assert "b" in out
        assert out["a"] == pytest.approx(0.6)
        assert out["b"] == pytest.approx(0.9)

    def test_empty(self) -> None:
        assert summarize_ragas([]) == {}
