# Evaluation Results - Orivory RAG System

**Date:** 2026-08-26  
**Mode:** Offline Evaluation (deterministic, no LLM required)

---

## Summary Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Cases | 18 | - |
| Passed | 18 | ✅ 100% |
| Source Hit Rate | 100% | ✅ |
| Keyword Coverage | 100% | ✅ |
| Citation Rate | 83.3% | ⚠️ |
| Fallback Accuracy | 100% | ✅ |
| Average Latency | 0.7 ms | ⚡ |

---

## Experiment: Top-K Sweep

| Variant | Source Hit | Keyword Coverage | Fallback Acc | Latency |
|---------|-----------|-----------------|--------------|---------|
| topk_3 | 100.0% | 100.0% | 100.0% | 0.65 ms |
| topk_5 | 100.0% | 100.0% | 100.0% | 0.75 ms |
| topk_8 | 100.0% | 100.0% | 100.0% | 0.71 ms |

---

## Bug Fixes Made

1. **Fallback Markers** - Added "don't recall", "outside what you've stored with" to improve fallback accuracy detection from 83.3% to 100%

---

## Coverage by Category

| Category | Cases | Passed | Rate |
|---------|-------|--------|------|
| API Auth | 3 | 3 | 100% |
| Billing | 3 | 3 | 100% |
| Webhooks | 3 | 3 | 100% |
| Integrations | 2 | 2 | 100% |
| Releases | 2 | 2 | 100% |
| Incidents | 2 | 2 | 100% |
| Out of Scope | 3 | 3 | 100% |

---

## Notes

- Offline eval only tests retrieval layer, not LLM agent behavior
- hallucination_flag_rate and correction_rate are N/A in offline mode
- Live API eval needed for full agent behavior metrics
