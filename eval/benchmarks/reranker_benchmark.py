"""
Reranker benchmark harness.

Compares NDCG@k and MRR across rerankers. Caller supplies the rerank_fn
since rerankers vary (Jina API, Cohere, local models).
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from eval.ragas_metrics import mean_reciprocal_rank, ndcg_at_k


@dataclass
class RerankerResult:
    name: str
    ndcg_scores: list[float] = field(default_factory=list)
    mrr_scores: list[float] = field(default_factory=list)

    @property
    def mean_ndcg(self) -> float:
        return sum(self.ndcg_scores) / len(self.ndcg_scores) if self.ndcg_scores else 0.0

    @property
    def mean_mrr(self) -> float:
        return sum(self.mrr_scores) / len(self.mrr_scores) if self.mrr_scores else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "reranker": self.name,
            "queries_evaluated": len(self.ndcg_scores),
            "mean_ndcg_at_5": round(self.mean_ndcg, 4),
            "mean_mrr": round(self.mean_mrr, 4),
        }


class RerankerBenchmark:
    def __init__(
        self,
        rerankers: Iterable[tuple[str, Callable[[str, list[str]], list[str]]]],
        queries: Iterable[tuple[str, list[str], list[str]]],
        k: int = 5,
    ) -> None:
        """
        Args:
            rerankers: list of (name, fn). fn(query, candidates) -> reranked candidates.
            queries: list of (query, expected_sources, candidate_sources).
        """
        self.rerankers = list(rerankers)
        self.queries = list(queries)
        self.k = k

    def run(self) -> dict[str, Any]:
        results = []
        for name, fn in self.rerankers:
            rr = RerankerResult(name=name)
            for _query, expected, candidates in self.queries:
                try:
                    reranked = fn(_query, candidates)
                except Exception:
                    reranked = candidates  # fall back to original order
                rr.ndcg_scores.append(ndcg_at_k(reranked, expected, k=self.k))
                rr.mrr_scores.append(mean_reciprocal_rank(reranked, expected))
            results.append(rr.to_dict())
        return {"results": results}

    @staticmethod
    def to_markdown(report: dict[str, Any]) -> str:
        lines = [
            "# Reranker Benchmark Report",
            "",
            "| Reranker | Mean NDCG@5 | Mean MRR | Queries |",
            "|---|---:|---:|---:|",
        ]
        for r in report.get("results", []):
            lines.append(
                f"| {r['reranker']} | {r['mean_ndcg_at_5']:.3f} | "
                f"{r['mean_mrr']:.3f} | {r['queries_evaluated']} |"
            )
        return "\n".join(lines)
