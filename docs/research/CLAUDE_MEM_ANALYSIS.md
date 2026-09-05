# claude-mem — Competitive Analysis

**Date:** 2026-09-05 · **Method:** desk research via Exa (primary sources: the
[claude-mem repo](https://github.com/thedotmack/claude-mem) README/architecture
docs/issues, [npm page](https://www.npmjs.com/package/claude-mem),
[docs.claude-mem.ai](https://docs.claude-mem.ai/architecture/hooks-architecture),
[cmem.ai](https://cmem.ai/pricing), tracker pages: [Repository Radar](https://repositoryradar.dev/repo/thedotmack/claude-mem), [Claracle](https://claracle.com/repo/thedotmack-claude-mem/), [GStars](https://www.gstars.dev/repo/thedotmack-claude-mem),
[Mnemoverse comparison](https://mnemoverse.com/docs/library/memory-mcp-servers-compared),
[Context Cloud comparison](https://contextcloud.pro/blog/best-mcp-memory-servers-for-teams/),
[DEV 4-way](https://dev.to/labyrinthanalytics/ai-memory-for-claude-an-honest-4-way-comparison-2p34),
[Serenities comparison](https://serenitiesai.com/articles/ai-agent-memory-why-2026-is-the-year-of-persistent-context)).
Vendor/self-reported numbers marked [vendor]. ~25 sources.

---

## 1. What claude-mem is, precisely

**claude-mem** (thedotmack, Apache-2.0, TypeScript/Bun, npm `claude-mem`,
v13.x) is a **session-capture and compression system for coding agents**.
Install is one command (`npx claude-mem install`) or a Claude Code plugin
(`/plugin install claude-mem`). It also ships an **OpenClaw gateway
installer** (`curl -fsSL https://install.cmem.ai/openclaw.sh | bash`) and
installers for Gemini CLI and OpenCode.

**Architecture** (from [hooks-architecture](https://docs.claude-mem.ai/architecture/hooks-architecture)
+ [search-architecture](https://github.com/thedotmack/claude-mem/blob/main/docs/public/architecture/search-architecture.mdx)):

1. **5 lifecycle hooks** — SessionStart (worker start + context inject),
   UserPromptSubmit, PostToolUse (capture every tool I/O), Stop (session
   summary), SessionEnd. Hooks are fire-and-forget HTTP (2s timeout,
   non-blocking).
2. **Worker service** (Express, per-user port) — processes observations
   asynchronously: **AI compression** of tool I/O into structured
   observations via the Claude Agent SDK / Gemini / OpenRouter.
3. **Storage** — SQLite + FTS5 (keyword) + ChromaDB (vector, hybrid recall).
4. **MCP server** — a thin wrapper (~312 lines) exposing 4 tools over the
   worker HTTP API: `search`, `timeline`, `get_observations`, `__IMPORTANT`
   (workflow guidance).
5. **Viewer UI** — real-time memory stream at localhost:37777.

The signature mechanic is **progressive disclosure**: a 3-layer search
workflow (search → index with IDs ~50-100 tokens → timeline → full details
only for filtered IDs) that yields ~10x token savings and structurally
prevents wasting tokens.

## 2. Traction & trajectory

| Signal | Value | Source |
|---|---|---|
| GitHub stars | **92-93K** (2026-08; 1K on 2025-12-10 → 92K by 2026-08, ~+11K/mo at peak, +656/wk current) | Repository Radar, Claracle, GStars |
| npm downloads | ~16.5-19K/week | npm page, Repository Radar |
| Contributors | 139 (bus factor 2, top author 45% of 6-mo commits) | Repository Radar |
| Release cadence | weekly; 2,009 commits; 94% issues closed ~2d | Repository Radar |
| Cloud | CMEM Pro $30/mo solo; Team $333/seat/mo (FDE onboarding) | cmem.ai/pricing |

Growth flattened in W30 (+255) then recovered (+771 W31) — big but no longer
hypergrowth.

## 3. Feature inventory vs Orivory

| Feature | claude-mem | Orivory | Verdict |
|---|---|---|---|
| Automatic session capture | ✅ 5 lifecycle hooks, zero-touch | ❌ manual `add_memory` / imports only | **adopt** |
| AI compression before storage | ✅ (~10x token savings) | ❌ raw content capped at 10k chars | **adopt** |
| Progressive-disclosure search workflow | ✅ 3-layer (index→timeline→details) | ⚠️ single search tool | **adopt** |
| MCP server | ✅ 4 read tools (search/timeline/get_observations) | ✅ 6 tools (read+write+forget) | parity-ish |
| **Per-agent scoped tokens** | ⚠️ API-key scopes exist in server-beta, scope middleware mismatch bug (#2428) | ✅ `memory:read`/`memory:write` per agent, sha256 registry, instant revoke | **Orivory wins** |
| **Access ledger ("which AI saw what")** | ❌ none (Viewer UI shows stored memory, not agent access) | ✅ append-only `memory_access_logs` | **Orivory wins** |
| **Erasure receipts (verified RTBF)** | ❌ delete exists in cloud tier, no verification/receipts | ✅ cascade + verification pass + receipt | **Orivory wins** |
| **Knowledge graph** | ❌ | ✅ entities/relations/clusters | **Orivory wins** |
| **Import from other providers** | ❌ (captures its own sessions only) | ✅ ChatGPT/Claude/Gemini/Copilot/OpenClaw/generic/PAM | **Orivory wins** |
| **Benchmarks** | ❌ (evals/swebench exists — SWE-bench, not memory benchmarks) | ✅ LongMemEval-S + MAB scaffold | **Orivory wins** |
| Client reach | ✅ Claude Code, OpenClaw, Codex, Gemini CLI, Hermes, Copilot, OpenCode (8 agents via CMEM Cloud) | ⚠️ any MCP client via /mcp; OpenClaw skill + config docs | **claude-mem wins (packaged integrations)** |
| Auto-capture friction | ✅ zero-touch (hooks fire automatically) | ❌ agent/API must explicitly call | **claude-mem wins (biggest gap)** |
| Token-efficiency UX | ✅ progressive disclosure | ❌ | **claude-mem wins** |
| Team features | ❌ OSS single-user; Team = $333/seat cloud | ✅ workspaces (full stack) | Orivory wins (full stack) |
| Community | ✅ 139 contributors, 90K+ stars, 19K npm/wk | ❌ pre-launch | claude-mem wins |

## 4. Documented weaknesses (user complaints, sourced)

- **Process/memory leaks** — orphaned Claude subagents accumulating
  (220+ processes, 7.8GB RAM/22GB swap; recurred in v9.0.4: 209 orphans,
  2.5-3.5GB RAM) ([#650](https://github.com/thedotmack/claude-mem/issues/650),
  [#701](https://github.com/thedotmack/claude-mem/issues/701)).
- **Unbounded tool_output → infinite overflow loop with data loss** — no
  context budget management in the observer ([#2468](https://github.com/thedotmack/claude-mem/issues/2468)).
- **Server-beta structural gaps** — auth scope mismatch (#2428), no mode
  loaded on boot (#2443), unsalted SHA-256 API keys (#2541), no e2e tests
  (#2550), no uninstall path (#2568) — tracked in
  [server-runtime GA plan #2685](https://github.com/thedotmack/claude-mem/issues/2685).
- **Single-user OSS** — no shared workspaces, RBAC, or attribution
  ([Context Cloud comparison](https://contextcloud.pro/blog/best-mcp-memory-servers-for-teams/)).
- **Cloud sync uploads prompt text + narratives to cmem.ai** — privacy
  tradeoff documented but real
  ([cloud-sync docs](https://docs.claude-mem.ai/cloud-sync)).

## 5. Threat assessment

**Confirmed expansion toward a general memory hub** — three independent
signals:

1. **Multi-agent support shipped**: Claude Code + OpenClaw gateway installer
   + Gemini CLI + OpenCode + Codex + Hermes + Copilot (README + installers).
2. **Server-runtime GA plan** ([#2685](https://github.com/thedotmack/claude-mem/issues/2685)):
   standalone server with **Docker + Postgres + Redis + API keys with
   scopes + scopes middleware + argon2id hashing + Docker restart policies
   + Viewer UI on the server** — that is Orivory's full-stack lane. The plan
   explicitly targets "the same matrix as the worker" before dropping beta.
3. **CMEM Cloud (cmem.ai)**: hosted sync + private MCP link across 8
   agents/IDEs; Team tier with "per-project scopes & isolation, roles,
   access control & audit" — the governance positioning Orivory owns, now
   appearing in their marketing copy.

**Threat level: HIGH, 2-3 quarters.** Their #2685 plan is a direct roadmap
toward a self-hosted governed hub. What they will likely NOT have soon:
knowledge graph, cross-provider imports, erasure receipts, benchmarks, and
the ledger-as-product UX — Orivory's differentiation window is those.

**Counter-signal (their advantage that is hard to copy fast)**: hook-based
auto-capture is the single biggest UX moat. It eliminates capture friction —
the #1 abandonment cause in our own user research. Orivory currently has no
equivalent.

## 6. Implications for Orivory

1. **Adopt: hook-based auto-capture** — build an OpenClaw-side capture
   integration (their OpenClaw installer proves the pattern works) so agent
   sessions auto-flow into Orivory's import/ingestion path. This is the
   single biggest UX gap and attacks our own #1 abandonment-cause finding.
2. **Adopt: compression-before-storage** — add an optional AI-compression
   step (summarize tool output before storing) behind a feature flag; the
   10x token-savings claim is their most-quoted metric.
3. **Adopt: progressive-disclosure search guidance** — bake the
   index→details workflow into MCP tool descriptions (cheap, pure UX) and
   consider a `timeline` tool.
4. **Adopt: npx/curl one-command installer** for the lite image (we have
   `make quickstart`; competitors have `npx claude-mem install`).
5. **Do NOT chase**: solo-dev session compression speed (their home turf,
   139 contributors); out-compressing them is not winnable near-term.
6. **Position against their governance gap**: they have no permissions
   model that works, no ledger, no receipts, no graph, no imports. Market
   the ledger + receipts as the anti-"memory Black Box" story — especially
   at teams, where CMEM Cloud charges $333/seat.
7. **Watch #2685 closely** — the server-runtime GA plan is the moment
   claude-mem becomes a direct hub competitor (Docker+pg+redis+scopes).
   Time Orivory's differentiator launches (ledger UI, receipts UX, public
   benchmark) to land before their GA drops.
8. **Their weakness is our proof point**: process leaks, overflow loops,
   and unsalted hashes are recurring. Orivory's Python/FastAPI stack with
   proper service isolation, parameterized queries, and argon2-class
   patterns is structurally less leak-prone — worth a public reliability
   comparison once benchmarks are public.
9. **License parity**: both Apache-2.0/MIT-friendly — no license wedge, so
   differentiation must come from features + governance, not licensing.
10. **OpenClaw is the contested ground**: they ship a curl installer for
    OpenClaw gateways; our OpenClaw skill + config docs exist but have no
    auto-capture. Closing the auto-capture gap on OpenClaw specifically is
    the highest-leverage counter-move.
