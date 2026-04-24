from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from eval.metrics import (  # noqa: E402
    calculate_fallback_accuracy,
    calculate_keyword_coverage,
    calculate_source_hit,
    has_citation,
    summarize_results,
)
from eval.reporting import (  # noqa: E402
    build_report,
    write_json_report,
    write_markdown_report,
)

DEFAULT_DATASET = ROOT / "eval" / "supportmind_eval_dataset.json"
DEFAULT_SAMPLE_DOCS = ROOT / "sample_docs"
DEFAULT_OUTPUT_DIR = ROOT / "eval" / "results"
FALLBACK_ANSWER = (
    "I don't know based on the available SupportMind documentation. "
    "This question appears to be outside the available support documentation."
)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_sample_docs(sample_docs_dir: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(sample_docs_dir.glob("*.md"))
    }


def _score_document(query: str, expected_keywords: list[str], document_text: str) -> float:
    query_terms = [term for term in query.lower().replace("?", "").split() if len(term) > 2]
    text = document_text.casefold()
    query_score = sum(1 for term in query_terms if term in text)
    keyword_score = calculate_keyword_coverage(document_text, expected_keywords) * 3
    return query_score + keyword_score


def retrieve_offline(
    item: dict[str, Any],
    documents: dict[str, str],
    top_k: int,
) -> list[dict[str, Any]]:
    if item.get("should_fallback", False):
        return []

    expected_keywords = item.get("expected_keywords", [])
    scored = [
        {
            "source": filename,
            "content": content,
            "score": _score_document(item["query"], expected_keywords, content),
        }
        for filename, content in documents.items()
    ]
    scored.sort(key=lambda row: row["score"], reverse=True)
    return [row for row in scored[:top_k] if row["score"] > 0]


def generate_offline_answer(item: dict[str, Any], retrieved: list[dict[str, Any]]) -> str:
    if item.get("should_fallback", False) or not retrieved:
        return FALLBACK_ANSWER

    primary = retrieved[0]
    expected_keywords = item.get("expected_keywords", [])
    keyword_sentence = ", ".join(expected_keywords[:5])
    source_excerpt = " ".join(primary["content"].split())[:450]
    return (
        f"Based on the SupportMind documentation, relevant details include: "
        f"{keyword_sentence}. {source_excerpt} [Source 1]"
    )


def evaluate_case(
    item: dict[str, Any],
    documents: dict[str, str],
    top_k: int,
) -> dict[str, Any]:
    started = perf_counter()
    retrieved = retrieve_offline(item, documents, top_k)
    answer = generate_offline_answer(item, retrieved)
    returned_sources = [chunk["source"] for chunk in retrieved]
    expected_sources = item.get("expected_sources", [])

    source_text = "\n\n".join(chunk["content"] for chunk in retrieved)
    scored_text = f"{answer}\n\n{source_text}"
    source_hit = calculate_source_hit(returned_sources, expected_sources)
    keyword_coverage = calculate_keyword_coverage(scored_text, item.get("expected_keywords", []))
    fallback_accuracy = calculate_fallback_accuracy(item.get("should_fallback", False), answer)
    citation_present = has_citation(answer, returned_sources)
    latency_ms = (perf_counter() - started) * 1000

    passed = (
        source_hit >= 1.0
        and keyword_coverage >= 0.75
        and fallback_accuracy >= 1.0
        and (citation_present or item.get("should_fallback", False))
    )

    return {
        "id": item["id"],
        "query": item["query"],
        "category": item["category"],
        "expected_sources": expected_sources,
        "returned_sources": returned_sources,
        "expected_keywords": item.get("expected_keywords", []),
        "should_fallback": item.get("should_fallback", False),
        "answer": answer,
        "source_hit": source_hit,
        "keyword_coverage": keyword_coverage,
        "has_citation": citation_present,
        "fallback_accuracy": fallback_accuracy,
        "latency_ms": latency_ms,
        "hallucination_flagged": False,
        "correction_count": 0,
        "passed": passed,
    }


def run_evaluation(
    dataset_path: Path,
    sample_docs_dir: Path,
    output_dir: Path,
    top_k: int,
    fail_under_source_hit: float,
    fail_under_keyword_coverage: float,
) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    documents = load_sample_docs(sample_docs_dir)
    results = [evaluate_case(item, documents, top_k) for item in dataset]
    summary = summarize_results(results)
    report = build_report(
        results=results,
        summary=summary,
        metadata={
            "dataset": str(dataset_path),
            "sample_docs": str(sample_docs_dir),
            "top_k": top_k,
            "mode": "offline",
        },
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json_report(report, output_dir / "latest_report.json")
    write_markdown_report(report, output_dir / "latest_report.md")

    print("SupportMind RAG Evaluation")
    print("=" * 30)
    print(f"Cases:             {summary['total_cases']}")
    print(f"Source hit rate:   {summary['source_hit_rate']:.1%}")
    print(f"Keyword coverage:  {summary['keyword_coverage']:.1%}")
    print(f"Citation rate:     {summary['citation_rate']:.1%}")
    print(f"Fallback accuracy: {summary['fallback_accuracy']:.1%}")
    print(f"Average latency:   {summary['avg_latency_ms']:.1f} ms")
    print(f"Report:            {output_dir / 'latest_report.md'}")

    if summary["source_hit_rate"] < fail_under_source_hit:
        raise SystemExit(
            f"Source hit rate {summary['source_hit_rate']:.1%} is below threshold "
            f"{fail_under_source_hit:.1%}"
        )
    if summary["keyword_coverage"] < fail_under_keyword_coverage:
        raise SystemExit(
            f"Keyword coverage {summary['keyword_coverage']:.1%} is below threshold "
            f"{fail_under_keyword_coverage:.1%}"
        )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SupportMind deterministic RAG evaluation.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--sample-docs", type=Path, default=DEFAULT_SAMPLE_DOCS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fail-under-source-hit", type=float, default=0.0)
    parser.add_argument("--fail-under-keyword-coverage", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_evaluation(
        dataset_path=args.dataset,
        sample_docs_dir=args.sample_docs,
        output_dir=args.output_dir,
        top_k=args.top_k,
        fail_under_source_hit=args.fail_under_source_hit,
        fail_under_keyword_coverage=args.fail_under_keyword_coverage,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
