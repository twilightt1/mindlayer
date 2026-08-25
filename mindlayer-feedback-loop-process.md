# MindLayer Feedback Loop Process v1.0

**Document Status:** Active  
**Last Updated:** June 2025  
**Owner:** Product Engineering & Research Quality  
**Review Cycle:** Quarterly  

---

## 1. Overview

### 1.1 Why Feedback Matters

MindLayer's core value proposition is accuracy — researchers trust MindLayer to surface the right evidence from their corpus. That trust is earned and maintained through continuous improvement driven by user signal. Feedback is not a secondary feature; it is the primary mechanism by which MindLayer compounds its intelligence over time.

Without an active feedback loop:

- Citation errors persist indefinitely
- Retrieval failures accumulate without correction
- Confidence scores drift from actual performance
- User trust erodes silently

With an active feedback loop, MindLayer transforms every user interaction into a training signal, creating a compounding advantage that competitors cannot replicate without equivalent engagement.

### 1.2 The Learning Flywheel

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────────┐    │
│   │  User    │───▶│   Feedback   │───▶│  Automatic        │    │
│   │  Query   │    │   Capture    │    │  Classification   │    │
│   └──────────┘    └──────────────┘    └─────────┬─────────┘    │
│         ▲                                      │               │
│         │                                      ▼               │
│         │         ┌──────────────────────────────┐             │
│         │         │                              │             │
│         │         ▼                              ▼             │
│         │  ┌────────────┐              ┌──────────────────┐   │
│         │  │ Eval Set   │◀─────────────│  Manual Review   │   │
│         │  │ Curation   │              │  Queue           │   │
│         │  └─────┬──────┘              └────────┬─────────┘   │
│         │        │                                │             │
│         │        ▼                                ▼             │
│         │  ┌──────────────────────────────────────────────┐     │
│         │  │  Active Learning & Prioritization            │     │
│         │  └──────────────────────┬───────────────────────┘     │
│         │                         │                            │
│         │                         ▼                            │
│         │  ┌──────────────────────────────────────────────┐     │
│         │  │  Model Improvement Pipeline                   │     │
│         │  │  • Reranker Fine-tuning                       │     │
│         │  │  • Prompt Engineering                         │     │
│         │  │  • Retrieval Optimization                    │     │
│         │  └──────────────────────┬───────────────────────┘     │
│         │                         │                            │
│         │                         ▼                            │
│         │                 ┌────────────┐                       │
│         │                 │  Deploy &  │                       │
│         │                 │  Monitor    │                       │
│         │                 └─────┬──────┘                       │
│         │                       │                              │
│         └───────────────────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The flywheel accelerates with volume. Every additional user interaction increases the fidelity of the eval set, which improves model performance, which improves user satisfaction, which generates more interactions.

### 1.3 Competitive Moat Through Feedback

MindLayer's feedback infrastructure creates a **data network effect** that compounds over time:

| Feedback Volume | Competitive Advantage | Measurable Impact |
|----------------|----------------------|-------------------|
| 100 interactions/day | Basic signal detection | Emerging pattern recognition |
| 1,000 interactions/day | Reliable eval sets | Measurable quality improvements |
| 10,000 interactions/day | Training signal density | Top-quartile retrieval accuracy |
| 100,000+ interactions/day | Proprietary intelligence | Defensible quality moat |

Competitors can replicate the architecture but cannot replicate the accumulated proprietary signal. This makes feedback collection a strategic priority, not merely an operational nicety.

---

## 2. Feedback Collection

### 2.1 User Feedback Points

MindLayer captures feedback at four distinct interaction points, each targeting a different quality dimension:

#### 2.1.1 "Report Error" Button

**Trigger:** Available on every answer, prominent placement below the response.  
**Target:** Citation accuracy, hallucination, factual errors  
**User Action:** Opens a structured form with error categorization and free-text description.  
**Data Captured:** Error type, affected citations, severity rating, free-text description  

**Error Categories:**
- `citation_missing` — Relevant source not included in answer
- `citation_wrong` — Citation points to incorrect source or passage
- `citation_misquoted` — Source supports claim but quoted passage is inaccurate
- `hallucination` — Answer contains information not supported by any source
- `outdated` — Answer reflects stale information from sources
- `incomplete` — Answer omits relevant information from sources
- `other` — Category not covered above

**Severity Scale:**
- `P0` — Confident hallucination; could mislead research decisions
- `P1` — Significant error affecting answer correctness
- `P2` — Minor inaccuracy or incomplete citation
- `P3` — Cosmetic issue or preference

#### 2.1.2 Answer Thumbs Up/Down

**Trigger:** Visible on every answer after 3-second dwell time.  
**Target:** Overall answer quality, relevance, and usefulness  
**User Action:** Single tap binary rating.  
**Data Captured:** Rating, query hash, answer ID, session context, timestamp  

**Behavioral Considerations:**
- Thumbs down immediately surfaces the Report Error flow
- Explicit "This answer helped me" confirmation on thumbs up (reduces positive bias)
- Rate-limiting: one rating per answer per user per session

#### 2.1.3 Citation Verification

**Trigger:** Activated when user clicks a citation in-context.  
**Target:** Individual citation accuracy and source relevance  
**User Action:** "Was this citation helpful?" with Yes/No/Report options  

**Verification Outcomes:**
- `citation_helpful` — User confirms citation supports the claim
- `citation_not_relevant` — Citation is tangentially related
- `citation_wrong` — Citation does not support the claim (routes to Report Error)
- `citation_unclear` — Cannot determine relevance without opening source

#### 2.1.4 Confidence Rating

**Trigger:** Prompted after answer delivery for queries in high-stakes domains.  
**Target:** Confidence calibration, over/under-confidence detection  
**User Action:** 1–5 scale rating of how well confidence matched actual accuracy  

**Calibration Targets:**
| Confidence Score | Expected Accuracy | Observed Threshold |
|-----------------|-----------------|-------------------|
| 5 (Very High) | 95%+ | 95th percentile answers |
| 4 (High) | 85–94% | 80th percentile answers |
| 3 (Medium) | 70–84% | 60th percentile answers |
| 2 (Low) | 50–69% | 40th percentile answers |
| 1 (Very Low) | <50% | Bottom 20% answers |

### 2.2 Feedback Data Model

#### 2.2.1 Core Feedback Schema

