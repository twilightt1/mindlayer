"""Lightweight offline evaluation for the MindLayer Demo dataset.

This script checks whether each expected source document contains the keywords
that should support the demo answer. It does not require the API, database, LLM,
or vector store to be running, so it is useful as a fast portfolio sanity check.

For the richer report generator, use `python eval/run_eval.py`.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DOCS = ROOT / "sample_docs"
DATASET = Path(__file__).resolve().parent / "mindlayer_eval_dataset.json"


def load_dataset() -> list[dict]:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return text.casefold()


def keyword_coverage(document_text: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0
    text = normalize(document_text)
    hits = sum(1 for keyword in expected_keywords if normalize(keyword) in text)
    return hits / len(expected_keywords)


def expected_doc(item: dict) -> str | None:
    sources = item.get("expected_sources", [])
    if sources:
        return sources[0]
    return item.get("expected_doc")


def item_question(item: dict) -> str:
    return item.get("query") or item.get("question", "")


def run() -> int:
    started = perf_counter()
    dataset = load_dataset()
    rows = []

    for item in dataset:
        doc_name = expected_doc(item)
        if not doc_name:
            rows.append(
                {
                    "question": item_question(item),
                    "expected_doc": "—",
                    "doc_exists": True,
                    "keyword_coverage": 1.0,
                    "should_fallback": True,
                }
            )
            continue

        doc_path = SAMPLE_DOCS / doc_name
        exists = doc_path.exists()
        text = doc_path.read_text(encoding="utf-8") if exists else ""
        coverage = keyword_coverage(text, item.get("expected_keywords", []))
        rows.append(
            {
                "question": item_question(item),
                "expected_doc": doc_name,
                "doc_exists": exists,
                "keyword_coverage": coverage,
                "should_fallback": item.get("should_fallback", False),
            }
        )

    total = len(rows)
    doc_hit = sum(1 for row in rows if row["doc_exists"]) / total if total else 0.0
    avg_coverage = sum(row["keyword_coverage"] for row in rows) / total if total else 0.0
    latency_ms = (perf_counter() - started) * 1000

    print("MindLayer Offline Eval")
    print("=" * 28)
    print(f"Questions:          {total}")
    print(f"Expected doc hit:   {doc_hit:.2%}")
    print(f"Keyword coverage:   {avg_coverage:.2%}")
    print(f"Runtime:            {latency_ms:.1f} ms")
    print()

    for row in rows:
        status = "PASS" if row["doc_exists"] and row["keyword_coverage"] >= 0.75 else "WARN"
        print(
            f"[{status}] {row['expected_doc']} | "
            f"coverage={row['keyword_coverage']:.2%} | {row['question']}"
        )

    return 0 if doc_hit == 1.0 and avg_coverage >= 0.75 else 1


if __name__ == "__main__":
    raise SystemExit(run())
