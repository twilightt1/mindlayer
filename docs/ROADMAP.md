# Orivory Roadmap

> Status: 2026-09-04. History lives in git; this file tracks what shipped and
> what's open. Design rationale for the hub direction:
> [ideas/open-memory-hub.md](ideas/open-memory-hub.md) + [research/](research/).

## Shipped

### Foundation (P0–P4, 2026-06)
- Connector-synced memories embed; reindex/backfill task + admin endpoint.
- Documents → memories unification (hybrid granularity); `save_note` intent.
- Salience loop (bump-on-use + decay), proactive digest endpoint, graph perf fix.
- Provable quality: grounding confidence in SSE + admin quality-trend endpoint.
- Hardening: answer temperature 0.0, char-budget contexts, index migrations,
  email normalization, query length caps, dead code removal.

### Open Memory Hub MVP (2026-09, PR #7)
- **MCP server** at `/mcp` — six scoped memory tools, per-agent identity
  (sha256 token registry), streamable-HTTP with scope normalization.
- **Permissions + access ledger** — per-agent read/write scopes, append-only
  audit log of every authorized call.
- **Erasure receipts** — ownership-checked transitive cascade, Chroma
  verification pass, three honest statuses, MCP `forget_memory` + REST.
- **Import paths** — ChatGPT / Claude / generic / PAM upload with detection,
  dedup, 10k cap, per-item isolation.
- **Benchmark scaffold** — LongMemEval-S + MemoryAgentBench adapters, phased
  runner, no-fabrication guarantee, hygiene fields reserved.
- **ClawHub skill package** — `skills/orivory/` (runbook + examples + tool
  catalog), publishable via `clawhub skill publish` (founder-side step).
- **Hardened compose** — one-shot `migrate` service gating app/celery;
  `mcp_hub` readiness check; healthchecks on all infra.

## Open follow-ups (ranked)

1. **UI**: access-ledger page, upload/import page, erasure-receipts view.
2. **Behavioral REST security tests** (cross-user 404, 201 shape, ledger
   scoping over HTTP) — wiring tests exist; HTTP-level tests are the top gap
   from the final reviews.
3. **LLM judge for benchmarks** (official LongMemEval prompt, version pinned)
   → first real public score after ≥3 judged runs.
4. **Live wiring for benchmark ingest/query** against a running stack.
5. **Ledger retention policy** (unbounded growth under chatty agents) +
   unique index on `(user_id, source_type, source_ref)` for import races.
6. **OpenClaw session-log import** (their memory is local Markdown — same
   generic-JSON path, needs a converter).
7. **Rewind/Limitless adapter** — blocked on a verified export format
   (SQLCipher-encrypted, no official format).
8. **Gemini/Copilot import adapters** (PAM documents the shapes).
9. **Re-revoke `revoked_at` guard; explicit `captured_at` in imports.**
10. **Parent ownership + depth-cap receipts polish** — partially done; see
    code TODOs.

### From claude-mem competitive analysis (see research/CLAUDE_MEM_ANALYSIS.md)
- **Auto-capture for OpenClaw**: an OpenClaw-side hook/integration that
  flows agent session activity into Orivory's ingestion path without manual
  calls (the pattern behind claude-mem's 90K+ stars) — highest-leverage
  counter-move.
- **Compression-before-storage**: optional AI summarize step before memory
  writes (feature-flagged; ~10x token savings is their most-quoted metric).
- **Progressive-disclosure search**: index → details workflow baked into
  MCP tool descriptions; consider a `timeline` tool.
- **Watch**: claude-mem's server-runtime GA plan (#2685) — Docker+pg+redis+
  scopes is Orivory's full-stack lane; land ledger/receipts/benchmark
  differentiators before their GA drops.

## Explicitly out of scope (for now)

Meeting-notes AI (30+ player market), team-first positioning, Celery for
large imports (sync + 20 MiB cap covers v0), donation-based funding.
