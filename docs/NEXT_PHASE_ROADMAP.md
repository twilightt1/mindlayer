# MindLayer — Next Phase Roadmap

> **Purpose**: turn MindLayer from "a document-chat RAG with a memory layer
> bolted on" into a product that genuinely behaves like a **Personal AI
> Second Brain** — one brain, many ways to ask, that remembers across
> conversations and gets smarter the more you use it.
>
> This roadmap is **evidence-grounded**: every problem below cites the file
> and line where it lives today, so the work is verifiable rather than
> aspirational. Phases are ordered by dependency — fix the spine before
> growing the brain.

**Status legend**: 🔴 broken / blocking · 🟠 incomplete · 🟢 works today ·
🔵 net-new

---

## Implementation status (updated as phases land)

| Phase | Status | Notes |
| :--- | :--- | :--- |
| **P0 — Close the spine** | ✅ done | Connector-synced memories now embed; reindex/backfill task + admin endpoint added. |
| **P1.1 — Documents → memories** | ✅ done | Hybrid granularity (1 doc Memory + N passage Memories); cleanup on doc/conversation delete. |
| **P1.2 — Connectors** | ✅ done | web_clipper hardened (no more junk-memory on failure); real RSS connector (feedparser); `bs4`+`feedparser` declared. |
| **P1.3 — Save note from chat** | ✅ done | `save_note` router intent (regex fast-path + LLM) → `save_note` graph node → memory + confirmation. |
| **P2.1 — Salience loop** | ✅ done | Bump on used-in-answer (asymptotic toward 1.0) + daily decay task; `recall_count`/`last_used_at` columns (migration `b2c3d4e5f6a7`). |
| **P2.2 — Proactive digest** | ✅ done | `GET /api/v1/memories/digest`: recent-window themes + "on this day" resurfacing. No LLM cost. |
| **P2.3 — Graph surface** | ✅ done (scoped) | Graph read API already existed (snapshot/clusters/related/memories); did the entity-match perf fix (DB-side ILIKE instead of Python loop over 100 rows). |
| **P3 — Provable quality** | ✅ done | Per-answer grounding confidence (in SSE `done` + persisted in `agent_trace.grounding`); admin `GET /api/v1/admin/quality/trend` aggregates citation/grounded/self-correction/confidence/latency from persisted traces. |
| **P4 — Hardening** | ✅ done (safe set) | `ANSWER_TEMPERATURE=0.0` for factual answers; `ChatRequest.query` max_length; email lowercased at the schema boundary; deleted dead code (`query_processor`, `reranker_agent`); char-based context budget; additive index migration `c3d4e5f6a7b8`. Deferred: `parent_id` JSONB→column (needs backfill). |

> **All roadmap phases (P0–P4) are implemented at the unit level.** Verified
> after each phase with `ruff check app tests` + the CI-safe pytest suite
> (211 passing). **Not yet done:** a live integration smoke pass
> (Postgres/Redis/Chroma/Celery) and applying the three new migrations
> (`b2c3d4e5f6a7`, `c3d4e5f6a7b8`) — `alembic upgrade head` is required before
> the salience columns and new indexes exist in a running database.

---

## 0. The core finding

The codebase has **two parallel retrieval worlds** that ingest separately and
only meet at answer-assembly time:

| | Document-chat world | Personal Memory world (the "second brain") |
| --- | --- | --- |
| Stored in | `document_chunks` (scoped per conversation) | `memories` (scoped per user) |
| Vector index | Chroma collection **per conversation** + in-process BM25 | Chroma collection **`mindlayer_memories`**, filtered by `user_id` |
| Enters via | file upload into one conversation | `POST /api/v1/memories` + connector sync |
| Gets embedded | `tasks/ingestion_tasks.py::process_document` ✅ | **only the manual `POST` path** — see P0 |
| Visible across conversations | ❌ no | ✅ yes (by design) |

They are merged for answering in
[`app/agents/context_merge_agent.py:33`](../app/agents/context_merge_agent.py)
in priority order `document → personal_memory → knowledge_graph`. **The
architecture is correct.** What's missing is that the second-brain world is
not fully wired end-to-end, and the document world never *becomes* memory.

Three concrete gaps make the product feel like "chat-with-PDF + a separate
note app" instead of one brain. They are P0–P1 below.

---

## P0 — Close the spine (≈1–2 days) 🔴

Without this, memories captured from connectors are written to Postgres but
are **invisible to recall**. This is a correctness bug, not a feature.

### P0.1 — Connector-synced memories are never embedded 🔴

