"""
CLI orchestrator for MindLayer benchmark suite.

Examples:
  # Compare 3 LLM models (requires OPENROUTER_API_KEY)
  python eval/benchmarks/run_benchmark.py --mode llm --models gpt-4o-mini,gpt-4o --n-runs 3

  # Show cost estimates for all known models
  python eval/benchmarks/run_benchmark.py --mode cost

  # Run a synthetic embedding benchmark (no model needed)
  python eval/benchmarks/run_benchmark.py --mode embedding --dry-run

  # Run a synthetic reranker benchmark
  python eval/benchmarks/run_benchmark.py --mode reranker --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from eval.benchmarks.cost_estimator import (  # noqa: E402
    estimate_query_cost,
    list_known_models,
    rank_models_by_cost,
)
from eval.benchmarks.embedding_benchmark import EmbeddingBenchmark  # noqa: E402
from eval.benchmarks.llm_benchmark import BenchmarkPrompt, LLMBenchmark  # noqa: E402
from eval.benchmarks.reranker_benchmark import RerankerBenchmark  # noqa: E402

DEFAULT_OUTPUT = ROOT / "eval" / "benchmark_results"


def parse_models(raw: str | None) -> list[str]:
    if not raw:
        return ["openai/gpt-4o-mini"]
    return [m.strip() for m in raw.split(",") if m.strip()]


def cmd_llm(args: argparse.Namespace) -> int:
    models = parse_models(args.models)
    prompt = BenchmarkPrompt(
        system="You are a helpful assistant.",
        user=args.prompt or "Explain retrieval-augmented generation in 2 sentences.",
        max_tokens=args.max_tokens,
    )
    bench = LLMBenchmark(models=models, prompt=prompt, n_runs=args.n_runs)
    if args.dry_run:
        print(f"[DRY-RUN] Would benchmark {len(models)} models x {args.n_runs} runs")
        return 0
    report = bench.run()
    return _write_report(args, report, bench.to_markdown(report))


def cmd_cost(args: argparse.Namespace) -> int:
    models = list_known_models() if not args.models else parse_models(args.models)
    ranking = rank_models_by_cost(models)
    rows = []
    for model, cost in ranking:
        est = estimate_query_cost(model)
        rows.append({
            "model": model,
            "estimated_cost_per_query_usd": cost,
            "breakdown": est["per_agent"],
        })
    report = {"models_compared": len(ranking), "ranking": rows}
    md_lines = [
        "# LLM Cost Estimate",
        "",
        "Sorted by estimated cost per query (ascending).",
        "",
        "| Model | Est. cost/query |",
        "|---|---:|",
    ]
    for r in rows:
        md_lines.append(f"| {r['model']} | ${r['estimated_cost_per_query_usd']:.6f} |")
    return _write_report(args, report, "\n".join(md_lines))


def cmd_embedding(args: argparse.Namespace) -> int:
    models = parse_models(args.models)
    # Synthetic corpus
    corpus = [f"document {i} about topic {i % 10}" for i in range(args.corpus_size)]
    bench = EmbeddingBenchmark(models=models, corpus=corpus)
    report = bench.run()
    if args.dry_run:
        print(f"[DRY-RUN] Would benchmark {len(models)} embedding models on {len(corpus)} docs")
        return 0
    md = "# Embedding Benchmark (dry-run / no embedder)\n\n"
    md += "No embedder configured — install sentence-transformers and pass --embed-fn to enable.\n"
    return _write_report(args, report, md)


def cmd_reranker(args: argparse.Namespace) -> int:
    models = parse_models(args.models)
    # Synthetic queries
    queries = [
        (f"query {i}", [f"doc_{i}.md"], [f"doc_{j}.md" for j in range(5)])
        for i in range(args.n_queries)
    ]
    # Synthetic rerankers: identity and reverse. Model is not used for the
    # synthetic passes — pass a real rerank_fn in production.
    rerankers = [
        ("identity", lambda q, cs: cs),
        ("reverse", lambda q, cs: list(reversed(cs))),
    ]
    bench = RerankerBenchmark(rerankers=rerankers, queries=queries, k=5)
    report = bench.run()
    if args.dry_run:
        print(f"[DRY-RUN] Would run {len(rerankers)} reranker strategies on {len(queries)} queries")
        return 0
    return _write_report(args, report, bench.to_markdown(report))


def _write_report(args: argparse.Namespace, report: dict, md: str) -> int:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = args.name or args.mode
    (out_dir / f"{out_name}.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    (out_dir / f"{out_name}.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"\nReport written: {out_dir / out_name}.{{json,md}}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MindLayer benchmark suite.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["llm", "cost", "embedding", "reranker"],
    )
    parser.add_argument("--models", help="Comma-separated list of model identifiers.")
    parser.add_argument("--n-runs", type=int, default=3)
    parser.add_argument("--n-queries", type=int, default=10)
    parser.add_argument("--corpus-size", type=int, default=100)
    parser.add_argument("--max-tokens", type=int, default=120)
    parser.add_argument("--prompt", help="Custom user prompt for LLM benchmark.")
    parser.add_argument("--name", help="Output file name (default: mode)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return {
        "llm": cmd_llm,
        "cost": cmd_cost,
        "embedding": cmd_embedding,
        "reranker": cmd_reranker,
    }[args.mode](args)


if __name__ == "__main__":
    raise SystemExit(main())
