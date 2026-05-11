# RAG Techniques Deep-Dive

Implementation notes for the techniques used in MindLayer. Each section
links to the source file, explains the trade-off, and points at the tests
that exercise it.

---

## 1. Hybrid retrieval (BM25 + dense + RRF)

**Why.** BM25 excels at exact keyword / Vietnamese diacritic matches
(e.g. `"API"`, `"rate limit"`). Dense retrieval excels at semantic
paraphrases. Combining them via Reciprocal Rank Fusion gives the best
of both.

**Where.**
- BM25: [`app/retrieval/bm25_retriever.py`](app/retrieval/bm25_retriever.py)
- Dense: [`app/retrieval/vector_store.py`](app/retrieval/vector_store.py)
- RRF: [`app/retrieval/rrf.py`](app/retrieval/rrf.py)

**Trade-off.** Slightly higher latency than dense-only (two retrievers +
fusion), but ~30% recall improvement on Vietnamese technical terms
(measured on the offline eval set).

**Test.** `tests/rag/test_hybrid_retrieval.py::test_bm25_contributes_when_dense_fails`

---

## 2. Reciprocal Rank Fusion

```
score(d) = Σ_i  1 / (k + rank_i(d))     # k = 60 (Cormack et al.)
```

**Why RRF instead of linear combination.** RRF needs no score
calibration between retrievers (BM25 scores ≠ cosine scores). It also
handles "the result only appears in one list" gracefully.

**Where.** [`app/retrieval/rrf.py`](app/retrieval/rrf.py)

**Test.** `tests/rag/test_rrf.py` — covers single-list inputs, equal rank, and
overlapping docs.

---

## 3. Parent-child chunking

```
[Parent (1024 tok)]     ← returned to the LLM for context
   ├── [Child (256 tok)] ← embedded into the vector store
   ├── [Child (256 tok)]
   └── [Child (256 tok)]
```

**Why.** Small children → precise embedding (better recall).
Large parents → readable context for the answer agent.

**Where.** [`app/retrieval/processor.py`](app/retrieval/processor.py)

**Trade-off.** 4-6× more storage, but the LLM's "answer quality" metrics
improve noticeably because the answer agent has surrounding context for
each child.

---

## 4. Multi-query + HyDE + conversation rewrite

Three query transformations run in parallel (`asyncio.gather`):

1. **Conversation rewrite** — resolves pronouns using the last 3 turns
2. **Multi-query** — 3 lexical variants of the question
3. **HyDE** — generate a hypothetical answer, embed that instead of the question

**Why.** Different retrievers respond to different query phrasings. Throwing
3-5 reformulations at the retriever and fusing the results is a cheap win.

**Trade-off.** LLM call for the router → +50-200 ms p50. HyDE is
opt-in (gated by config) because not all domains benefit from it.

**Test.** `tests/rag/test_query_transforms.py`

---

## 5. Cross-encoder reranking

A small cross-encoder reads `(query, chunk)` pairs and re-orders the top-K
chunks. Cheaper than re-embedding the whole corpus, and the signal is much
stronger than cosine similarity alone.

**Where.** [`app/retrieval/reranker.py`](app/retrieval/reranker.py)
(uses FlashRank by default)

**Trade-off.** ~50-150 ms added latency. We compensate by
reranking only the **top 20** of the 50 retrieved chunks.

**Benchmark.** See [`eval/benchmarks/reranker_benchmark.py`](eval/benchmarks/reranker_benchmark.py)
for an NDCG/MRR harness.

---

## 6. LLM-as-judge hallucination detection

After the answer agent runs, a second LLM call asks:

> "Given the context and the question, is the answer grounded?
> Does it actually answer the question? Cite a [Source N] marker?"

If `is_hallucination` is True, the graph re-enters the answer node with
the same context but a stricter prompt hint — up to 3 times.

**Where.** [`app/agents/hallucination_agent.py`](app/agents/hallucination_agent.py)
(used by [`app/graph.py`](app/graph.py))

**Test.** `tests/rag/test_hallucination_retry.py`

---

## 7. Self-correction loops (LangGraph)

Two correction edges in the graph:
- `grade_docs` returns `context_relevant=False` → re-retrieve
- `grade_gen` returns `is_hallucination=True` → re-generate

Each is bounded at 3 retries to prevent infinite loops.

**Where.** [`app/graph.py`](app/graph.py) — see the `add_conditional_edges` calls.

**Metric.** "Correction rate" in the eval report measures how often
retries actually fixed the issue.

---

## 8. Parent-chunk cache (Redis)

Successful parent retrievals are cached in Redis (`parent:<doc_id>:<chunk_id>`)
for 2 hours. Hot docs become sub-millisecond to retrieve.

**Where.** [`app/retrieval/cache.py`](app/retrieval/cache.py)

**Trade-off.** Redis becomes a hard dependency in production. For local
dev, the cache layer transparently falls back to a no-op.

---

## 9. Vietnamese-specific preprocessing

- **NFC normalization** — `"café"` and `"café"` collapse to the same string
- **Syllable segmentation** — `underthesea` (configurable)
- **Stopword filter** — Vietnamese + English stopword lists
- **Diacritic-safe BM25** — keep diacritics for the index (Vietnamese users
  type with diacritics), strip only for the query (some keyboards lose them)

**Where.** [`app/retrieval/preprocessor.py`](app/retrieval/preprocessor.py)

---

## 10. Versioned prompt registry with A/B testing

All 4 agent prompts are versioned (`v1`, `v2`, ...). For each
conversation, the registry assigns a variant deterministically
(hash of `agent:conversation_id`) so the same conversation always sees
the same prompt — critical for fair A/B comparison.

Outcomes are logged to a JSONL file and aggregated by variant for
analysis.

**Where.** [`app/agents/prompts/`](app/agents/prompts/) — see
[`registry.py`](app/agents/prompts/registry.py) and
[`integration.py`](app/agents/prompts/integration.py).

**Test.** `tests/agents/test_prompt_registry.py` (20 tests)