```json
{
  "feedback_id": "uuid",
  "timestamp": "ISO8601",
  "user_id": "uuid (hashed)",
  "session_id": "uuid",
  "query": {
    "text": "string",
    "hash": "sha256",
    "domain": "string (research_area)",
    "query_type": "factual|conceptual|comparative|list|procedural"
  },
  "answer": {
    "answer_id": "uuid",
    "version": "string",
    "model_used": "string"
  },
  "feedback_type": "thumbs | report_error | citation_verification | confidence_rating",
  "feedback_data": {
    // thumbs
    "rating": 1 | -1,
    // report_error
    "error_categories": ["citation_wrong", "hallucination"],
    "severity": "P0|P1|P2|P3",
    "description": "string",
    "affected_citation_ids": ["uuid"],
    // citation_verification
    "citation_id": "uuid",
    "verification_outcome": "helpful|not_relevant|wrong|unclear",
    // confidence_rating
    "perceived_confidence": 1-5,
    "expected_accuracy": 1-5
  },
  "context": {
    "retrieved_chunk_count": "number",
    "reranker_score_top": "float",
    "answer_latency_ms": "number",
    "corpus_id": "uuid"
  }
}
```

#### 2.2.2 Privacy Considerations

| Data Category | Retention | Anonymization | Consent Basis |
|--------------|-----------|---------------|---------------|
| User ID | 90 days rolling | Hashed immediately | Service necessity |
| Query text | 12 months | Pseudonymized after 30 days | Legitimate interest |
| Answer content | Permanent | N/A | N/A |
| Feedback metadata | Permanent | Aggregated for reporting | Consent at collection |
| Session context | 30 days | Stripped | Service necessity |

**Privacy Requirements:**
- Query text is stored with a salted hash; original text is deleted after 30 days
- Feedback cannot be traced back to individual users in reporting
- Researchers with domain expertise may be granted limited access to pseudonymized feedback for eval set curation
- All feedback data used for model training undergoes differential privacy processing (ε = 1.0)

### 2.3 Feedback Capture UI

#### 2.3.1 Inline Feedback

Deployed immediately below every answer:

```
┌─────────────────────────────────────────────────────────┐
│  Answer provided in 1.2s                                  │
│  ┌────────┐  Was this answer helpful?   [👍] [👎]    │
│  │ Stats  │  Low confidence: 0.72                         │
│  └────────┘  3 citations                                 │
└─────────────────────────────────────────────────────────┘
```

#### 2.3.2 Post-Answer Feedback

Triggered on thumbs down or dedicated CTA after 30 seconds of no further interaction:

```
┌─────────────────────────────────────────────────────────┐
│  Help us improve this answer                            │
│                                                         │
│  What was wrong?                                        │
│  [ ] Citation is incorrect                              │
│  [ ] Missing important information                       │
│  [ ] Answer is confusing                                │
│  [ ] Confidence too high/low                            │
│  [ ] Other _______________                              │
│                                                         │
│  [Submit]                         [Skip]                │
└─────────────────────────────────────────────────────────┘
```

#### 2.3.3 Periodic Surveys

- **In-app micro-surveys** — Single question deployed every 10th interaction
  - "How confident are you that this answer is accurate?" (1–5)
- **Weekly digest survey** — Emailed to active users summarizing their interaction quality
- **Quarterly NPS survey** — Full product feedback with open-text fields

---

## 3. Feedback Processing

### 3.1 Automatic Classification

All incoming feedback passes through an automatic classification pipeline before entering the review queue.

#### 3.1.1 Hallucination Detection

**Trigger:** Any `report_error` with `hallucination` category, or pattern of multiple `citation_wrong` reports on a single answer.  
**Detection Pipeline:**

1. **Cross-reference:** Compare answer claims against retrieved chunks using NLI (natural language inference) model
2. **Source grounding score:** For each claim, compute the maximum semantic similarity to any retrieved chunk (threshold: 0.72)
3. **Contradiction detection:** Run contradiction classifier on claim-chunk pairs
4. **Confidence signal:** Flag answers where `confidence_score > 0.85` but `grounding_score < 0.5`

**Output Labels:**
- `hallucination_confirmed` — Automated pipeline confirms unsupported claim
- `hallucination_likely` — High probability (>80%) but requires human review
- `grounded` — Claim supported by retrieved evidence
- `uncertain` — Requires human judgment

#### 3.1.2 Relevance Scoring

**Trigger:** All thumbs-down feedback and citation verification outcomes.  
**Metrics Computed:**

- `chunk_relevance_score` — Per-retrieved-chunk relevance (from reranker)
- `answer_relevance_score` — Composite score of whether answer addressed the query
- `coverage_score` — Proportion of query intent covered by answer
- `citation_utilization_score` — Whether retrieved citations were effectively used

**Classification Thresholds:**

| Score Range | Classification | Action |
|------------|---------------|--------|
| 0.85–1.0 | Excellent | Log, no action |
| 0.70–0.84 | Good | Monitor trends |
| 0.50–0.69 | Marginal | Add to eval set |
| 0.30–0.49 | Poor | Priority review |
| 0.00–0.29 | Critical | Immediate review |

#### 3.1.3 Confidence Mismatch Detection

**Trigger:** Feedback where `perceived_confidence ≠ expected_confidence` by 2+ points.  
**Detection Logic:**

```
mismatch_score = |perceived_confidence - expected_accuracy|

if mismatch_score >= 2:
    if perceived_confidence > expected_accuracy:
        classify("overconfident")
    else:
        classify("underconfident")
```

**Calibration Improvement:** Mismatch patterns feed directly into confidence score recalibration during model retraining.

### 3.2 Manual Review Queue

#### 3.2.1 Weekly Review Process

**Queue Population:** Feedback items flagged as `uncertain`, `hallucination_likely`, or `critical` relevance, plus a 10% random sample of all feedback for quality calibration.

**Review Frequency:** Weekly batch reviews every Tuesday and Thursday, 2-hour sessions.

**Review Tool:** Internal dashboard showing:
- Original query
- Delivered answer
- Retrieved chunks (top 10)
- All feedback submitted
- Auto-classification results
- Ground truth input field

**Output:** Each reviewed item receives a `review_label`:
- `correct` — Answer is satisfactory
- `incorrect_citation` — Citation error, specify which
- `incorrect_answer` — Answer logic/facts wrong
- `incorrect_retrieval` — Wrong chunks retrieved
- `misleading_confidence` — Confidence miscalibrated
- `edge_case` — Valid query outside system competence

