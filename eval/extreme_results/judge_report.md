# LLM-as-Judge Evaluation Report

**Total Cases:** 30
**Reasoning Cases:** 25
**Pass Rate:** 100.0% (30/30)

## Summary Scores

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 75.0% |
| Reasoning Quality | 59.3% |
| **Overall** | **78.1%** |

## Scores by Difficulty

| Difficulty | Count | Overall | Faithfulness | Reasoning |
|------------|-------|--------|--------------|-----------|
| Extreme | 18 | 73.3% | 100.0% | 50.0% |
| Hard | 7 | 78.3% | 100.0% | 65.0% |
| Easy | 5 | 95.0% | 100.0% | 85.0% |

## Scores by Reasoning Type

- **abstraction_mapping**: 73.3% (1 cases)
- **temporal_ordering**: 78.3% (1 cases)
- **feature_separation**: 73.3% (1 cases)
- **prohibition_inference**: 73.3% (1 cases)
- **conditional_logic**: 78.3% (1 cases)
- **negative_inference**: 73.3% (1 cases)
- **comparative_definition**: 73.3% (1 cases)
- **temporal_numeric**: 78.3% (1 cases)
- **version_comparison**: 73.3% (1 cases)
- **boundary_value**: 78.3% (1 cases)
- **diagnostic_decomposition**: 73.3% (1 cases)
- **state_machine**: 75.8% (2 cases)
- **exception_logic**: 73.3% (1 cases)
- **boolean_logic**: 78.3% (1 cases)
- **constraint_satisfying**: 73.3% (1 cases)
- **tradeoff_reasoning**: 73.3% (1 cases)
- **negation_understanding**: 73.3% (1 cases)
- **logical_inconsistency**: 73.3% (1 cases)
- **causal_chain**: 73.3% (1 cases)
- **implication_chain**: 73.3% (1 cases)
- **order_analysis**: 73.3% (1 cases)
- **edge_case_inference**: 73.3% (1 cases)
- **direct_lookup**: 78.3% (1 cases)
- **numeric_calculation**: 73.3% (1 cases)

## Detailed Results


### ✅ extreme_001

**Query:** If a SEV-1 incident affects authentication and document retrieval, what's the maximum time before we...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_002

**Query:** What happens to my access token if I refresh it exactly at minute 14?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_003

**Query:** Between Starter and Enterprise, which plan is better for a company that needs SSO but has limited bu...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_004

**Query:** If I already revoked my old API key, can I still use it during the grace period?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_005

**Query:** What's the difference between 'retry' and 'manual replay' for webhooks?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_006

**Query:** If I want to use both ChromaDB vector search and BM25, what additional step is required?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_007

**Query:** Can a Pro workspace user access admin endpoints?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_008

**Query:** How many days after a SEV-1 incident should the post-mortem be completed?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 65.0% |
| **Overall** | **78.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_009

**Query:** What should I check if BOTH Redis AND ChromaDB are slow?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_010

**Query:** If I'm on the grace period due to payment failure, can I still ask questions about my existing docum...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_011

**Query:** What version should I downgrade to if I want async ingestion but not the agent trace feature?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_012

**Query:** Why might Stripe sync show wrong billing even if Stripe dashboard looks correct?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_013

**Query:** What's the worst case total time a webhook could take to be delivered?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_014

**Query:** If Celery workers are processing critical ingestion jobs, what should I NOT do when Redis has issues...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_015

**Query:** What's the relationship between OAuth redirect exchange codes and token security?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_016

**Query:** If my webhook endpoint returns 500, will it be retried?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 65.0% |
| **Overall** | **78.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_017

**Query:** Which feature came first: Agent trace diagnostics or hybrid retrieval?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 65.0% |
| **Overall** | **78.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_018

**Query:** Can I configure CORS without SSO?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_019

**Query:** What happens if I exceed my rate limit once, then immediately upgrade to Pro?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_020

**Query:** If CRM metadata is synced, is it embedded into the vector index?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_021

**Query:** Is the order of steps 2 and 3 in API key rotation important?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 50.0% |
| **Overall** | **73.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_022

**Query:** What's the minimum response time for a SEV-2 incident acknowledgment?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 65.0% |
| **Overall** | **78.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_023

**Query:** If I'm on Enterprise, do I automatically get audit logs?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 65.0% |
| **Overall** | **78.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_024

**Query:** What's the maximum number of documents I can have if I'm on Starter and can't upload new ones?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 65.0% |
| **Overall** | **78.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ extreme_025

**Query:** If my document status is 'processing', will vector search find it?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 70.0% |
| Reasoning Quality | 65.0% |
| **Overall** | **78.3%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ fallback_001

**Query:** What is the meaning of life?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 100.0% |
| Reasoning Quality | 85.0% |
| **Overall** | **95.0%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ fallback_002

**Query:** Help me write a love letter...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 100.0% |
| Reasoning Quality | 85.0% |
| **Overall** | **95.0%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ fallback_003

**Query:** What programming language should I learn first?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 100.0% |
| Reasoning Quality | 85.0% |
| **Overall** | **95.0%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ fallback_004

**Query:** Can you book a flight for me?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 100.0% |
| Reasoning Quality | 85.0% |
| **Overall** | **95.0%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)

### ✅ fallback_005

**Query:** What's the weather like in Tokyo?...

| Metric | Score |
|--------|-------|
| Faithfulness | 100.0% |
| Answer Relevancy | 100.0% |
| Reasoning Quality | 85.0% |
| **Overall** | **95.0%** |

**Judge Reasoning:** Heuristic evaluation (LLM not available)