**Evidence**: `upsert_memory_sync()` exists at
[`app/retrieval/memory/vector_store.py:204`](../app/retrieval/memory/vector_store.py)
but a repo-wide search shows **no caller**. The sync path
[`app/ingestion/dispatcher.py::_persist_item`](../app/ingestion/dispatcher.py)
(≈ lines 144–168) creates a `Memory` row and a `MemorySource` link and
enqueues graph extraction — but never embeds the memory into ChromaDB. Only
the manual `POST /api/v1/memories` path embeds, via
[`app/api/v1/memories.py:62`](../app/api/v1/memories.py).

**Impact**: everything synced from Gmail / Drive / Notion / web clipper lands
in Postgres but cannot be found by vector recall — the exact job a second
brain exists to do.

**Fix**:
1. In `_persist_item`, after a memory is added or updated, schedule a
   best-effort embed. Because the dispatcher runs in an async request context
   today and the embed has a sync and async variant, prefer the async
   `upsert_memory` so it shares the request event loop; fall back to logging
   on failure (Postgres remains source of truth).
2. Collect the affected `memory_id`s and embed **after** `_finalize` commits,
   mirroring how `graph_memory_ids` is already deferred until after commit
   (`dispatcher.py:105`). Do not embed uncommitted rows.
3. Keep it best-effort: wrap per-memory so one embedding failure does not fail
   the whole sync.

**Acceptance**: sync a source with N items → `mindlayer_memories` Chroma
collection grows by N → `POST /api/v1/memories/recall` returns them.

### P0.2 — No reindex / backfill task 🔴

**Evidence**: the code itself flags this as missing —
[`app/api/v1/memories.py:59`](../app/api/v1/memories.py) says *"the recall
pipeline can still rebuild the index from Postgres later (see Phase 3.5
backlog: bulk reindex task)"*. No such task exists.

**Impact**: if ChromaDB is wiped, restarted empty, or memories predate P0.1,
there is no way to repopulate vectors. The "Postgres is source of truth"
guarantee is only real if it can be replayed.

**Fix**: add a Celery task `reindex_user_memories(user_id, *, only_missing=True)`
in a new `app/tasks/reindex_tasks.py`:
- Page through `Memory` rows for the user (reuse the shared sync engine from
  `app/tasks/db.py`).
- For `only_missing`, check Chroma membership in batches and embed the gaps;
  for a full rebuild, re-embed all.
- Batch embeds via `embed_texts_sync` (respects `EMBED_BATCH_SIZE`).
- Expose an admin trigger: `POST /api/v1/admin/memories/reindex`.

**Acceptance**: wipe the Chroma memory collection → run the task → recall works
again with no data loss.

### P0.3 — Wire `upsert_memory_sync` into Celery graph path (consistency) 🟠

**Evidence**: `tasks/graph_tasks.py` builds the knowledge graph for a memory
but does not embed it; embedding currently only happens on the API thread.
For connector items that are large, embedding on the request path can be slow.

**Fix**: once P0.1 + P0.2 land, standardize on **one** place that owns
"memory persisted → embed + graph". Prefer enqueuing both embed and graph from
the same post-commit hook so the two indexes never diverge.

---

## P1 — Unify the two worlds + make capture a daily habit (≈1–2 weeks) 🟠

This is where MindLayer stops being two apps and becomes one brain.

### P1.1 — Documents should *become* memories 🟠

**Evidence**: `process_document`
([`app/tasks/ingestion_tasks.py`](../app/tasks/ingestion_tasks.py)) writes
`document_chunks` and a per-conversation Chroma collection, but never creates a
`Memory`. A PDF uploaded in conversation A is invisible in conversation B.

**Decision required** (see §Strategic decision): the recommended path is that
finishing ingestion also creates a `Memory` (source_type `file_upload`)
pointing back at the document, embedded into `mindlayer_memories`. Then upload
= permanent recall, askable from anywhere.

**Fix (recommended variant)**:
1. At the end of `_ingest`, create one summary-level `Memory` per document
   (title = filename, content = document summary or first parent chunk,
   `source_ref` = document id), or one memory per parent chunk if granular
   recall is wanted.
2. Embed via the P0 path.
3. Keep `document_chunks` as the high-fidelity citation layer; the `Memory`
   row is the cross-conversation handle.

**Acceptance**: upload a doc in conversation A, ask about it in conversation B
→ it is recalled and cited.

### P1.2 — One excellent connector instead of six stubs 🟠

**Evidence**: the dispatcher has an explicit stub branch —
[`app/ingestion/dispatcher.py:71`](../app/ingestion/dispatcher.py) catches
`NotImplementedError` with the note *"This connector is a stub in Phase 2 v0."*
Several connectors under `app/ingestion/connectors/` validate config and shape
items but do not perform real fetches.

