"""CLI behavior: plan phase prints and exits 0; other phases refuse honestly; score aggregates."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "eval" / "run_benchmark.py"
FIXTURES = REPO / "eval" / "benchmarks" / "fixtures"

pytestmark = pytest.mark.eval


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def test_plan_phase_prints_instance_count_and_phases_and_exits_zero(tmp_path):
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(FIXTURES / "longmemeval_s_fixture.json"),
        "--output-dir", str(tmp_path),
        "--limit", "2",
        "--phase", "plan",
    )
    assert proc.returncode == 0, proc.stderr
    assert "2" in proc.stdout  # instance count
    assert "ingest" in proc.stdout
    assert "query" in proc.stdout
    assert "score" in proc.stdout


def test_plan_phase_writes_no_results(tmp_path):
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(FIXTURES / "longmemeval_s_fixture.json"),
        "--output-dir", str(tmp_path),
        "--phase", "plan",
    )
    assert proc.returncode == 0, proc.stderr
    assert list(tmp_path.rglob("*.json")) == []


def test_missing_dataset_exits_nonzero_with_readme_pointer(tmp_path):
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(tmp_path / "missing.json"),
        "--output-dir", str(tmp_path / "out"),
        "--phase", "plan",
    )
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "dataset not found" in combined
    assert "eval/benchmarks/README.md" in combined


def test_ingest_phase_without_live_stack_exits_with_followup_message(tmp_path):
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(FIXTURES / "longmemeval_s_fixture.json"),
        "--output-dir", str(tmp_path),
        "--phase", "ingest",
    )
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "live wiring is a follow-up" in combined
    # And it never fabricated a results file while refusing.
    assert list(tmp_path.rglob("*.json")) == []


def test_query_phase_without_live_stack_exits_with_followup_message(tmp_path):
    proc = run_cli(
        "--benchmark", "memoryagentbench",
        "--dataset", str(FIXTURES / "memoryagentbench_fixture.json"),
        "--output-dir", str(tmp_path),
        "--phase", "query",
    )
    assert proc.returncode != 0
    assert "live wiring is a follow-up" in proc.stdout + proc.stderr


def test_score_phase_on_existing_results_json_aggregates(tmp_path):
    """score on an existing per-question results JSON aggregates — the one live-free path."""
    results_path = tmp_path / "results.json"
    results_path.write_text(
        json.dumps(
            [
                {"question_id": "q1", "correct": True},
                {"question_id": "q2", "correct": True},
                {"question_id": "q3", "correct": False},
            ]
        )
    )
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(FIXTURES / "longmemeval_s_fixture.json"),
        "--output-dir", str(tmp_path),
        "--phase", "score",
        "--results", str(results_path),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "mean: 0.667" in proc.stdout  # 2/3 mean, honestly aggregated
    assert "questions: 3" in proc.stdout


def test_score_phase_without_results_flag_exits_three_with_pointer(tmp_path):
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(FIXTURES / "longmemeval_s_fixture.json"),
        "--output-dir", str(tmp_path),
        "--phase", "score",
    )
    assert proc.returncode == 3
    combined = proc.stdout + proc.stderr
    assert "pass --results PATH" in combined
    assert list(tmp_path.rglob("*.json")) == []


def test_score_phase_with_missing_results_file_exits_two_echoing_path(tmp_path):
    missing = tmp_path / "nope.json"
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(FIXTURES / "longmemeval_s_fixture.json"),
        "--output-dir", str(tmp_path),
        "--phase", "score",
        "--results", str(missing),
    )
    assert proc.returncode == 2
    assert str(missing) in proc.stderr
    assert list(tmp_path.rglob("*.json")) == []


def test_score_phase_with_malformed_results_json_exits_two_cleanly(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    proc = run_cli(
        "--benchmark", "longmemeval_s",
        "--dataset", str(FIXTURES / "longmemeval_s_fixture.json"),
        "--output-dir", str(tmp_path),
        "--phase", "score",
        "--results", str(bad),
    )
    assert proc.returncode == 2
    assert "not valid JSON" in proc.stderr
    assert str(bad) in proc.stderr
    assert "Traceback" not in proc.stderr
    assert list(tmp_path.rglob("*.json")) == [bad]
