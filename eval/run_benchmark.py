"""Benchmark runner CLI: phased execution, honest about what is not wired yet.

Phases: ``plan`` (default) prints the instance count and the phase list and
exits 0 — no results are written. ``ingest``/``query`` require live-stack
wiring (a pinned follow-up) and exit with a clear message instead of
fabricating anything. ``score`` aggregates an existing per-question results
JSON — the one phase that needs no live stack — and never invents scores.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from eval.benchmarks.longmemeval_s import load_instances as load_longmemeval
from eval.benchmarks.memoryagentbench import load_instances as load_mab
from eval.benchmarks.runner import (
    PHASES,
    RunnerConfig,
    record_sha256,
    run_score,
    write_results,
)

BENCHMARK_LOADERS = {
    "longmemeval_s": load_longmemeval,
    "memoryagentbench": load_mab,
}

_LIVE_WIRING = (
    "live wiring is a follow-up — this phase needs a running Orivory stack and "
    "injected ingest/recall callables (see eval/benchmarks/README.md); no results "
    "were fabricated"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_benchmark.py",
        description="Phased benchmark runner for LongMemEval-S and MemoryAgentBench.",
    )
    parser.add_argument("--benchmark", required=True, choices=sorted(BENCHMARK_LOADERS))
    parser.add_argument("--dataset", type=Path, required=True, help="path to the dataset JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for results")
    parser.add_argument("--limit", type=int, default=None, help="cap on instance count")
    parser.add_argument("--phase", choices=list(PHASES), default="plan")
    parser.add_argument(
        "--results",
        type=Path,
        default=None,
        help="existing per-question results JSON for --phase score",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.dataset.is_file():
        print(
            f"error: dataset not found — download per eval/benchmarks/README.md: {args.dataset}",
            file=sys.stderr,
        )
        return 2

    loader = BENCHMARK_LOADERS[args.benchmark]
    instances = loader(args.dataset)
    selected = instances[: args.limit] if args.limit is not None else instances

    config = RunnerConfig(
        benchmark=args.benchmark,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        limit=args.limit,
    )

    if args.phase == "plan":
        print(f"benchmark: {args.benchmark}")
        print(f"dataset: {args.dataset}")
        print(f"dataset_sha256: {record_sha256(args.dataset)}")
        print(f"instances: {len(instances)}")
        print(f"selected: {len(selected)} (limit={args.limit})")
        print(f"phases: {' → '.join(PHASES)}")
        print(
            "plan only — no results written; ingest/query need live wiring, "
            "score aggregates an existing results JSON"
        )
        return 0

    if args.phase in ("ingest", "query"):
        print(f"error: --phase {args.phase}: {_LIVE_WIRING}", file=sys.stderr)
        return 3

    # --phase score: aggregate an existing per-question results JSON, if given.
    if args.results is not None and args.results.is_file():
        records = json.loads(args.results.read_text())
        if not isinstance(records, list):
            print(f"error: {args.results} must be a JSON array of per-question results", file=sys.stderr)
            return 2
        summary = run_score_sync(config, records)
        print(f"benchmark: {args.benchmark}")
        print(f"mean: {summary['mean']:.3f}")
        print(f"runs: {summary['runs']}")
        print(f"dataset_sha256: {summary['dataset_sha256']}")
        if summary["pending_interpretation"]:
            print(f"pending_interpretation: {len(summary['pending_interpretation'])} (not yet scoreable — LLM-judge follow-up)")
        out = args.output_dir / "results.json"
        write_results(out, summary)
        print(f"results written: {out}")
        return 0

    print(f"error: --phase score: {_LIVE_WIRING}", file=sys.stderr)
    print(
        "hint: pass --results PATH pointing at a per-question results JSON "
        "from a real run to aggregate it",
        file=sys.stderr,
    )
    return 3


def run_score_sync(config: RunnerConfig, records: list[dict]) -> dict:
    """Synchronous wrapper so the CLI can aggregate without an event loop."""
    import asyncio

    return asyncio.run(run_score(config, records))


if __name__ == "__main__":
    raise SystemExit(main())