#### 3.2.2 Reviewer Guidelines

**Core Principles:**
1. **Ground truth is the source corpus, not external knowledge.** Reviewers evaluate whether the answer accurately represents retrieved sources.
2. **Distinguish retrieval errors from generation errors.** A hallucinated answer with perfect retrieval is a generation problem. A missed relevant source is a retrieval problem.
3. **Context matters.** A technically accurate answer for a different query is still an error.
4. **Severity drives prioritization.** P0 errors always take precedence.

**Labeling Criteria:**

| Error Type | Evidence Required | Severity Assignment |
|-----------|-------------------|-------------------|
| Citation wrong | Show exact passage contradiction | P0 if misleading, P1 if minor |
| Hallucination | NLI score + chunk comparison | P0 if consequential, P2 if trivial |
| Missing citation | Identify missing source | P1–P2 depending on impact |
| Retrieval failure | Show which chunks should have ranked higher | P1 if relevant chunk missed |
| Confidence mismatch | Compare stated vs actual accuracy | P2 calibration issue |

#### 3.2.3 Quality Assurance

**Inter-Annotator Agreement:**
- 15% of reviewed items are dual-annotated
- Target agreement rate: Cohen's κ ≥ 0.75
- Items below threshold are escalated to senior reviewer
- Quarterly calibration sessions to maintain labeling consistency

**Review Accuracy Checks:**
- Spot-check 5% of closed reviews weekly
- Cross-reference with subsequent user behavior (did users accept the answer after our fix?)
- Flag systematic reviewer bias

**Feedback Validation:**
- Reject feedback that is clearly adversarial or spam (rate: typically <0.1%)
- Validate that feedback corresponds to a real query-answer pair
- Deduplicate identical feedback on same answer from same user

### 3.3 Quality Assurance

#### 3.3.1 Review Accuracy Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Label consistency | κ ≥ 0.75 | Inter-annotator on 15% sample |
| Corrective action accuracy | >85% | Closed-loop verification after deployment |
| False positive rate (hallucination) | <10% | Spot-check against ground truth |
| Review throughput | 50 items/hour | Per reviewer, including breaks |

#### 3.3.2 Feedback Funnel Metrics

```
Total feedback submitted
    ├─── Valid feedback (passed validation)
    │     ├─── Auto-classified as correct (no action needed)
    │     ├─── Auto-classified as incorrect
    │     │     ├─── Added to eval set (no manual review)
    │     │     └─── Escalated to manual review queue
    │     └─── Manually reviewed
    │           ├─── Confirmed incorrect → Improvement pipeline
    │           └─── Confirmed correct → Logging only
    │
    └─── Invalid feedback (spam, duplicates, erroneous)
```

**Funnel Targets:**
- Validation pass rate: >85%
- Auto-resolution rate: >60% of valid feedback
- Manual review turnaround: <72 hours
- Escalation to model improvement: Weekly batch

---

## 4. Eval Set Curation

### 4.1 Eval Set Structure

The MindLayer eval set is a curated collection of query-answer pairs with verifiable ground truth, used to measure and improve system performance.

```json
{
  "eval_item_id": "uuid",
  "created_at": "ISO8601",
  "source": "user_feedback | expert_creation | synthetic",
  "status": "active | retired | draft",
  "query": {
    "text": "string",
    "domain": "string",
    "query_type": "factual|conceptual|comparative|list|procedural",
    "difficulty": "simple|moderate|complex|expert"
  },
  "answer": {
    "expected_answer": "string (reference answer)",
    "acceptable_answers": ["string (variations that are correct)"],
    "key_claims": [
      {
        "claim": "string",
        "source_chunk_id": "uuid",
        "citation_required": true
      }
    ],
    "anti_patterns": ["common wrong answers to penalize"]
  },
  "retrieval": {
    "relevant_chunk_ids": ["uuid"],
    "distractor_chunk_ids": ["uuid (intentionally misleading)"],
    "retrieval_difficulty": "easy|medium|hard"
  },
  "confidence": {
    "expected_confidence": 1-5,
    "confidence_rationale": "string"
  },
  "metadata": {
    "num_times_tested": "number",
    "pass_rate": "float",
    "avg_model_score": "float",
    "last_tested": "ISO8601",
    "tags": ["string"]
  }
}
```

### 4.2 Curation Process

#### 4.2.1 Weekly Aggregation

**Monday:** Automated pipeline aggregates the previous week's reviewed feedback and generates candidate eval items.

**Candidate Generation Rules:**
- All items with `review_label = incorrect_citation` → `citation_accuracy` eval candidates
- All items with `review_label = incorrect_retrieval` → `retrieval_quality` eval candidates
- All items with `review_label = incorrect_answer` → `answer_relevance` eval candidates
- Items with `mismatch_score >= 2` → `confidence_calibration` eval candidates
- Top 10% by engagement (high-view, high-feedback) across correct answers → `strength_examples`

**Deduplication:**
- Semantic deduplication using embedding similarity (threshold: 0.92 cosine similarity)
- Exact-match deduplication on query hash
- Family deduplication: if query variant exists, retain the harder version

#### 4.2.2 Quality Checks

Before an eval item enters the active set:

| Check | Method | Pass Threshold |
|-------|--------|---------------|
| Ground truth verifiability | Reviewer confirms source supports expected answer | 100% |
| Unambiguous correctness | At least 2 reviewers agree on expected answer | κ ≥ 0.7 |
| Not test-set contamination | Embedding similarity to existing train queries < 0.85 | 100% |
| Sufficient difficulty | Pass rate on current model < 80% (or intentionally easy) | Per difficulty tier |
| Source availability | Source chunks are in active corpus | 100% |

#### 4.2.3 Eval Set Maintenance

**Retirement Criteria:**
- Source document removed from corpus → Item retired, not deleted
- Pass rate consistently >95% for 3 consecutive weeks → Move to "mastered" tier
- Found to have ambiguous ground truth → Return to review
- Corpus update changed relevant chunks → Recalibrate or retire

**Addition Cadence:**
- Weekly: 20–50 new items added (from feedback pipeline)
- Monthly: 100–200 new items from expert creation
- Quarterly: 500 synthetic items for coverage gaps

**Balance Targets:**

