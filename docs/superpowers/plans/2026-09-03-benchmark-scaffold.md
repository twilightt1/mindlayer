# Benchmark Harness Scaffold Implementation Plan (MVP item 6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the benchmark harness scaffold for Orivory's memory hub: protocol docs with leaderboard-hygiene rules, LongMemEval-S adapter (primary benchmark), MemoryAgentBench adapter stub (secondary — selective forgetting), and a phased runner CLI — fixture-tested, CI-safe, with **zero fabricated scores** (real runs need a live stack + downloaded datasets + LLM keys).

**Architecture:** `eval/benchmarks/` extends the existing eval harness (`eval/metrics.py`, `eval/reporting.py` — reuse, don't duplicate). A `BenchmarkInstance` dataclass normalizes each benchmark's dataset shape; adapters load → ingest (feed history into Orivory memories via the API service layer) → query (recall) → score (judge or exact-match); a runner CLI drives phases separately so ingest (hours) is never repeated accidentally. Datasets are downloaded by the operator (HuggingFace, ~264MB) and never committed.

**Tech Stack:** Python 3.12+ stdlib + existing eval helpers; no new dependencies. Live runs use the same OpenAI client the backend already has.

**Spec:** `docs/ideas/open-memory-hub.md` (MVP item 6) + benchmark selection rationale in `docs/research/PAPERS_AGENT_MEMORY.md` §3 (LongMemEval-S primary per ICLR 2025; MemoryAgentBench secondary — only benchmark scoring selective forgetting; LoCoMo never-lead rule).

## Global Constraints

- Python 3.12+, ruff line-length 120, target py313. Gate: zero NEW ruff findings in touched files (repo baseline red ~224 — do not fix unrelated files).
- CI-safe tests only: adapters tested against **inline fixture JSON** (tiny, committed), never the real 264MB dataset. Fixture mirrors the verified official schema exactly.
- Dataset schema is VERIFIED from the official repo (github.com/xiaowu0162/LongMemEval README, fetched 2026-09-04): 500 instances; fields `question_id`, `question_type` (one of `single-session-user`, `single-session-assistant`, `single-session-preference`, `temporal-reasoning`, `knowledge-update`, `multi-session`; id suffix `_abs` = abstention), `question`, `answer`, `question_date`, `haystack_session_ids`, `haystack_dates`, `haystack_sessions` (parallel arrays; each session = list of `{role: user|assistant, content: str}` turns; evidence turns carry `has_answer: true`), `answer_session_ids` (evidence subset of session ids).
- **No fabricated scores.** Runners write results files only from actual runs; without a dataset/live stack they exit with a clear error. Never commit result JSONs claiming benchmark scores.
- Leaderboard hygiene (from the LoCoMo controversy — PAPERS_AGENT_MEMORY §3.1): judge prompt version pinned and committed; ≥3 runs with mean±variance when scoring is judged; dataset file SHA-256 recorded in every result; full-context baseline noted; protocol deviations stated.
- datetime: `datetime.now(UTC)` aware convention. Conventional Commits. Register nothing in main app (eval-only).

---

### Task 1: Package skeleton + protocol doc + fixtures

**Files:**
- Create: `eval/benchmarks/__init__.py` (docstring only)
- Create: `eval/benchmarks/README.md`
- Create: `eval/benchmarks/fixtures/longmemeval_s_fixture.json`
- Create: `eval/benchmarks/fixtures/memoryagentbench_fixture.json`
- Test: `tests/benchmarks/test_fixtures.py`

**Interfaces:**
- Produces: fixture files whose top level is a JSON **array** of instances matching the verified schema (LongMemEval) and the MemoryAgentBench stub schema (Task 3 defines its loader; fixture has `question_id`, `question`, `answer`, `sessions`, `answer_session_ids`, `competency` in {`accurate_retrieval`, `test_time_learning`, `long_range_understanding`, `selective_forgetting`}, `phase` in {`ingest`, `query`}).

- [ ] **Step 1: Write the failing test** — `tests/benchmarks/test_fixtures.py`:

```python
"""Fixture integrity: committed fixtures must parse and match the official schemas."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "eval" / "benchmarks" / "fixtures"


def test_longmemeval_fixture_matches_official_schema():
    records = json.loads((FIXTURES / "longmemeval_s_fixture.json").read_text())
    assert isinstance(records, list) and len(records) >= 2
    for rec in records:
        for field in ("question_id", "question_type", "question", "answer", "question_date",
                      "haystack_session_ids", "haystack_dates", "haystack_sessions", "answer_session_ids"):
            assert field in rec, f"missing {field}"
        assert len(rec["haystack_session_ids"]) == len(rec["haystack_sessions"]) == len(rec["haystack_dates"])
        for session in rec["haystack_sessions"]:
            for turn in session:
                assert turn["role"] in ("user", "assistant")
                assert isinstance(turn["content"], str) and turn["content"]
        assert set(rec["answer_session_ids"]).issubset(set(rec["haystack_session_ids"]))


def test_memoryagentbench_fixture_covers_all_four_competencies():
    records = json.loads((FIXTURES / "memoryagentbench_fixture.json").read_text())
    competencies = {rec["competency"] for rec in records}
    assert competencies == {"accurate_retrieval", "test_time_learning",
                            "long_range_understanding", "selective_forgetting"}
    for rec in records:
        assert rec["phase"] in ("ingest", "query")
        assert rec["question"] and rec["answer"]
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python -m pytest tests/benchmarks/test_fixtures.py -v --noconftest` → FAIL (FileNotFoundError).
- [ ] **Step 3: Create fixtures** — `eval/benchmarks/fixtures/longmemeval_s_fixture.json`: 2 instances (one `temporal-reasoning`, one `knowledge-update` whose id ends `_abs` for abstention), 2-3 sessions each, 2-4 turns per session, one turn flagged `"has_answer": true`, `answer_session_ids` pointing at it. `memoryagentbench_fixture.json`: 4 records (one per competency; the `selective_forgetting` pair uses `phase: "ingest"` for the to-be-forgotten fact and `phase: "query"` for the forgetting question).
- [ ] **Step 4: Write `eval/benchmarks/README.md`** — sections: which benchmarks and why (LongMemEval-S primary — ICLR 2025, human-curated, tests knowledge-update/temporal/abstention; MemoryAgentBench secondary — only benchmark scoring selective forgetting; LoCoMo only protocol-explicit, never lead), dataset download instructions (HuggingFace `xiaowu0162/longmemeval-cleaned` → `longmemeval_s_cleaned.json`, ~264MB, place under `eval/benchmarks/data/` — gitignored), leaderboard-hygiene rules (judge prompt version committed; ≥3 runs mean±variance; dataset SHA-256 recorded in results; full-context baseline noted; deviations stated), how to run (Task 4 CLI), and the explicit note that **no scores ship in this repo until a real run happens**.
- [ ] **Step 5: Create `eval/benchmarks/__init__.py`** — one-line docstring.
- [ ] **Step 6: Run to verify it passes** — `.venv/bin/python -m pytest tests/benchmarks/test_fixtures.py -v --noconftest` → PASS.
- [ ] **Step 7: Lint + commit** — `ruff check eval/benchmarks tests/benchmarks` → 0 findings; `git commit -m "feat: benchmark harness skeleton + protocol docs + fixtures"`.

---

### Task 2: LongMemEval-S adapter (loader + ingest + judge interfaces)

**Files:**
- Create: `eval/benchmarks/longmemeval_s.py`
- Test: `tests/benchmarks/test_longmemeval_s.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class BenchmarkInstance`: `question_id: str`, `question_type: str`, `question: str`, `answer: str`, `question_date: str`, `sessions: tuple[BenchmarkSession, ...]`, `answer_session_ids: frozenset[str]` where `@dataclass(frozen=True) class BenchmarkSession`: `session_id: str`, `date: str`, `turns: tuple[BenchmarkTurn, ...]`, `@dataclass(frozen=True) class BenchmarkTurn`: `role: str`, `content: str`, `has_answer: bool`.
  - `load_instances(path: Path) -> list[BenchmarkInstance]` — validates the schema (ValueError on missing fields / non-parallel arrays); `is_abstention(instance)` → `instance.question_id.endswith("_abs")`.
  - `async def ingest_history(session: BenchmarkSession, *, create_memory: Callable[[str, str], Awaitable[None]]) -> None` — turns each session into memory-create calls via an injected async callable (content capped at 10_000 chars, role noted in the text prefix `"[user] "`/`"[assistant] "`; date embedded as first line). The injection point keeps the adapter decoupled from the DB/API (tests pass a collector; live runs pass a closure over `MemoryService`/API).
  - `async def run_query(instance: BenchmarkInstance, *, recall: Callable[[str], Awaitable[str]]) -> str` — calls the injected recall callable with the question, returns the answer text.
  - `judge_answer(question: str, answer: str, response: str) -> bool` — exact-match guard per the official protocol's non-LLM subset: case-insensitive, whitespace-normalized containment of the gold answer for short numeric/boolean gold answers; returns False otherwise (LLM-judge integration is a follow-up — protocol README says so).

- [ ] **Step 1: Write the failing test** — `tests/benchmarks/test_longmemeval_s.py`: load the fixture, assert 2 instances typed correctly, parallel-array validation raises ValueError on a mutated copy (delete `haystack_dates`), `is_abstention` True for the `_abs` id; `ingest_history` collector receives one call per turn-capped chunk with `[user]`/`[assistant]` prefixes; `judge_answer` True on exact numeric gold, False on wrong answer.
- [ ] **Step 2: Run to verify it fails** — ImportError.
- [ ] **Step 3: Implement** `eval/benchmarks/longmemeval_s.py` per the Interfaces above (dataclasses frozen; `load_instances` reads JSON array; strict parallel-array + role validation; `ingest_history` iterates `session.turns` in order building one memory per turn with prefix + date header; `run_query` single recall call; `judge_answer` normalization = `str.lower()` + `" ".join(split())`).
- [ ] **Step 4: Run to verify it passes** — all tests green.
- [ ] **Step 5: Lint + commit** — `ruff check eval/benchmarks tests/benchmarks`; `git commit -m "feat: LongMemEval-S adapter (loader, ingest, exact-match judge)"`.

---

### Task 3: MemoryAgentBench adapter stub (selective forgetting focus)

**Files:**
- Create: `eval/benchmarks/memoryagentbench.py`
- Test: `tests/benchmarks/test_memoryagentbench.py`

**Interfaces:**
- Produces:
  - Reuses `BenchmarkInstance`/`BenchmarkSession`/`BenchmarkTurn` from `longmemeval_s.py` (import, don't duplicate).
  - `load_instances(path: Path) -> list[BenchmarkInstance]` — MemoryAgentBench fixture schema; groups records into scenarios: consecutive `ingest` records become one history, each `query` record becomes a question bound to the history ingested so far (`Scenario` dataclass: `scenario_id: str`, `competency: str`, `history: tuple[BenchmarkTurn, ...]`, `questions: tuple[BenchmarkInstance, ...]`).
  - `async def run_forgetting_scenario(scenario: Scenario, *, ingest_turn: Callable[[str], Awaitable[None]], forget: Callable[[str], Awaitable[None]], recall: Callable[[str], Awaitable[str]]) -> dict` — drives ingest → forget (the fact to forget is the turn content whose text is flagged in fixture as `"forget": true` on the turn) → recall; returns `{"recalled_after_forget": bool}` — **True means the forgotten fact was still recalled (bad)**. This is the adapter's core: it exercises Orivory's `forget_memory` path against the only benchmark that scores selective forgetting.
- [ ] **Step 1: Write the failing test** — fixture scenario grouping (4 records → 2 scenarios: `selective_forgetting` with 1 ingest + 1 query, `accurate_retrieval` likewise); `run_forgetting_scenario` with fake injectors asserts ingest called for each history turn, forget called exactly once for the `"forget": true` turn, and the returned dict shape.
- [ ] **Step 2: FAIL → Step 3: implement → Step 4: PASS** (same loop).
- [ ] **Step 5: Lint + commit** — `git commit -m "feat: MemoryAgentBench adapter stub (selective forgetting scenario)"`.

---

### Task 4: Runner CLI + eval README wiring

**Files:**
- Create: `eval/benchmarks/runner.py`
- Create: `eval/run_benchmark.py`
- Modify: `eval/README.md` (new "Benchmarks" section pointing at `eval/benchmarks/README.md`)
- Modify: `.gitignore` (add `eval/benchmarks/data/`)
- Test: `tests/benchmarks/test_runner.py`

**Interfaces:**
- Produces:
  - `eval/benchmarks/runner.py`: `@dataclass class RunnerConfig`: `benchmark: str` (`longmemeval_s` | `memoryagentbench`), `dataset_path: Path`, `output_dir: Path`, `limit: int | None`, `ingest_callable_factory: Callable[[], ...]` — NO; keep v0 honest: the runner **requires** injected callables (live wiring is a follow-up); it exposes `async def run_ingest(config, instances, ingest_history)` and `async def run_score(config, results)` that aggregate `[{question_id, correct}]` into `{"mean": float, "runs": int}` + `record_sha256(path) -> str` (dataset integrity per hygiene rules) and `write_results(out: Path, payload: dict)` (JSON + markdown via `eval.reporting` helpers if compatible, else simple writer). Runner raises `RuntimeError("dataset not found — download per eval/benchmarks/README.md")` when `dataset_path` is missing.
  - `eval/run_benchmark.py`: argparse CLI `--benchmark {longmemeval_s,memoryagentbench} --dataset PATH --output-dir PATH --limit N --phase {ingest,query,score}` — validates the dataset exists (clear error), loads via the adapter, runs the phase with **stdin-confirmation-free** dry mode: without a live stack config it prints the plan (instance count, phases) and exits 0 — it never fabricates results.
- [ ] **Step 1: Write failing tests** — runner aggregation (3 results → mean), `record_sha256` deterministic, missing dataset → RuntimeError with the README pointer, CLI `--limit 2` on the fixture prints plan and exits 0 without writing results.
- [ ] **Step 2: FAIL → implement → PASS.**
- [ ] **Step 3: Docs + gitignore** as listed.
- [ ] **Step 4: Lint + commit** — `git commit -m "feat: benchmark runner CLI (phased, no fabricated scores)"`.

---

## Follow-ups (explicitly NOT in this plan)

- LLM-judge integration for LongMemEval answers that fail the exact-match guard (official judge prompt — pin its version).
- Live wiring: ingest callables backed by the real API (`POST /api/v1/memories`) and recall via `POST /api/v1/memories/recall`; forget path via MCP `forget_memory`.
- Actual benchmark runs + public results page (`docs/benchmarks.md`) — only after ≥3 judged runs.
- LoCoMo protocol-explicit adapter (community will ask; never lead with it).
- Full MemoryAgentBench dataset rebuild (its released data is reconstructed long-context sets — arXiv 2507.05257).
