# MindLayer Rebrand Notes

This document captures the **SupportMind → MindLayer** brand pivot that took place
on 2026-06-15. The pivot is part of repositioning the project from a multi-tenant
SaaS support RAG into a **Personal AI Second Brain**.

The rename was done in two passes:

- [scripts/_bulk_rename_docs.ps1](../scripts/_bulk_rename_docs.ps1) — `.md` / `.ipynb`
- [scripts/_bulk_rename_py.ps1](../scripts/_bulk_rename_py.ps1) — `.py` + file renames

The PowerShell scripts are kept in `scripts/` as a historical record. They can be
deleted once the team is confident the new brand has fully propagated.

---

## Brand mapping

| Old | New | Notes |
| --- | --- | --- |
| `SupportMind` | `MindLayer` | Brand name, used in docs, prompts, app titles |
| `supportmind.local` | `mindlayer.local` | Default email domain |
| `supportmind-demo@example.com` | `mindlayer-demo@example.com` | Demo account email |
| `app.supportmind.example` | `app.mindlayer.example` | Default CORS / frontend origin in tests |
| `supportmind-prod-minio` | `mindlayer-prod-minio` | MinIO key placeholder in test fixtures |
| `X-SupportMind-Signature` | `X-MindLayer-Signature` | Webhook signature header in sample docs |
| `author: "supportmind"` | `author: "mindlayer"` | Prompt template author metadata |

## File renames

| Old path | New path |
| --- | --- |
| `eval/supportmind_offline_eval.py` | `eval/mindlayer_offline_eval.py` |
| `eval/supportmind_eval_dataset.json` | `eval/mindlayer_eval_dataset.json` |

## LLM prompt template rewrites

The prompt templates in [app/agents/prompts/versions.py](../app/agents/prompts/versions.py)
were updated to reflect the new role:

| Prompt | Old role | New role |
| --- | --- | --- |
| `ROUTER_V1` | "SupportMind's intent router. Default to `rag`." | "MindLayer's intent router. Default to `recall`." |
| `ROUTER_V2` | Same as above with stricter JSON | New intents: `recall`, `save_note`, `web_search` |
| `ANSWER_V1` | "SupportMind's support assistant. Cite [Source N]." | "MindLayer, a personal AI second brain. Cite [Source N]." |
| `ANSWER_V2` | Same as V1 with chain-of-thought | Same with CoT |

The fallback message changed from
`"I don't know based on the available SupportMind documentation."` to
`"I don't recall that in your memories. Would you like me to save a note about it?"`.

`EVALUATOR_*` and `HALLUCINATION_*` prompts had no SupportMind mention in their
template text, so only the `author` metadata was updated.

## What was intentionally NOT renamed

- **DB schema, table names, column names** — out of scope for the brand pivot.
  Future migrations can rename them; the codebase does not reference the old
  brand as identifiers in the DB layer.
- **Class / function / variable names in `app/`** — they don't contain the old
  brand; they use generic terms like `Document`, `Conversation`, `Message`.
- **Git history** — left as-is. The pre-pivot commits are still searchable.

## Intentionally kept SupportMind references

The following files still contain `SupportMind` (or `supportmind`) by design:

- `scripts/_bulk_rename_docs.ps1` and `scripts/_bulk_rename_py.ps1` — the rename
  scripts themselves contain the literal strings as find patterns.
- `notebooks/rag_analysis.ipynb` — will be regenerated or rewritten in Phase 7.
- `tests/integration/test_redis_live.py`, `tests/integration/test_minio_live.py`
  — test fixtures use SupportMind-only key prefixes and payloads. Will be
  refreshed in Phase 7 alongside the sample data.
- `tests/eval/test_eval_metrics.py`, `tests/api/test_chat_streaming.py` —
  test fixtures only, not user-facing.
- `eval/results/latest_report.json` — generated artifact from a previous run,
  will be overwritten on the next `python eval/run_eval.py` invocation.
- `.env` — the local development env file. The bulk rename scripts intentionally
  skipped this file because it may contain real secrets. After pulling the
  rebrand, manually update `EMAIL_FROM`, `EMAIL_FROM_NAME`, and any other
  SupportMind-specific values to their MindLayer equivalents (see
  `.env.example` for the new defaults).
- `docs/REBRAND_NOTES.md` — this file.

## Verification

To confirm no stray references remain in production code or docs:

```bash
# Should match only the files in "Intentionally kept" section above
grep -ri "supportmind" \
  --exclude-dir=.venv --exclude-dir=.git --exclude-dir=__pycache__ \
  --exclude-dir=node_modules \
  --exclude="*_bulk_rename*.ps1" \
  --exclude="REBRAND_NOTES.md"
```

Expected: no results.