| Dimension | Target Distribution | Current Distribution | Gap |
|-----------|--------------------|---------------------|-----|
| Query type | 30% factual, 20% conceptual, 25% comparative, 15% list, 10% procedural | [Track monthly] | — |
| Domain coverage | Proportional to user query distribution | [Track monthly] | — |
| Difficulty | 15% simple, 35% moderate, 35% complex, 15% expert | [Track monthly] | — |
| Error type | 40% retrieval, 35% generation, 25% calibration | [Track monthly] | — |
| Corpus coverage | All indexed collections represented | [Track monthly] | — |

---

## 5. Active Learning

### 5.1 Uncertainty Sampling

Active learning focuses model improvement effort on cases where additional training would have the greatest impact. MindLayer uses a multi-signal uncertainty sampling strategy.

#### 5.1.1 Low Confidence + High Impact

```
priority_score = uncertainty_score × impact_weight

where:
    uncertainty_score = 1 - model_confidence  (for low-confidence items)
                      OR disagreement_score   (for ensemble disagreement)
    impact_weight = user_engagement × domain_frequency × safety_factor
```

**Impact Weight Components:**
- `user_engagement`: Queries with high repeat rate or session depth
- `domain_frequency`: Queries in the top 20% of queried domains
- `safety_factor`: Multiplier for domains where errors have high consequence (medical, legal, financial)

#### 5.1.2 Disagreement Between Models

For queries where the reranker and generator produce conflicting signals:

1. **Retrieval-Generation disagreement:** Reranker retrieves chunk X as top-1; generator generates answer supporting claim Y (incompatible with X)
2. **Multi-model disagreement:** Ensemble of rerankers disagree on top-3 ranking by >0.3 margin
3. **Confidence-Outcome disagreement:** Model reports 0.9+ confidence but eval set performance on similar queries < 0.6

These disagreements are prime candidates for human-in-the-loop review and subsequent training data generation.

#### 5.1.3 Edge Cases

Edge cases receive elevated priority due to their outsized impact on user trust:

- **Out-of-distribution queries:** Semantically distant from training data (measured by embedding centroid distance)
- **Multi-hop reasoning:** Queries requiring synthesis across 3+ retrieved chunks
- **Ambiguous queries:** Same surface form mapping to multiple valid intents
- **Negation queries:** "Does NOT mention X" style queries with high hallucination rates
- **Comparative queries:** "Which is better, X or Y?" style queries with high disagreement

### 5.2 Prioritization

#### 5.2.1 High-Impact Queries First

**Priority Tiers:**

| Tier | Criteria | SLA |
|------|----------|-----|
| P0 — Critical | P0-rated errors, hallucination_confirmed, safety-domain errors | 48-hour turnaround |
| P1 — High | P1-rated errors, retrieval failures in top-10% domains | 1-week turnaround |
| P2 — Medium | P2-rated errors, calibration mismatches, edge cases | 2-week turnaround |
| P3 — Low | P3-rated errors, synthetic candidates, strength examples | Monthly batch |

#### 5.2.2 Novel Patterns

Detect and prioritize novel error patterns before they become systemic:

- **Cluster drift detection:** Weekly comparison of error clusters against prior weeks; flag emerging cluster topics
- **New domain signal:** When query volume to a previously low-traffic domain exceeds threshold, immediately increase eval set coverage for that domain
- **Regression signal:** Errors appearing in previously mastered eval items trigger immediate investigation

#### 5.2.3 Retention-Correlated Signals

Feedback patterns correlate with user retention:

| Signal | Retention Impact | Priority Weight |
|--------|-----------------|-----------------|
| Immediate thumbs down | -15% 30-day retention | 2.0× |
| Report Error submitted | -8% 30-day retention | 1.5× |
| Repeated same-query feedback | -25% 30-day retention | 3.0× |
| Positive feedback + expert badge | +12% 30-day retention | 1.2× |

### 5.3 Human-in-the-Loop

#### 5.3.1 Expert Review

For domain-specific errors, MindLayer engages researchers with domain expertise:

**Expert Review Triggers:**
- Errors in domains with <80% automatic classification accuracy
- P0/P1 errors in specialized research areas
- Eval items with conflicting expert opinions
- Ground truth creation for synthetic data generation

**Expert Review Process:**
1. Reviewer receives anonymized context (query, answer, sources)
2. Reviewer provides: correct answer, citation corrections, confidence assessment
3. Reviewer tags difficulty and suggests similar query patterns
4. Output feeds directly into eval set and training data generation

#### 5.3.2 Researcher Validation

Before any model change is deployed, domain expert researchers validate:

- The fix does not introduce regressions in adjacent domains
- Corrected answers meet the quality bar for their field
- Updated confidence scores align with expert expectations
- Edge cases are appropriately handled

**Validation Checklist:**
- [ ] Reviewed on 5 representative queries from the error cluster
- [ ] Checked against 3 held-out eval items from same domain
- [ ] Expert sign-off obtained and logged
- [ ] No increase in false positive rate on unrelated queries

#### 5.3.3 Ground Truth Creation

For synthetic data and coverage gaps:

1. Identify the knowledge gap (e.g., "system fails on temporal comparisons")
2. Domain expert creates 20–50 ground truth query-answer pairs
3. Pairs validated by second expert
4. Added to eval set with `source = expert_creation`
5. Model performance tracked over subsequent weeks

---

## 6. Model Improvement

### 6.1 Reranker Fine-tuning

The reranker is the core component controlling which chunks reach the generator. Fine-tuning focuses on failure cases from the feedback pipeline.

#### 6.1.1 Failure Case Training

**Training Data Construction:**

```
positive_examples:  Retrieved chunks that led to correct answers (high user satisfaction)
negative_examples:  Retrieved chunks that led to incorrect answers
hard_negatives:     Chunks ranked highly but not used, or used incorrectly
```

**Fine-tuning Schedule:**
- **Weekly:** Incremental fine-tune on previous week's feedback-derived examples (3–5 epochs)
- **Monthly:** Full fine-tune on accumulated feedback data (10 epochs, validated against holdout)
- **Quarterly:** Model architecture review and potential model upgrade

**Data Mixing Strategy:**

| Example Type | Weight | Rationale |
|-------------|--------|-----------|
| Feedback-derived correct | 1.0× | Direct user signal |
| Feedback-derived incorrect | 2.5× | Over-sample failures |
| Expert-created ground truth | 1.5× | High-quality domain signal |
| Synthetic hard negatives | 0.5× | Expansion, not replacement |
| Existing eval positives | 0.3× | Prevent catastrophic forgetting |

