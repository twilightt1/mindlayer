"""Tests for the benchmark suite."""
from __future__ import annotations

from eval.benchmarks.cost_estimator import (
    estimate_query_cost,
    list_known_models,
    rank_models_by_cost,
)
from eval.benchmarks.embedding_benchmark import EmbeddingBenchmark
from eval.benchmarks.llm_benchmark import BenchmarkPrompt, LLMBenchmark
from eval.benchmarks.reranker_benchmark import RerankerBenchmark


class TestCostEstimator:
    def test_estimate_default(self) -> None:
        est = estimate_query_cost("openai/gpt-4o-mini")
        assert "per_agent" in est
        assert est["total_cost_usd"] >= 0
        # Default has 5 agents
        assert len(est["per_agent"]) >= 4

    def test_estimate_custom_breakdown(self) -> None:
        est = estimate_query_cost(
            "openai/gpt-4o-mini",
            call_breakdown={"answer": 2, "router": 1},
        )
        assert est["per_agent"]["answer"]["calls"] == 2
        assert est["per_agent"]["router"]["calls"] == 1

    def test_estimate_unknown_model_zero(self) -> None:
        est = estimate_query_cost("unknown/missing")
        assert est["total_cost_usd"] == 0.0

    def test_rank_models(self) -> None:
        ranking = rank_models_by_cost(
            ["openai/gpt-4o-mini", "openai/gpt-4o"]
        )
        # gpt-4o-mini should be cheaper than gpt-4o
        assert ranking[0][0] == "openai/gpt-4o-mini"
        assert ranking[0][1] < ranking[1][1]

    def test_list_known_models(self) -> None:
        models = list_known_models()
        assert "openai/gpt-4o-mini" in models
        assert isinstance(models, list)


class TestLLMBenchmarkStub:
    """Test the LLMBenchmark with a fake invoke_fn (no API needed)."""

    def test_runs_with_stub(self) -> None:
        def stub(model: str, prompt: BenchmarkPrompt) -> tuple[str, dict[str, int]]:
            return ("ok", {"tokens_in": 100, "tokens_out": 50})

        bench = LLMBenchmark(
            models=["openai/gpt-4o-mini"],
            prompt=BenchmarkPrompt(system="x", user="y"),
            n_runs=3,
            invoke_fn=stub,
        )
        report = bench.run()
        assert len(report["results"]) == 1
        r = report["results"][0]
        assert r["successful"] == 3
        assert r["failed"] == 0
        assert r["latency_p50_ms"] >= 0
        assert r["total_cost_usd"] > 0
        md = LLMBenchmark.to_markdown(report)
        assert "Latency p50" in md

    def test_run_with_failure(self) -> None:
        def fail_stub(model: str, prompt: BenchmarkPrompt) -> tuple[str, dict[str, int]]:
            raise RuntimeError("API down")

        bench = LLMBenchmark(
            models=["openai/gpt-4o-mini"],
            prompt=BenchmarkPrompt(system="x", user="y"),
            n_runs=2,
            invoke_fn=fail_stub,
        )
        report = bench.run()
        r = report["results"][0]
        assert r["successful"] == 0
        assert r["failed"] == 2
        assert "API down" in str(r["error_samples"])


class TestEmbeddingBenchmark:
    def test_dry_run(self) -> None:
        bench = EmbeddingBenchmark(
            models=["m1", "m2"],
            corpus=["a", "b", "c"],
        )
        report = bench.run()
        assert len(report["results"]) == 2

    def test_with_stub_embedder(self) -> None:
        def stub(model: str, corpus: list[str]) -> tuple[list[list[float]], int]:
            # Return 384-dim zero vectors
            return [[0.0] * 384 for _ in corpus], 384

        bench = EmbeddingBenchmark(
            models=["fake-model"],
            corpus=["doc a", "doc b"],
            embed_fn=stub,
        )
        report = bench.run()
        r = report["results"][0]
        assert r["dimensions"] == 384
        assert r["corpus_size"] == 2


class TestRerankerBenchmark:
    def test_identity_beats_reverse(self) -> None:
        queries = [
            ("q1", ["doc_0.md"], ["doc_0.md", "doc_1.md", "doc_2.md", "doc_3.md", "doc_4.md"]),
            ("q2", ["doc_1.md"], ["doc_0.md", "doc_1.md", "doc_2.md", "doc_3.md", "doc_4.md"]),
        ]
        # Identity: doc_0 first, MRR=1
        # Reverse: doc_4 first, doc_0 last, MRR=1/k
        def identity(q, cs):
            return cs

        def reverse(q, cs):
            return list(reversed(cs))

        bench = RerankerBenchmark(
            rerankers=[("identity", identity), ("reverse", reverse)],
            queries=queries,
            k=5,
        )
        report = bench.run()
        id_score = next(r for r in report["results"] if r["reranker"] == "identity")
        rev_score = next(r for r in report["results"] if r["reranker"] == "reverse")
        assert id_score["mean_mrr"] > rev_score["mean_mrr"]
        md = RerankerBenchmark.to_markdown(report)
        assert "identity" in md