**Why it matters**: an empty second brain is never used. Breadth of *daily*
capture is the retention moat, not breadth of half-built connectors.

**Fix**: pick the two lowest-friction, highest-frequency capture paths and make
them production-grade end to end:
- **Web clipper** (`web_clipper.py`) — already the closest to complete.
- **RSS** (`source_type` already reserved in `SOURCE_TYPES`,
  [`app/models/source.py:54`](../app/models/source.py)) — cheap, high-volume,
  habit-forming.

Harden: incremental sync via `sync_cursor`, dedup via
`MemorySource(source_id, item_ref)` (add the composite index noted in the data
review), and per-item error surfacing (already modeled in `SyncResult`).

### P1.3 — "Save note" from chat 🟠

**Evidence**: the rebrand introduced a `save_note` intent
([`docs/REBRAND_NOTES.md:44`](REBRAND_NOTES.md)) and the fallback answer
offers *"Would you like me to save a note about it?"*. But the compiled graph
only routes `rag | summarize | chitchat`
([`app/agents/graph.py:102`](../app/agents/graph.py)) — `save_note` is not a
node.

**Fix**: add a `save_note` branch: router classifies intent → a `save_memory`
node creates a `Memory` (source_type `conversation_excerpt`) from the user's
turn → embed + enqueue graph. Stream a confirmation event over SSE.

**Acceptance**: in chat, "remember that I decided to use pgvector" creates a
recallable memory.

---

## P2 — Make it get smarter over time (≈3–4 weeks) 🔵

This is the difference between a vector database and a *brain*.

### P2.1 — Salience feedback loop 🔵

**Evidence**: `Memory.salience` is documented as *"a float in [0,1] that the
system can update over time based on usage / recency"*
([`app/models/memory.py:14`](../app/models/memory.py)) and is already consumed
by ranking (`time_decay_score`,
[`app/retrieval/memory/scoring.py:137`](../app/retrieval/memory/scoring.py)).
But the **automatic, usage-driven** update the docstring promises does not
exist: `Memory.salience` is set at creation and can only change via a manual
`PATCH /api/v1/memories/{id}`. Nothing bumps it when a memory is actually
recalled or decays it when a memory goes stale. (Note: `builder.py:268/282`
updates `MemoryEntity` *link* salience, a different field — not the memory's
own salience.)

**Fix**:
- When a memory is recalled and actually used in an answer (it survives into
  `grounding_context_chunks`), bump its salience with a bounded increment.
- Apply gentle decay for memories untouched for a long window (a periodic
  Celery task, reusing the quota-reset beat pattern in
  [`app/tasks/celery_app.py`](../app/tasks/celery_app.py)).
- Record recall counts in `Memory.extra_metadata` for transparency.

**Acceptance**: frequently-recalled memories rank above stale ones for
comparable relevance.

### P2.2 — Proactive surfacing 🔵

The system today is purely reactive (you ask, it answers). A second brain
should also *bring things back*.

**Leverage what already exists**: `captured_at` gives true time-aware recall;
the knowledge graph (`entities` / `relations`) gives topical links.

**Fix**: a digest task that produces, e.g., *"This week you saved 3 things
about Postgres indexing"* and *"6 months ago you read X, relevant to today's
question."* Deliver via a `GET /api/v1/digest` endpoint first (UI-pull), email
later (the SendGrid path already exists).

### P2.3 — Knowledge graph as a user-facing surface 🔵

**Evidence**: `app/api/v1/entities.py` already exposes `graph/snapshot`,
`graph/clusters`, and `graph/related/{entity}`. Today these are mostly
internal plumbing for the `graph_context_agent`.

**Fix**: make the graph explorable — "show me how *Project Atlas*, *Mom*, and
*asyncio* connect across my memories." Almost no consumer note app offers this;
it is a genuine differentiator. (Pair with the entity-matching performance fix
from the RAG review — move casefold matching out of Python into a DB-side
query.)

---

## P3 — Quality you can prove (parallelizable) 🟢→🔵

The eval harness already exists ([`eval/`](../eval)); the work is to surface it
as a *trust* feature rather than a one-off script.

- **Quality trend endpoint**: `GET /api/v1/admin/quality/trend` over time —
  source-hit-rate, citation-rate, hallucination-flag rate, self-correction
  rate. The data is already produced by the observability layer
  (`app/observability/`); it just needs aggregation and exposure.
- **Per-answer grounding confidence**: surface "this answer draws on memories
  X, Y" with a confidence signal. The `agent_trace` already carries the
  grounding chain; expose it in the `done`/`trace` SSE events.