#### 6.1.2 Positive Example Weighting

Examples from high-engagement users receive amplified weights because they represent users who invested effort in evaluation:

```python
engagement_weight = (
    1.0
    + 0.1 * feedback_depth_score      # Number of feedback types submitted
    + 0.2 * session_recurrence          # Returning user bonus
    + 0.3 * expert_domain_match         # User domain matches error domain
)
```

#### 6.1.3 A/B Testing Framework

**Test Design:**

| Test | Control | Treatment | Primary Metric | Guard Metric |
|------|---------|-----------|---------------|-------------|
| Reranker v2 | Current reranker | New fine-tuned reranker | Citation accuracy | Retrieval recall |
| Chunk weighting | Equal weight | Chunk-source quality weight | Answer correctness | Answer length |
| Diversity penalty | No penalty | Inter-chunk diversity penalty | Answer coverage | Latency |

**Guard Rails:**
- Citation accuracy must not decrease by >2% (relative)
- P95 latency must not increase by >50ms
- Retrieval recall must not decrease (measured on holdout)
- Deployment proceeds only if all guard metrics pass

**Minimum Detectable Effect:** 3% relative improvement on primary metric, 95% statistical power.

### 6.2 Prompt Engineering

Feedback directly informs prompt evolution through a structured versioning process.

#### 6.2.1 Prompt Updates from Feedback

**Update Triggers:**
- Systematic error pattern in generation (e.g., "model consistently misattributes temporal claims")
- New eval item categories performing below threshold
- Expert feedback on answer quality dimensions (clarity, depth, citation format)

**Update Process:**

1. **Pattern Identification:** Aggregate feedback into generation error themes
2. **Hypothesis Generation:** Propose prompt modifications to address themes
3. **Controlled Experiment:** A/B test prompt variants on 5% of traffic
4. **Analysis:** Evaluate against eval set and production metrics
5. **Deployment:** Roll out winning variant to full traffic
6. **Documentation:** Version the prompt with change rationale and eval evidence

#### 6.2.2 System Prompt Versioning

Every prompt version is versioned with:

```yaml
prompt_version: "v3.2.1"
created_date: "2025-06-09"
source_feedback_batch: "2025-W23"
change_summary: "Added citation attribution instruction for comparative claims"
rationale: "Reduced misattribution errors by 40% in W22 feedback"
eval_evidence:
  comparative_query_pass_rate: "+8.3%"
  citation_accuracy: "+5.1%"
  answer_length_delta: "+12 words (acceptable)"
rollout_status: "100%"
rollback_version: "v3.2.0"
```

#### 6.2.3 A/B Testing

**Prompt Test Infrastructure:**

- **Shadow mode:** New prompt runs alongside current, scores eval items, no user impact
- **Canary:** 5% traffic split for 7 days with automated monitoring
- **Full rollout:** After canary passes, gradual rollout (10% → 50% → 100%) with 24-hour evaluation windows

### 6.3 Retrieval Optimization

Feedback reveals retrieval weaknesses that prompt infrastructure changes beyond fine-tuning.

#### 6.3.1 Chunk Size Tuning

**Evaluation:** Feedback items classified as `incorrect_retrieval` are analyzed to determine if chunk size contributed:

- **Too large:** Relevant information buried in longer chunk; sub-passage retrieval would help
- **Too small:** Context collapsed; model cannot synthesize across chunks
- **Boundary error:** Chunk boundary split a coherent argument

**Adjustment Triggers:**
- >20% of retrieval errors attributable to chunk size in a domain → Trigger chunking strategy review
- Default chunk sizes: 512 tokens (dense topics), 256 tokens (high-specificity topics), 1024 tokens (review/survey content)

#### 6.3.2 Embedding Model Selection

Feedback-driven embedding evaluation:

| Metric | Measure | Decision Threshold |
|--------|---------|------------------|
| Recall@10 | Are relevant chunks in top 10? | <0.85 triggers embedding review |
| Mean Rank | How high do relevant chunks rank? | >5.0 average triggers review |
| Domain recall variance | Recall consistency across domains | >0.15 variance triggers domain-specific embedding |

#### 6.3.3 Hybrid Search Weights

**Feedback informs the balance between:**

- **Dense (embedding) search:** Semantic similarity, catches conceptual matches
- **Sparse (BM25) search:** Keyword matching, catches precise terminology
- **Direct (exact) search:** Exact phrase matching, catches precise queries

**Weight Adjustment Triggers:**
- High `citation_wrong` + low `citation_missing` → Increase sparse weight
- High `citation_missing` + low semantic diversity → Increase dense weight
- Negation query errors spike → Increase exact-match component

---

## 7. Impact Measurement

### 7.1 Feedback → Improvement Metrics

These metrics track whether feedback-driven changes actually improved the measured dimensions.

| Metric | Definition | Baseline | Target (Q3) | Target (Q4) |
|--------|-----------|----------|-------------|-------------|
| Citation accuracy | % of answers with verified correct citations | [Measure] | +10% | +20% |
| Retrieval precision@5 | Relevant chunks in top-5 / total retrieved | [Measure] | +8% | +15% |
| Retrieval recall@10 | Relevant chunks in top-10 / all relevant | [Measure] | +5% | +10% |
| Answer correctness | Eval set pass rate on answer quality items | [Measure] | +12% | +25% |
| Confidence calibration | Expected accuracy vs actual accuracy match | [Measure] | +15% | +25% |

**Measurement Cadence:** Weekly spot-check on 10% of eval set; monthly full eval set run.

### 7.2 Improvement → Feedback Metrics

These metrics track whether improvements reduced the feedback rate — the ultimate closed-loop signal.

| Metric | Definition | Baseline | Target |
|--------|-----------|----------|--------|
| Thumbs-down rate | Thumbs down / total answers | [Measure] | -30% by Q4 |
| Report Error volume | Reports submitted / total answers | [Measure] | -40% by Q4 |
| Citation error rate | Citation-related reports / total answers | [Measure] | -50% by Q4 |
| Confidence mismatch rate | Mismatch reports / total answers | [Measure] | -35% by Q4 |
| P0 error rate | P0 reports / total answers | [Measure] | -60% by Q4 |

