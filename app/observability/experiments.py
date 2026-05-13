"""
High-level experiment wrapper around `RunTracker`.

Defines a named experiment, runs the offline evaluation under multiple
configurations (e.g. different prompt variants or top-k values), and stores
a per-run comparison in SQLite.

Example:
    from app.observability.experiments import Experiment, Variant

    exp = Experiment(
        name="router_topk_sweep",
        dataset_path="eval/mindlayer_eval_dataset.json",
        sample_docs_dir="sample_docs",
        output_dir="eval/experiments",
    )
    exp.add_variant(Variant(name="topk_3", params={"top_k": 3, "variant": "v1"}))
    exp.add_variant(Variant(name="topk_5", params={"top_k": 5, "variant": "v1"}))
    exp.add_variant(Variant(name="topk_8", params={"top_k": 8, "variant": "v1"}))
    report = exp.run(enable_ragas=True)
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.observability.tracker import RunTracker, _utcnow_iso


@dataclass
class Variant:
    """A single experimental configuration to evaluate."""

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    experiment: str
    runs: list[dict[str, Any]]
    best_run_id: str | None
    best_metric: str
    comparison_table: list[list[Any]]


class Experiment:
    def __init__(
        self,
        name: str,
        dataset_path: str | Path,
        sample_docs_dir: str | Path,
        output_dir: str | Path,
        tracker_db: str | Path = "eval/experiments.db",
        primary_metric: str = "source_hit_rate",
    ) -> None:
        self.name = name
        self.dataset_path = Path(dataset_path)
        self.sample_docs_dir = Path(sample_docs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tracker = RunTracker(db_path=tracker_db)
        self.primary_metric = primary_metric
        self.variants: list[Variant] = []

    def add_variant(self, variant: Variant) -> None:
        self.variants.append(variant)

    def add_variants(self, variants: Iterable[Variant]) -> None:
        self.variants.extend(variants)

    def run(self, enable_ragas: bool = True) -> ExperimentResult:
        """Run every variant and persist per-run results to the tracker."""
        from eval.run_eval import run_evaluation  # local import to avoid hard dep at module load

        runs: list[dict[str, Any]] = []
        for variant in self.variants:
            run_name = f"{self.name}/{variant.name}"
            with self.tracker.start_run(run_name, tags={"experiment": self.name, **variant.tags}) as run:
                self.tracker.log_params(variant.params, run_id=run["run_id"])
                self.tracker.log_params({"dataset": str(self.dataset_path)}, run_id=run["run_id"])
                self.tracker.log_params({"enable_ragas": enable_ragas}, run_id=run["run_id"])
                variant_output = self.output_dir / variant.name
                variant_output.mkdir(parents=True, exist_ok=True)
                report = run_evaluation(
                    dataset_path=self.dataset_path,
                    sample_docs_dir=self.sample_docs_dir,
                    output_dir=variant_output,
                    top_k=int(variant.params.get("top_k", 5)),
                    fail_under_source_hit=0.0,
                    fail_under_keyword_coverage=0.0,
                    enable_ragas=enable_ragas,
                )
                summary = report.get("summary", {})
                flat_metrics = {k: v for k, v in summary.items() if isinstance(v, (int, float))}
                # Unpack RAGAS sub-dict so each metric gets its own column
                ragas_block = summary.get("ragas", {}) or {}
                for k, v in ragas_block.items():
                    flat_metrics[f"ragas_{k}"] = v
                self.tracker.log_metrics(flat_metrics, run_id=run["run_id"])
                self.tracker.log_artifact(
                    variant_output / "latest_report.md", run_id=run["run_id"]
                )
                runs.append(
                    {
                        "run_id": run["run_id"],
                        "variant": variant.name,
                        "params": variant.params,
                        "summary": flat_metrics,
                    }
                )

        # Build comparison table
        all_metric_keys: set[str] = set()
        for r in runs:
            all_metric_keys.update(r["summary"].keys())
        metric_keys = sorted(all_metric_keys)
        comparison_table: list[list[Any]] = [
            ["variant", "run_id", *metric_keys],
        ]
        for r in runs:
            row = [r["variant"], r["run_id"]]
            for k in metric_keys:
                row.append(r["summary"].get(k))
            comparison_table.append(row)

        # Pick best
        best_run_id = None
        best_score = -1.0
        for r in runs:
            score = r["summary"].get(self.primary_metric, 0.0) or 0.0
            if score > best_score:
                best_score = score
                best_run_id = r["run_id"]

        result = ExperimentResult(
            experiment=self.name,
            runs=runs,
            best_run_id=best_run_id,
            best_metric=self.primary_metric,
            comparison_table=comparison_table,
        )

        # Persist a human-readable comparison
        out_path = self.output_dir / f"{self.name}_comparison.md"
        out_path.write_text(_render_comparison(result), encoding="utf-8")
        # Also write raw JSON
        json_path = self.output_dir / f"{self.name}_comparison.json"
        json_path.write_text(
            json.dumps(
                {
                    "experiment": result.experiment,
                    "best_run_id": result.best_run_id,
                    "best_metric": result.best_metric,
                    "runs": result.runs,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return result


def _render_comparison(result: ExperimentResult) -> str:
    lines = [
        f"# Experiment: {result.experiment}",
        "",
        f"Generated at: `{_utcnow_iso()}`",
        "",
        f"Primary metric: **{result.best_metric}**",
        "",
        "## Comparison Table",
        "",
    ]
    if not result.comparison_table:
        lines.append("No runs.")
        return "\n".join(lines)
    header = result.comparison_table[0]
    lines.append("| " + " | ".join(str(c) for c in header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in result.comparison_table[1:]:
        cells: list[str] = []
        for i, c in enumerate(row):
            if i < 2:
                cells.append(str(c))
            elif isinstance(c, float):
                cells.append(f"{c:.3f}")
            else:
                cells.append(str(c))
        lines.append("| " + " | ".join(cells) + " |")
    if result.best_run_id:
        lines.extend(["", f"🏆 Best run: `{result.best_run_id}`", ""])
    return "\n".join(lines)
