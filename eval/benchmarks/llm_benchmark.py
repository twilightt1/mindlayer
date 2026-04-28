"""
LLM benchmark harness: compare latency, cost, and quality across LLM models.

Runs a configurable prompt N times against each model and reports
p50 / p95 latency, tokens/sec, and cost per call.

Usage:
    from eval.benchmarks.llm_benchmark import LLMBenchmark, BenchmarkPrompt

    bench = LLMBenchmark(
        models=["openai/gpt-4o-mini", "openai/gpt-4o"],
        prompt=BenchmarkPrompt(system="...", user="..."),
        n_runs=5,
    )
    result = bench.run()
    print(result.to_markdown())
"""
from __future__ import annotations

import asyncio
import statistics
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.observability.cost import calculate_cost


@dataclass
class BenchmarkPrompt:
    system: str
    user: str
    max_tokens: int = 200


@dataclass
class ModelResult:
    model: str
    runs: int
    successful: int
    failed: int
    latencies_ms: list[float] = field(default_factory=list)
    tokens_in: list[int] = field(default_factory=list)
    tokens_out: list[int] = field(default_factory=list)
    costs_usd: list[float] = field(default_factory=list)
    error_samples: list[str] = field(default_factory=list)

    @property
    def latency_p50(self) -> float:
        return _percentile(self.latencies_ms, 50)

    @property
    def latency_p95(self) -> float:
        return _percentile(self.latencies_ms, 95)

    @property
    def total_cost_usd(self) -> float:
        return round(sum(self.costs_usd), 6)

    @property
    def mean_tokens_per_sec(self) -> float:
        out_tokens = sum(self.tokens_out)
        total_sec = sum(self.latencies_ms) / 1000.0
        if total_sec == 0:
            return 0.0
        return round(out_tokens / total_sec, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "runs": self.runs,
            "successful": self.successful,
            "failed": self.failed,
            "latency_p50_ms": round(self.latency_p50, 2),
            "latency_p95_ms": round(self.latency_p95, 2),
            "mean_tokens_per_sec": self.mean_tokens_per_sec,
            "mean_tokens_in": int(statistics.mean(self.tokens_in)) if self.tokens_in else 0,
            "mean_tokens_out": int(statistics.mean(self.tokens_out)) if self.tokens_out else 0,
            "total_cost_usd": self.total_cost_usd,
            "cost_per_call_usd": round(self.total_cost_usd / max(1, self.successful), 6),
            "error_samples": self.error_samples[:3],
        }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(sorted_v) - 1)
    if f == c:
        return sorted_v[f]
    return sorted_v[f] * (c - k) + sorted_v[c] * (k - f)


class LLMBenchmark:
    """Stateless harness — caller passes an `invoke_fn(model, prompt) -> (text, usage)`."""

    def __init__(
        self,
        models: Iterable[str],
        prompt: BenchmarkPrompt,
        n_runs: int = 5,
        invoke_fn: Any | None = None,
    ) -> None:
        self.models = list(models)
        self.prompt = prompt
        self.n_runs = n_runs
        # Default: use the OpenAI client through the app's existing config
        self.invoke_fn = invoke_fn or self._default_invoke

    def _default_invoke(self, model: str, prompt: BenchmarkPrompt) -> tuple[str, dict[str, int]]:
        from openai import AsyncOpenAI

        from app.config import settings

        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )

        async def call_once() -> tuple[str, dict[str, int]]:
            resp = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt.system},
                    {"role": "user", "content": prompt.user},
                ],
                max_tokens=prompt.max_tokens,
                temperature=0.0,
            )
            text = resp.choices[0].message.content or ""
            usage = {
                "tokens_in": getattr(resp.usage, "prompt_tokens", 0) or 0,
                "tokens_out": getattr(resp.usage, "completion_tokens", 0) or 0,
            }
            return text, usage

        return asyncio.run(call_once())

    def run(self) -> dict[str, Any]:
        results: list[ModelResult] = []
        for model in self.models:
            mr = ModelResult(model=model, runs=self.n_runs, successful=0, failed=0)
            for _ in range(self.n_runs):
                start = time.perf_counter()
                try:
                    _text, usage = self.invoke_fn(model, self.prompt)
                    elapsed = (time.perf_counter() - start) * 1000
                    t_in = int(usage.get("tokens_in", 0))
                    t_out = int(usage.get("tokens_out", 0))
                    cost = calculate_cost(model, t_in, t_out)
                    mr.latencies_ms.append(round(elapsed, 2))
                    mr.tokens_in.append(t_in)
                    mr.tokens_out.append(t_out)
                    mr.costs_usd.append(cost)
                    mr.successful += 1
                except Exception as e:  # pragma: no cover - network failure path
                    mr.failed += 1
                    if len(mr.error_samples) < 3:
                        mr.error_samples.append(str(e))
            results.append(mr)
        return {
            "models": [r.model for r in results],
            "results": [r.to_dict() for r in results],
        }

    @staticmethod
    def to_markdown(report: dict[str, Any]) -> str:
        lines = [
            "# LLM Benchmark Report",
            "",
            "| Model | Latency p50 | Latency p95 | Tokens/sec | Tokens in | Tokens out | Cost/call | Total cost |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in report.get("results", []):
            lines.append(
                f"| {r['model']} | "
                f"{r['latency_p50_ms']:.1f} ms | "
                f"{r['latency_p95_ms']:.1f} ms | "
                f"{r['mean_tokens_per_sec']:.1f} | "
                f"{r['mean_tokens_in']} | "
                f"{r['mean_tokens_out']} | "
                f"${r['cost_per_call_usd']:.6f} | "
                f"${r['total_cost_usd']:.6f} |"
            )
        return "\n".join(lines)