**Measurement Cadence:** Weekly aggregation.

### 7.3 Closed-Loop Verification

The most critical step: confirming that fixes actually worked.

#### 7.3.1 Did the Fix Work?

**Post-Deployment Verification:**

1. **Immediate (0–24 hours):** Automated monitoring on production metrics
   - Error rate on affected eval items: should decrease
   - General error rate: should not increase (no regression)
   - Latency: should not increase beyond SLA

2. **Short-term (1–2 weeks):** Feedback rate analysis
   - Feedback volume on previously flagged error types: should decrease
   - New feedback patterns: monitor for emergent issues

3. **Medium-term (4–8 weeks):** Eval set validation
   - Pass rate on items from the error cluster: should improve
   - Performance on held-out items from same domain: should maintain or improve

#### 7.3.2 Regression Testing

**Automated Regression Suite:**

- Full eval set run on every deployment candidate (not just affected items)
- **Regression threshold:** Any eval metric decrease >2% (relative) blocks deployment
- **Regression scope:** Check all eval dimensions, not just the fixed dimension
- **Regressed items action:** Return to review queue, do not deploy until resolved

#### 7.3.3 Continuous Monitoring

**Production Monitoring Dashboard:**

```
┌─────────────────────────────────────────────────────────────┐
│  MindLayer Quality Dashboard — Live                         │
│                                                             │
│  Citation Accuracy    ████████░░  84.2%  (+2.1% W/W)       │
│  Retrieval Prec@5    █████████░  78.6%  (+1.4% W/W)       │
│  Answer Correctness  ███████░░░  72.1%  (-0.3% W/W) ⚠️    │
│  Confidence Cal.     █████████░  81.4%  (+3.2% W/W)        │
│                                                             │
│  Thumbs Down Rate    ████░░░░░░   8.3%  (-1.1% W/W)       │
│  Report Error Rate   ███░░░░░░░   3.7%  (-0.8% W/W)       │
│  P0 Error Rate       █░░░░░░░░░   0.4%  (-0.2% W/W)       │
│                                                             │
│  Last eval run: 2 hours ago  │  Deploy candidate: v2.4.1   │
└─────────────────────────────────────────────────────────────┘
```

**Alerting Thresholds:**

| Condition | Severity | Action |
|-----------|----------|--------|
| Any quality metric drops >5% in 24h | P1 Alert | Page on-call |
| Any quality metric drops >10% in 24h | P0 Alert | Immediate rollback review |
| Feedback rate increases >20% week-over-week | P1 Alert | Page on-call |
| P0 error rate exceeds 1% | P0 Alert | Immediate review |

---

## 8. Weekly Process

### 8.1 Monday: Data Aggregation

**Owner:** Data Engineering  
**Time:** Automated pipeline completes by 09:00 UTC  

**Steps:**

1. **Export:** Pull all feedback from past week (Monday 00:00 → Sunday 23:59 UTC)
2. **Validate:** Run deduplication, spam filtering, schema validation
3. **Classify:** Run automatic classification pipeline (hallucination detection, relevance scoring, confidence mismatch)
4. **Aggregate:** Generate candidate eval items, update eval set candidate pool
5. **Alert:** Distribute weekly feedback summary to review team
   - Total feedback volume
   - Breakdown by feedback type
   - Breakdown by error category
   - Emerging patterns (new error clusters)
   - Metrics vs prior week and vs baseline

**Deliverable:** `weekly_feedback_report_YYYY-WXX.md` shared with all stakeholders.

### 8.2 Tuesday–Wednesday: Review

**Owner:** Review Team (rotating 2-person team)  
**Time:** 2-hour blocks, Tuesday 14:00–16:00 UTC and Wednesday 10:00–12:00 UTC  

**Tuesday Steps:**

1. Pull items from manual review queue (prioritized by P0 → P1 → P2)
2. Review each item following reviewer guidelines (Section 3.2.2)
3. Label each item with `review_label` and `corrective_action`
4. Identify eval set candidates that pass quality checks
5. Flag any items requiring expert review for Thursday

**Wednesday Steps:**

1. Complete Tuesday's remaining queue
2. Dual-annotate 15% sample for inter-annotator agreement measurement
3. Review and resolve any labeling conflicts from Tuesday
4. Finalize list of eval items for Thursday curation
5. Complete inter-annotator agreement calculation and log

**Deliverable:** `weekly_review_summary_YYYY-WXX.md` — reviewed items with labels, quality metrics, expert escalations.

### 8.3 Thursday: Eval Set Update

**Owner:** Research Quality Lead  
**Time:** 14:00–17:00 UTC  

**Steps:**

1. **Review candidates:** Review all eval item candidates from Tuesday's report
2. **Quality gate:** Apply quality checks (Section 4.2.2) — reject items failing any check
3. **Diversity check:** Verify eval set balance across dimensions; create gap-filling items if needed
4. **Version:** Create new eval set version with additions and retirements
5. **Test:** Run full eval set against current production model
6. **Report:** Generate eval set performance report
   - Overall pass rates by dimension
   - Items with performance regressions (vs prior version)
   - New failure patterns
   - Eval set coverage analysis

**Deliverable:** `evalset_vX.X.X_YYYY-MM-DD.json` + `eval_report_YYYY-WXX.md`.

### 8.4 Friday: Improvement Deployment

**Owner:** Engineering Lead (rotating)  
**Time:** 14:00–18:00 UTC  

**Steps:**

1. **Prepare:** Review eval report; identify improvement candidates from this week's pipeline
2. **Validate:** Confirm all candidate improvements have passed expert review
3. **Package:** Prepare deployment package (fine-tuned reranker weights, prompt changes, config updates)
4. **Test:** Run regression suite against full eval set
5. **Canary:** Deploy to 5% traffic canary
6. **Monitor:** 4-hour monitoring window — watch quality metrics, error rates, latency
7. **Decision:** If canary passes guard metrics → proceed to 100%. If fails → rollback and return to queue.

**Deliverable:** Deployment artifact tagged with version, changelog, and eval evidence. Canary report.

### 8.5 Weekly Metrics Review

**Owner:** Product Lead  
**Time:** Friday 16:00–17:00 UTC  

**Review Agenda:**

1. Review Section 8.1–8.4 outputs against targets
2. Trend analysis: feedback rates, quality metrics, eval set performance
3. Identify blockers or resource constraints
4. Prioritize next week's improvement backlog
5. Update weekly velocity metrics