- **Cost trend**: the cost ledger (`app/observability/cost.py`) is populated;
  add a windowed trend to the existing `/api/v1/admin/ai-costs`.

Why this is strategic: "an AI you can trust because it cites your own sources
and measures its own quality" is the wedge against generic chat-with-notes.

---

## P4 — Hardening carried over from the code review

These are not second-brain features but they gate production trust. (Severity
from the deep review; CRITICAL items #1–#7 were already remediated — see
[CHANGELOG.md](../CHANGELOG.md).)

| Area | Item | Status |
| --- | --- | --- |
| RAG quality | Answer agent used `LLM_TEMPERATURE=0.7` — too high for factual RAG | ✅ `ANSWER_TEMPERATURE=0.0` ([`app/config.py`](../app/config.py)) |
| RAG cost | HyDE text generated but never used (dead cost) | ✅ deleted `query_processor.py` (entirely unused) |
| RAG cost | `reranker_agent` defined but not wired into the graph | ✅ deleted `reranker_agent.py` |
| Context | No input token budget before the LLM call — large contexts silently truncated | ✅ char-based budget in [`context_merge_agent.py`](../app/agents/context_merge_agent.py) |
| Data model | Missing indexes: `documents(conversation_id, status)`, GIN on `memories.tags`, `memory_sources(source_id, item_ref)`, `messages(role, created_at)` | ✅ migration `c3d4e5f6a7b8` |
| Auth | Email not normalized to lowercase → unique index bypass | ✅ schema validator + OAuth path lowercased |
| API | `ChatRequest.query` had no `max_length` (cost / DoS) | ✅ `max_length=10_000` |
| Data model | `parent_id` stored inside JSONB instead of a real indexed column | ⬜ **deferred** — needs chunker/ingestion/BM25 changes + data backfill |

---

## Strategic decision: unify or keep separate? — RESOLVED: unify

The most consequential choice was whether documents and memories live in one
store. **Decision taken: unify.** P1.1 makes every ingested document also
project into the `memories` store (hybrid granularity: 1 document memory + N
passage memories), so a doc uploaded in one conversation is recallable from any
conversation. A conversation is now effectively a *view* over memories, which is
the "one brain, many ways to ask" model the README promises.

---

## Sequencing summary (all phases implemented)

```text
P0  Close the spine            ▸ connectors embed + reindex task          ✅ done
P1  Unify worlds + capture     ▸ docs→memories, web_clipper+RSS, save     ✅ done
P2  Smarter over time          ▸ salience loop, digest, graph perf fix    ✅ done
P3  Provable quality           ▸ trend + grounding confidence             ✅ done
P4  Hardening                  ▸ temperature, indexes, budget, dead code  ✅ done (safe set)
```

**Remaining before production**: apply migrations (`alembic upgrade head`) and a
live integration smoke pass. One item explicitly deferred: `document_chunks.
parent_id` JSONB→column (needs data backfill).

---

## How to verify this roadmap against the code

Each phase's claims are checkable. The fastest spot-checks (expectations
reflect the **current** state — P0/P1 done, P2 pending):

```bash
# P0.1 (DONE) — connector sync now embeds; reindex task exists.
grep -rn "index_memories\|upsert_memories_sync" app/ingestion app/tasks
# expect: dispatcher embeds synced memories; reindex_tasks present

# P1.3 (DONE) — save_note is routed in the graph.
grep -n "save_note" app/agents/graph.py        # expect: node + edges present

# P2.1 (DONE) — salience is bumped on used-in-answer + decayed periodically.
grep -rn "bump_salience\|next_salience" app/retrieval app/agents   # expect: present
grep -n "decay_stale_salience" app/tasks/celery_app.py             # expect: beat job

# P2.2 (DONE) — the digest endpoint exists, declared before /{memory_id}.
grep -n "digest" app/api/v1/memories.py        # expect: GET /digest route

# P3 (DONE) — grounding confidence is computed + a quality trend endpoint exists.
grep -rn "compute_grounding_confidence" app/agents            # expect: present
grep -n "quality/trend" app/api/v1/admin.py                   # expect: GET route

# P4 (DONE) — answer temperature lowered; dead code removed; budget added.
grep -n "ANSWER_TEMPERATURE" app/config.py                    # expect: present
test ! -f app/agents/reranker_agent.py && echo "reranker_agent removed"
test ! -f app/retrieval/query_processor.py && echo "query_processor removed"
```

Keep the **Implementation status** table at the top in sync with the code: when
a phase lands, flip its row and update these spot-checks.
