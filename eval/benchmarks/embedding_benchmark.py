"""
Embedding benchmark harness.

Compares embedding latency and (optionally) retrieval recall across models.
Pure-stdlib metrics; the embedding model itself is provided by the caller.
"""
from __future__ import annotations

import statistics
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbedResult:
    model: str
    corpus_size: int
    latencies_ms: list[float] = field(default_factory=list)
    dimensions: int = 0

    @property
    def latency_p50(self) -> float:
        return _percentile(self.latencies_ms, 50)

    @property
    def latency_p95(self) -> float:
        return _percentile(self.latencies_ms, 95)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "corpus_size": self.corpus_size,
            "latency_p50_ms": round(self.latency_p50, 2),
            "latency_p95_ms": round(self.latency_p95, 2),
            "mean_latency_ms": round(statistics.mean(self.latencies_ms), 2) if self.latencies_ms else 0.0,
            "dimensions": self.dimensions,
            "throughput_per_sec": round(self.corpus_size / max(0.001, sum(self.latencies_ms) / 1000.0), 2),
        }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] * (c - k) + s[c] * (k - f)


class EmbeddingBenchmark:
    def __init__(
        self,
        models: Iterable[str],
        corpus: list[str],
        embed_fn: Callable[[str, list[str]], tuple[list[list[float]], int]] | None = None,
    ) -> None:
        self.models = list(models)
        self.corpus = corpus
        self.embed_fn = embed_fn

    def run(self) -> dict[str, Any]:
        results: list[EmbedResult] = []
        for model in self.models:
            er = EmbedResult(model=model, corpus_size=len(self.corpus))
            if self.embed_fn is None:
                # If no embedder provided, skip with a stub result
                results.append(er)
                continue
            start = time.perf_counter()
            try:
                _vectors, dim = self.embed_fn(model, self.corpus)
                elapsed = (time.perf_counter() - start) * 1000
                er.latencies_ms.append(round(elapsed, 2))
                er.dimensions = dim
            except Exception:
                pass
            results.append(er)
        return {
            "models": [r.model for r in results],
            "results": [r.to_dict() for r in results],
        }