**Deliverable:** `weekly_metrics_review_YYYY-WXX.md` — signed off by Product and Engineering leads.

---

## 9. Team & Tools

### 9.1 Roles & Responsibilities

| Role | Responsibilities | Headcount | Primary Skills |
|------|-----------------|-----------|---------------|
| **Research Quality Lead** | Eval set ownership, curation quality, expert reviewer coordination | 1 | Domain expertise, eval design, data analysis |
| **Feedback Reviewer** (rotating) | Manual review queue, labeling, quality assurance | 2 (rotating) | Research methodology, critical evaluation, attention to detail |
| **ML Engineer — Reranker** | Fine-tuning pipeline, A/B testing, retrieval optimization | 1 | ML engineering, embeddings, ranking systems |
| **ML Engineer — Generation** | Prompt engineering, generation quality, calibration | 1 | NLP, prompt engineering, LLM evaluation |
| **Data Engineer** | Pipeline infrastructure, data quality, aggregation | 1 | Data engineering, SQL, pipeline automation |
| **Product Manager** | Prioritization, metrics ownership, stakeholder communication | 0.5 | Product sense, data-driven decision making |
| **Domain Experts** (panel) | Expert review, ground truth creation, validation | 3–5 (part-time) | Specialized domain knowledge (contracted) |

### 9.2 Tools & Platforms

