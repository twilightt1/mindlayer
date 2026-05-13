"""
LLM / embedding / reranker benchmark utilities for MindLayer.

This package contains reusable benchmark harnesses:

  - llm_benchmark.LLMBenchmark        latency + cost comparison across LLM models
  - embedding_benchmark.EmbeddingBenchmark   embedding latency / recall comparison
  - reranker_benchmark.RerankerBenchmark     reranker NDCG / MRR comparison
  - cost_estimator.estimate_query_cost     cost-per-query for a model
  - run_benchmark                         CLI orchestrator

All benchmarks write a JSON + Markdown report under `output_dir`.
"""
from app.observability.cost import calculate_cost, PRICING  # noqa: F401
from eval.benchmarks.cost_estimator import estimate_query_cost  # noqa: F401
