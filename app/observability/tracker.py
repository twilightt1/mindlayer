"""
MLflow-style experiment tracking for MindLayer.

Lightweight, SQLite-backed run logger. No external services required.

Usage:
    from app.observability.tracker import RunTracker

    tracker = RunTracker(db_path="eval/experiments.db")
    with tracker.start_run("router_v1_baseline", tags={"phase": "baseline"}) as run:
        tracker.log_params({"llm_model": "gpt-4o-mini", "top_k": 5})
        tracker.log_metrics({"source_hit_rate": 0.92, "latency_ms": 410.0})
        tracker.log_artifact("eval/results/latest_report.md")

    # Compare runs
    comparison = tracker.compare_runs(["router_v1", "router_v2"])
"""
from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import subprocess
import threading
import time
import uuid
from collections.abc import Generator, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("eval/experiments.db")


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_git_sha() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return out.decode().strip()
    except Exception:
        return None


class RunTracker:
    """SQLite-backed run logger with MLflow-style API."""

    def __init__(self, db_path: str | os.PathLike[str] = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
        self._active_run_id: str | None = None

    # -- DB setup -----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id      TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    started_at  TEXT NOT NULL,
                    ended_at    TEXT,
                    status      TEXT NOT NULL DEFAULT 'running',
                    git_sha     TEXT,
                    user        TEXT
                );
                CREATE TABLE IF NOT EXISTS params (
                    run_id  TEXT NOT NULL,
                    key     TEXT NOT NULL,
                    value   TEXT,
                    PRIMARY KEY (run_id, key),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS metrics (
                    run_id  TEXT NOT NULL,
                    key     TEXT NOT NULL,
                    value   REAL,
                    step    INTEGER DEFAULT 0,
                    ts      TEXT NOT NULL,
                    PRIMARY KEY (run_id, key, step),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS tags (
                    run_id  TEXT NOT NULL,
                    key     TEXT NOT NULL,
                    value   TEXT,
                    PRIMARY KEY (run_id, key),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id    TEXT NOT NULL,
                    path      TEXT NOT NULL,
                    kind      TEXT,
                    logged_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at);
                """
            )

    # -- Run lifecycle -------------------------------------------------------

    @contextlib.contextmanager
    def start_run(
        self,
        name: str,
        tags: dict[str, str] | None = None,
        run_id: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        rid = run_id or f"{name}-{uuid.uuid4().hex[:8]}"
        started = _utcnow_iso()
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO runs (run_id, name, started_at, git_sha, user) VALUES (?,?,?,?,?)",
                    (rid, name, started, _safe_git_sha(), os.environ.get("USER", "unknown")),
                )
                if tags:
                    conn.executemany(
                        "INSERT OR REPLACE INTO tags (run_id, key, value) VALUES (?,?,?)",
                        [(rid, k, v) for k, v in tags.items()],
                    )
                conn.commit()
        self._active_run_id = rid
        ctx: dict[str, Any] = {"run_id": rid, "name": name, "started_at": started}
        try:
            yield ctx
            self.end_run(rid, status="finished")
        except Exception as e:  # pragma: no cover - context manager
            self.end_run(rid, status="failed")
            ctx["error"] = str(e)
            raise
        finally:
            self._active_run_id = None

    def end_run(self, run_id: str, status: str = "finished") -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE runs SET ended_at = ?, status = ? WHERE run_id = ?",
                    (_utcnow_iso(), status, run_id),
                )
                conn.commit()

    # -- Logging -------------------------------------------------------------

    def log_params(self, params: dict[str, Any], run_id: str | None = None) -> None:
        rid = run_id or self._active_run_id
        if not rid:
            raise RuntimeError("No active run. Call start_run() first.")
        with self._lock:
            with self._connect() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO params (run_id, key, value) VALUES (?,?,?)",
                    [(rid, k, json.dumps(v)) for k, v in params.items()],
                )
                conn.commit()

    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int = 0,
        run_id: str | None = None,
    ) -> None:
        rid = run_id or self._active_run_id
        if not rid:
            raise RuntimeError("No active run. Call start_run() first.")
        ts = _utcnow_iso()
        with self._lock:
            with self._connect() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO metrics (run_id, key, value, step, ts) VALUES (?,?,?,?,?)",
                    [(rid, k, float(v), step, ts) for k, v in metrics.items()],
                )
                conn.commit()

    def log_artifact(self, path: str | os.PathLike[str], run_id: str | None = None) -> None:
        rid = run_id or self._active_run_id
        if not rid:
            raise RuntimeError("No active run. Call start_run() first.")
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO artifacts (run_id, path, kind, logged_at) VALUES (?,?,?,?)",
                    (rid, str(path), "file", _utcnow_iso()),
                )
                conn.commit()

    # -- Querying ------------------------------------------------------------

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_params(self, run_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM params WHERE run_id = ?", (run_id,)
            ).fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    def get_metrics(self, run_id: str) -> dict[str, float]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM metrics WHERE run_id = ? AND step = 0",
                (run_id,),
            ).fetchall()
        return {r["key"]: float(r["value"]) for r in rows}

    def compare_runs(
        self,
        run_ids: Iterable[str],
        metrics: Iterable[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Return a side-by-side comparison of params and metrics."""
        out: dict[str, dict[str, Any]] = {}
        all_metric_keys: set[str] = set()
        for rid in run_ids:
            run = self.get_run(rid)
            if run is None:
                continue
            params = self.get_params(rid)
            m = self.get_metrics(rid)
            out[rid] = {
                "name": run.get("name"),
                "started_at": run.get("started_at"),
                "ended_at": run.get("ended_at"),
                "status": run.get("status"),
                "params": params,
                "metrics": m,
            }
            all_metric_keys.update(m.keys())
        # Ensure every run has every key (None if missing)
        keys = metrics or sorted(all_metric_keys)
        for rid in out:
            for k in keys:
                out[rid]["metrics"].setdefault(k, None)
        return out


# ---------------------------------------------------------------------------
# Convenience: stopwatch
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def stopwatch() -> Generator[dict[str, float], None, None]:
    """Time a code block. Writes total_ms into the dict."""
    out: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield out
    finally:
        out["total_ms"] = round((time.perf_counter() - start) * 1000, 2)
