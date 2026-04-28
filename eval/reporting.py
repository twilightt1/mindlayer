from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _format_ms(value: float) -> str:
    return f"{value:.1f} ms"


def _status_icon(passed: bool) -> str:
    return "✅" if passed else "⚠️"


def write_json_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    results = report["results"]
    failed = [result for result in results if not result.get("passed", False)]

    lines = [
        "# SupportMind RAG Evaluation Report",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total cases | {summary['total_cases']} |",
        f"| Passed cases | {summary['passed_cases']} |",
        f"| Failed cases | {summary['failed_cases']} |",
        f"| Source hit rate | {_format_percent(summary['source_hit_rate'])} |",
        f"| Keyword coverage | {_format_percent(summary['keyword_coverage'])} |",
        f"| Citation rate | {_format_percent(summary['citation_rate'])} |",
        f"| Fallback accuracy | {_format_percent(summary['fallback_accuracy'])} |",
        f"| Hallucination flag rate | {_format_percent(summary['hallucination_flag_rate'])} |",
        f"| Correction rate | {_format_percent(summary['correction_rate'])} |",
        f"| Average latency | {_format_ms(summary['avg_latency_ms'])} |",
        "",
        "## Per-case Results",
        "",
        "| Status | ID | Category | Source hit | Keyword coverage | Citation | Fallback OK | Latency | Sources |",
        "|---|---|---|---:|---:|---|---|---:|---|",
    ]

    for result in results:
        sources = ", ".join(result.get("returned_sources", [])) or "—"
        lines.append(
            "| "
            f"{_status_icon(result.get('passed', False))} | "
            f"{result['id']} | "
            f"{result['category']} | "
            f"{_format_percent(result['source_hit'])} | "
            f"{_format_percent(result['keyword_coverage'])} | "
            f"{'yes' if result['has_citation'] else 'no'} | "
            f"{'yes' if result['fallback_accuracy'] == 1.0 else 'no'} | "
            f"{_format_ms(result['latency_ms'])} | "
            f"{sources} |"
        )

    ragas = summary.get("ragas") or {}
    if ragas:
        lines.extend(
            [
                "## RAGAS-Style Metrics",
                "",
                "| Metric | Value |",
                "|---|---:|",
            ]
        )
        for key, value in ragas.items():
            if isinstance(value, float):
                lines.append(f"| {key} | {value:.3f} |")
            else:
                lines.append(f"| {key} | {value} |")
        lines.append("")

    lines.extend(["", "## Failed / Warning Cases", ""])
    if not failed:
        lines.append("All cases passed the deterministic evaluation thresholds.")
    else:
        for result in failed:
            lines.extend(
                [
                    f"### {_status_icon(False)} {result['id']} — {result['query']}",
                    "",
                    f"- Category: `{result['category']}`",
                    f"- Expected sources: {', '.join(result.get('expected_sources', [])) or '—'}",
                    f"- Returned sources: {', '.join(result.get('returned_sources', [])) or '—'}",
                    f"- Source hit: {_format_percent(result['source_hit'])}",
                    f"- Keyword coverage: {_format_percent(result['keyword_coverage'])}",
                    f"- Citation present: {'yes' if result['has_citation'] else 'no'}",
                    f"- Fallback accuracy: {_format_percent(result['fallback_accuracy'])}",
                ]
            )
            if "ragas" in result:
                ragas_pairs = ", ".join(
                    f"{k}={v:.3f}" for k, v in result["ragas"].items() if isinstance(v, float)
                )
                if ragas_pairs:
                    lines.append(f"- RAGAS: {ragas_pairs}")
            lines.append("")

    lines.extend(
        [
            "## Recommendations",
            "",
            "- Add failed or ambiguous production questions to the dataset.",
            "- Investigate cases with low source hit before changing chunking or retriever weights.",
            "- Track citation and fallback accuracy separately from in-scope retrieval quality.",
            "- Use live/API evaluation as a separate non-blocking workflow when infrastructure and LLM keys are available.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(report), encoding="utf-8")


def build_report(results: list[dict[str, Any]], summary: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "metadata": metadata,
        "summary": summary,
        "results": results,
    }