| Function | Tool | Purpose |
|---------|------|---------|
| Feedback capture | MindLayer product UI | Inline and post-answer feedback collection |
| Feedback storage | PostgreSQL + Redis | Structured feedback storage, real-time access |
| Review queue | Custom internal dashboard | Queue management, labeling interface |
| Automatic classification | Python ML pipeline | Hallucination detection, relevance scoring |
| Eval set management | Versioned JSON + DVC | Eval set storage, versioning, diff tracking |
| Model training | Ray Tune + PyTorch | Distributed fine-tuning, hyperparameter search |
| Experiment tracking | MLflow | Experiment logging, metric comparison |
| A/B testing | LaunchDarkly + custom analytics | Feature flagging, traffic splitting |
| Monitoring | Grafana + custom dashboards | Quality metrics, alerting, trend analysis |
| Reporting | Notion + scheduled exports | Weekly reports, process documentation |
| Communication | Slack (#feedback-loop channel) | Alerts, async updates, escalations |

### 9.3 SLAs & Cadence

| Process | SLA | Frequency | Owner |
|---------|-----|-----------|-------|
| Feedback validation | <4 hours | Continuous | Data Engineering |
| Manual review queue (P0) | <48 hours | Continuous | Review Team |
| Manual review queue (P1) | <1 week | Weekly batch | Review Team |
| Eval set update | <1 week | Weekly | Research Quality Lead |
| Improvement deployment | <2 weeks from feedback | Weekly | Engineering Lead |
| Full eval set run | <4 hours | Weekly | Data Engineering |
| Canary monitoring | 4 hours post-deploy | Per deployment | Engineering On-call |
| Metrics review | Weekly | Friday 16:00 UTC | Product Lead |
| Process review | Quarterly | Calendar quarter-end | All leads |

---

## 10. Templates

### 10.1 Weekly Review Checklist

```markdown
# Weekly Review Checklist — YYYY-WXX

## Pre-Review Setup
- [ ] Pull review queue from database (items added since last review)
- [ ] Verify dual-annotation assignment (15% sample pre-selected)
- [ ] Check for P0 escalations requiring immediate attention
- [ ] Confirm expert review requests from prior week are addressed

## Review Session — Tuesday
- [ ] Review P0 items (target: all P0 items closed)
- [ ] Review P1 items batch 1 (target: 25 items reviewed)
- [ ] Log labels in review system
- [ ] Flag items for expert review
- [ ] Identify eval candidates

## Review Session — Wednesday
- [ ] Review P1 items batch 2 (target: 25 items reviewed)
- [ ] Review P2 items (target: 15 items reviewed)
- [ ] Complete dual-annotation on assigned sample
- [ ] Resolve labeling conflicts
- [ ] Finalize eval candidate list

## Post-Review
- [ ] Calculate inter-annotator agreement (Cohen's κ)
- [ ] If κ < 0.75: schedule calibration session
- [ ] Send summary to #feedback-loop
- [ ] Hand off expert review items to Research Quality Lead

## Metrics Check
- [ ] Review feedback volume vs prior week
- [ ] Check error category distribution
- [ ] Note any new patterns emerging

## Blockers
[List any blockers that prevent timely review completion]
```

### 10.2 Eval Set Curation Checklist

```markdown
# Eval Set Curation Checklist — YYYY-WXX

## Candidate Review
- [ ] Review all candidate items from weekly review
- [ ] Apply quality checks to each candidate:
      - [ ] Ground truth verifiability
      - [ ] Unambiguous correctness
      - [ ] No test-set contamination
      - [ ] Sufficient difficulty
      - [ ] Source availability
- [ ] Assign difficulty rating
- [ ] Assign query type
- [ ] Tag with relevant domains and error types

## Diversity Check
- [ ] Run balance analysis against target distributions
- [ ] Identify coverage gaps
- [ ] Create gap-filling items if needed (expert creation)
- [ ] Verify domain representation

## Version Management
- [ ] Create new eval set version file
- [ ] Document additions (count + rationale)
- [ ] Document retirements (reason for each)
- [ ] Update eval set metadata
- [ ] Commit to version control (DVC)

## Validation
- [ ] Run full eval set against production model
- [ ] Verify baseline metrics are reproducible
- [ ] Flag performance regressions
- [ ] Generate performance report

## Deliverables
- [ ] Eval set JSON file (new version)
- [ ] Performance report with pass rates by dimension
- [ ] Regressed items list (if any)
- [ ] Coverage gap analysis
- [ ] Recommendations for next week's curation focus
```

### 10.3 Deployment Checklist

```markdown
# Deployment Checklist — vX.X.X

## Pre-Deployment Validation
- [ ] All eval items from error cluster pass with new model
- [ ] No eval metric regression >2% (relative) on full set
- [ ] Expert validation completed and signed off
- [ ] A/B test results reviewed (if applicable)
- [ ] Rollback version identified and tested

## Deployment Package
- [ ] Model weights: [version/hash]
- [ ] Prompt version: [version]
- [ ] Config changes: [list]
- [ ] Eval evidence: [report link]
- [ ] Change log: [link]

## Canary Deployment
- [ ] Deploy to 5% traffic
- [ ] Enable enhanced monitoring
- [ ] Set 4-hour observation window
- [ ] Assign on-call engineer

## Canary Monitoring (4-Hour Window)
- [ ] Citation accuracy: [baseline] → [canary] (within 2%?)
- [ ] Retrieval precision: [baseline] → [canary] (within 2%?)
- [ ] Thumbs-down rate: [baseline] → [canary] (not increased >10%?)
- [ ] P95 latency: [baseline] → [canary] (within 50ms?)
- [ ] Error rate: [baseline] → [canary] (not increased?)

## Canary Decision
- [ ] PASS: All guard metrics within thresholds → Proceed to 100%
- [ ] FAIL: Any guard metric exceeded → Rollback and return to queue

## Full Rollout
- [ ] Deploy to 100% traffic
- [ ] Continue monitoring for 24 hours
- [ ] Disable enhanced monitoring after 24h stable
- [ ] Update production metrics baseline

## Post-Deployment
- [ ] Schedule closed-loop verification (1 week out)
- [ ] Update model version in documentation
- [ ] Archive deployment artifacts
- [ ] Notify #feedback-loop of deployment completion
```

### 10.4 Metrics Dashboard

```markdown
# MindLayer Feedback Loop — Weekly Metrics Dashboard
## Week Ending: YYYY-MM-DD

## 1. Feedback Volume
| Metric | This Week | Last Week | Δ | 4-Week Avg | Target |
|--------|-----------|-----------|---|------------|--------|
| Total feedback | [N] | [N] | [+/-N] | [N] | — |
| Thumbs up | [N] | [N] | [+/-N] | [N] | — |
| Thumbs down | [N] | [N] | [+/-N] | [N] | ↓30% |
| Report Error | [N] | [N] | [+/-N] | [N] | ↓40% |
| Citation verification | [N] | [N] | [+/-N] | [N] | — |

## 2. Error Distribution
| Error Type | Count | % of Reports | vs Last Week | Trend |
|-----------|-------|-------------|--------------|-------|
| citation_wrong | [N] | [X%] | [+/-N] | [↑/↓/→] |
| hallucination | [N] | [X%] | [+/-N] | [↑/↓/→] |
| citation_missing | [N] | [X%] | [+/-N] | [↑/↓/→] |
| incomplete | [N] | [X%] | [+/-N] | [↑/↓/→] |
| other | [N] | [X%] | [+/-N] | [↑/↓/→] |

## 3. Quality Metrics (Eval Set)
| Metric | This Week | Last Week | Δ | Target (Q3) | Status |
|--------|-----------|-----------|---|-------------|--------|
| Citation accuracy | [X.X%] | [X.X%] | [+/-X.X%] | +10% | [✓/⚠️/✗] |
| Retrieval precision@5 | [X.X%] | [X.X%] | [+/-X.X%] | +8% | [✓/⚠️/✗] |
| Retrieval recall@10 | [X.X%] | [X.X%] | [+/-X.X%] | +5% | [✓/⚠️/✗] |
| Answer correctness | [X.X%] | [X.X%] | [+/-X.X%] | +12% | [✓/⚠️/✗] |
| Confidence calibration | [X.X%] | [X.X%] | [+/-X.X%] | +15% | [✓/⚠️/✗] |

## 4. Closed-Loop Verification
| Deployment | Deploy Date | Citation Acc (Pre) | Citation Acc (Post) | Δ | Status |
|-----------|------------|-------------------|-------------------|---|--------|
| v2.3.1 | YYYY-MM-DD | [X.X%] | [X.X%] | [+/-X.X%] | [✓/✗] |
| v2.3.0 | YYYY-MM-DD | [X.X%] | [X.X%] | [+/-X.X%] | [✓/✗] |

## 5. Pipeline Health
| Stage | This Week | SLA | Status |
|-------|-----------|-----|--------|
| Feedback validation | [X.X%] | >85% | [✓/⚠️] |
| Auto-resolution rate | [X.X%] | >60% | [✓/⚠️] |
| Review turnaround (P0) | [X.X]h | <48h | [✓/⚠️] |
| Review turnaround (P1) | [X.X]d | <7d | [✓/⚠️] |
| Inter-annotator κ | [X.XX] | >0.75 | [✓/⚠️] |

## 6. Eval Set Growth
| Metric | Total | This Week | Target |
|--------|-------|-----------|--------|
| Active eval items | [N] | [+N] | — |
| Items added (cumulative) | [N] | [+N] | — |
| Items retired | [N] | [+N] | — |
| Domains covered | [N] | — | [Target] |

## 7. Key Observations
[Bulleted list of significant findings, patterns, or concerns]

## 8. Action Items
| Item | Owner | Due Date | Priority |
|------|-------|----------|----------|
| [Action] | [Name] | YYYY-MM-DD | P0/P1/P2 |

---
Prepared: YYYY-MM-DD | Next review: YYYY-MM-DD
```

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Eval Set** | Curated collection of query-answer pairs with ground truth used to measure system performance |
| **Hallucination** | Model generates content not supported by retrieved sources |
| **Reranker** | ML model that scores and reorders retrieved chunks before passing to generator |
| **Confidence Calibration** | Alignment between model's stated confidence and actual accuracy |
| **Active Learning** | ML strategy that prioritizes learning from informative (uncertain, high-impact) examples |
| **Closed-Loop** | Verification that an improvement actually reduced error rates in production |
| **Ground Truth** | Verified correct answer for a given query, established by expert review |
| **Hard Negative** | Retrieved chunk that appears relevant but is actually incorrect or misleading |
| **Continual Learning** | Incremental model improvement without catastrophic forgetting of prior knowledge |

## Appendix B: Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0 | 2025-06-09 | Research Quality | Initial document |

## Appendix C: Related Documents

- MindLayer Eval Set Specification (`/docs/eval-set-spec.md`)
- Reranker Fine-tuning Runbook (`/docs/reranker-finetune-runbook.md`)
- A/B Testing Framework (`/docs/ab-testing-framework.md`)
- Incident Response for P0 Errors (`/runbooks/p0-error-response.md`)
- Privacy & Data Handling Policy (`/policy/privacy-feedback.md`)
