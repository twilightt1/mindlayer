"""
CLI for running experiment sweeps with the MindLayer eval suite.

Examples:

  # Compare two top-k values with the offline evaluator
  python scripts/eval_experiments.py \\
      --experiment topk_sweep \\
      --dataset eval/mindlayer_eval_dataset.json \\
      --sample-docs sample_docs \\
      --output-dir eval/experiments \\
      --variants topk_3,topk_5,topk_8

  # Same with RAGAS metrics
  python scripts/eval_experiments.py \\
      --experiment router_compare --enable-ragas \\
      --variants v1,v2

Variants are defined in code (see app.observability.experiments.Variant),
or you can use the shorthand `--variants name1,name2` which will create
variants with only a name (no params). For parameterized sweeps, use a
JSON config file (see --config).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.observability.experiments import Experiment, Variant  # noqa: E402

DEFAULT_DATASET = ROOT / "eval" / "mindlayer_eval_dataset.json"
DEFAULT_SAMPLE_DOCS = ROOT / "sample_docs"
DEFAULT_OUTPUT_DIR = ROOT / "eval" / "experiments"
DEFAULT_TRACKER_DB = ROOT / "eval" / "experiments.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a MindLayer experiment sweep.")
    parser.add_argument("--experiment", required=True, help="Experiment name (used for run naming and output dir).")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--sample-docs", type=Path, default=DEFAULT_SAMPLE_DOCS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--tracker-db", type=Path, default=DEFAULT_TRACKER_DB)
    parser.add_argument("--primary-metric", default="source_hit_rate")
    parser.add_argument(
        "--variants",
        help="Comma-separated list of variant names (uses name only, no params).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to JSON file: list of {name, params, tags} variant definitions.",
    )
    parser.add_argument("--enable-ragas", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="List variants and exit.")
    return parser.parse_args()


def build_variants(args: argparse.Namespace) -> list[Variant]:
    if args.config:
        data = json.loads(args.config.read_text(encoding="utf-8"))
        return [Variant(**item) for item in data]
    if not args.variants:
        raise SystemExit("Either --variants or --config is required.")
    return [Variant(name=name.strip(), params={"top_k": 5}) for name in args.variants.split(",") if name.strip()]


def main() -> int:
    args = parse_args()
    variants = build_variants(args)
    if args.dry_run:
        print(f"Experiment: {args.experiment}")
        print(f"Variants: {[v.name for v in variants]}")
        print(f"Dataset: {args.dataset}")
        print(f"Sample docs: {args.sample_docs}")
        print(f"Output dir: {args.output_dir}")
        return 0

    exp = Experiment(
        name=args.experiment,
        dataset_path=args.dataset,
        sample_docs_dir=args.sample_docs,
        output_dir=args.output_dir,
        tracker_db=args.tracker_db,
        primary_metric=args.primary_metric,
    )
    exp.add_variants(variants)
    result = exp.run(enable_ragas=args.enable_ragas)
    print(f"\nExperiment '{args.experiment}' complete.")
    print(f"Best run ({result.best_metric}): {result.best_run_id}")
    print(f"Comparison report: {args.output_dir / f'{args.experiment}_comparison.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
