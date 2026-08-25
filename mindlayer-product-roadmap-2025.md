# MindLayer Product Roadmap 2025

**Version:** 1.0  
**Last Updated:** January 2025  
**Status:** Active

---

## 1. Strategic Summary

### One-Sentence Mission
Transform how researchers discover and synthesize knowledge by building the AI research assistant that answers questions from *your* documents, proves where it found the answer, and surfaces connections you forgot you made.

### 2025 Goal
Capture the unclaimed "RAG-native researcher" position in the $14.8B knowledge management market before competitors consolidate the category.

### Key Milestone
**Q2 Retention Gate:** Achieve ≥70% Weekly Active Query Rate among onboarded users to unlock growth investment.

---

## 2. Quarter-by-Quarter Breakdown

### Q1 (Jan–Mar 2025): Foundation & Trust

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  Q1 TIMELINE                                                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PHASE 0: PRODUCT RESET (Weeks 1–4)                    ████████░░░░  Jan    ║
║  ├── Redis fix (volatile-lru)                          [COMPLETE]            ║
║  ├── Prometheus metrics                                [COMPLETE]            ║
║  ├── Confidence UI in every answer                     [IN PROGRESS]         ║
║  ├── "I'm not confident" fallback                     [WEEK 3]             ║
║  └── "Report Error" pipeline                           [WEEK 4]             ║
║                                                                              ║
║  PHASE 1: TRACTION (Weeks 5–8)                         ████████░░░░  Feb    ║
║  ├── Zero-setup onboarding                             [WEEK 5]             ║
║  ├── Corrective-RAG implementation                    [WEEK 6–7]            ║
║  ├── HyDE (hypothetical document embeddings)           [WEEK 7]             ║
║  └── Temporal metadata enrichment                      [WEEK 8]             ║
║                                                                              ║
║  PHASE 2: VALUE DEMONSTRATION (Weeks 9–12)              ████████░░░░  Mar    ║
║  ├── Multi-hop reasoning (EfficientRAG)                [WEEK 9–10]          ║
║  ├── Temporal memory ("What did I conclude Q1?")      [WEEK 10–11]         ║
║  ├── Feedback → eval set pipeline                      [WEEK 11]            ║
║  └── Retention gate check                              [WEEK 12]            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

#### Phase 0 (Weeks 1–4): Production Readiness

**Objective:** Eliminate reliability blockers that erode user trust.

| Task | Owner | Status | Success Criteria |
|------|-------|--------|------------------|
| Redis eviction policy → volatile-lru | Backend | Complete | Cache hit rate ≥95%, OOM errors = 0 |
| Prometheus metrics instrumentation | DevOps | Complete | P50/P95/P99 latency visible in dashboards |
| Confidence score UI in answer cards | Frontend | In Progress | Users can see 0–100% confidence on every answer |
| "I'm not confident" fallback UX | Frontend | Week 3 | Graceful degradation message with escalation path |
| "Report Error" pipeline | Full Stack | Week 4 | Error reports reach internal dashboard within 60s |

**Phase 0 Success Criteria:**
- [ ] Zero OOM crashes in production
- [ ] P95 query latency < 2 seconds
- [ ] Confidence scores displayed on 100% of answers
- [ ] Error reporting pipeline latency < 60 seconds

#### Phase 1 (Weeks 5–8): Accuracy Infrastructure

**Objective:** Build the retrieval quality that earns researcher trust.

| Feature | Description | Target Users |
|---------|-------------|--------------|
| **Zero-setup onboarding** | Connect Google Drive, Dropbox, or upload PDFs in < 3 clicks | First-time researchers |
| **Corrective-RAG** | Self-critique loop: retrieve → generate → evaluate → re-retrieve with web fallback | All users |
| **HyDE (Hypothetical Document Embeddings)** | Generate hypothetical relevant passage, embed it, then retrieve real chunks | Complex query users |
| **Temporal metadata enrichment** | Extract and index document creation/modification dates | Users with versioned research |

**Corrective-RAG Flow:**
```
User Query → Initial Retrieval → Generate Answer → Self-Critique
                                                              ↓
                                            Low Confidence? → Web Search Fallback
                                                              ↓
                                            Re-retrieve + Generate Final Answer
```

#### Phase 2 (Weeks 9–12): Value Demonstration

**Objective:** Prove MindLayer surfaces insights researchers couldn't find alone.

| Feature | Description | Differentiation |
|---------|-------------|-----------------|
| **Multi-hop reasoning (EfficientRAG)** | Chain retrieval across documents to answer "How does A relate to B?" | Core moat #3 |
| **Temporal memory** | "What did I conclude about X in Q1?" — query across document versions | Core moat #2 |
| **Feedback → eval set pipeline** | User corrections automatically improve retrieval quality | Core moat #4 |
| **Retention gate check** | Measure Weekly Active Query Rate | Gate #1 |

**Q1 Success Criteria:**
- [ ] Weekly Active Query Rate ≥ 70% among users who completed onboarding
- [ ] Answer accuracy ≥ 85% (measured via user feedback)
- [ ] Multi-hop queries resolve correctly ≥ 80% of the time
- [ ] Zero confidence score abuse (users don't game the system)

---

### Q2 (Apr–Jun 2025): Traction

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  Q2 DECISION GATE                                                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   Retention ≥ 70%? ──────────────────┐                                       ║
║         │                               │                                       ║
║         ▼                               ▼                                       ║
║   ┌──────────┐                   ┌─────────────┐                              ║
║   │  LAUNCH  │                   │    PAUSE    │                              ║
║   │  GROWTH  │                   │  GROWTH     │                              ║
║   │          │                   │  INVESTMENT │                              ║
║   │ Proceed  │                   │  Fix        │                              ║
║   │ to Phase │                   │  retention   │                              ║
║   │ 3/4      │                   │  first      │                              ║
║   └──────────┘                   └─────────────┘                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

#### If ≥70% Weekly Active Query Rate: Launch Growth

| Feature | Description | Quarter |
|---------|-------------|---------|
| **"What I Didn't Know I Knew" cards** | Proactive insight surfacing from document connections | Q2 |
| **Multi-hop discovery experience** | Guided exploration of document relationships | Q2 |
| **Team knowledge base sharing** | Shared workspaces for research teams | Q2 |

#### If <70%: Fix Retention First

**Retention Diagnostics (if gate fails):**

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Users don't return | Onboarding friction | Simplify to single-source setup |
| Queries drop after Week 1 | Answer quality失望 | Improve Corrective-RAG recall |
| Users ask fewer questions | Trust issues | Strengthen confidence calibration |
| High churn after first session | Unclear value prop | Add "first insight" tutorial |

---

### Q3 (Jul–Sep 2025): Differentiation

**Objective:** Deploy SOTA techniques that competitors cannot easily replicate.

#### SOTA Moat Deployment Schedule

| Moat | Technique | Deployment Target |
|------|-----------|-------------------|
| **#1 Corrective-RAG** | Self-critique + web fallback | Q1 (shipped) → Q3 (optimize) |
| **#2 Temporal Memory** | Time-versioned retrieval | Q1 (shipped) → Q3 (enhance) |
| **#3 Multi-hop Reasoning** | EfficientRAG with graph traversal | Q1 (shipped) → Q3 (scale) |
| **#4 Continual Learning** | Feedback → eval set → retrieval improvement | Q3 (full pipeline) |
| **#5 Confidence Calibration** | Calibrated probabilities, not arbitrary scores | Q3 (production-ready) |

#### Q3 Priorities

1. **Continual Learning Pipeline**
   - Feedback collection → automatic eval set expansion
   - Weekly retrieval model fine-tuning trigger
   - A/B test improved vs. baseline retrieval

2. **Confidence Calibration**
   - Train calibration model on answer correctness history
   - Display calibrated probabilities (e.g., "89% ± 5%")
   - Flag low-confidence answers for human review

3. **Competitive Positioning**
   - Commission comparison benchmarks vs. Perplexity, Notion AI, ChatGPT
   - Publish accuracy results for "researcher-specific" queries
   - Build case studies from top 10 research teams

---

### Q4 (Oct–Dec 2025): Scale

**Conditional on sustained ≥70% retention.**

| Initiative | Description | Target Segment |
|------------|-------------|----------------|
| **Team knowledge bases** | Collaborative workspaces with permission controls | Research teams (5–50 users) |
| **Enterprise features** | SSO, audit logs, data residency | Enterprise accounts |
| **API access** | Developer SDK for embedding MindLayer in other tools | Developers, ISVs |
| **International expansion** | Japanese, German, French language support | Non-English research markets |

---

## 3. Feature Prioritization Matrix

```
                        IMPACT
                          │
         P0 ──────────────┼─────────────────────
          │               │                    │
          │   Confidence   │   Corrective-RAG   │
          │   UI + Fallback│   Multi-hop        │
          │   (Foundation) │   (Moat #1, #3)    │
          │                │                    │
    ──────┼────────────────┼────────────────────┼────── LOW
          │                │                    │       IMPACT
          │   Feedback →   │   "What I Didn't   │
          │   Eval Pipeline│   Know I Knew"     │
          │   (Moat #4)    │   (Growth)         │
          │                │                    │
          └────────────────┼────────────────────┘
                          │
                      P3
                        │
                   URGENCY ─────────────────────────────►
```

| Priority | Feature | Rationale | Target |
|----------|---------|-----------|--------|
| **P0** | Confidence UI + Fallback | Trust foundation; without this, nothing else matters | Week 4 |
| **P0** | Redis + Prometheus | Production stability; blocks all user-facing work | Week 2 |
| **P0** | Zero-setup onboarding | Acquisition funnel leak; users drop at first hurdle | Week 5 |
| **P1** | Corrective-RAG | Core moat #1; differentiates from generic RAG | Week 6–7 |
| **P1** | Multi-hop reasoning | Core moat #3; answers complex researcher questions | Week 9–10 |
| **P1** | Temporal memory | Core moat #2; unique time-aware retrieval | Week 10–11 |
| **P2** | HyDE | Improves recall for poorly-phrased queries | Week 7 |
| **P2** | Feedback → eval pipeline | Core moat #4; drives continuous improvement | Week 11 |
| **P2** | "What I Didn't Know I Knew" | Growth driver; differentiates from reactive Q&A | Q2 |
| **P3** | Team workspaces | Growth phase feature; premature in foundation | Q2–Q3 |
| **P3** | API access | Developer ecosystem; depends on product-market fit | Q4 |
| **P3** | Enterprise features | Only with proven team adoption | Q4 |

---

## 4. Milestone Timeline (Visual)

```
2025 MILESTONES
═══════════════════════════════════════════════════════════════════════════════

        Q1                              Q2                              Q3
  Jan · Feb · Mar                Apr · May · Jun                Jul · Aug · Sep

  ───┬──┬──┼──┬──┬──┼──┬──┬──┼──┬──┬──┼──┬──┬──┼──┬──┬──┼──┬──┬──┼──┬──┬──┼──
     │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
     ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ ● PHASE 0: Production Readiness                            [Jan W1–4]  │
  │   Redis fix ─────────────────────────────────────────────────────────▶ │
  │   Prometheus ─────────────────────────────────────────────────────────▶│
  │   Confidence UI ──────────────────────────────────────────────────────▶│
  │   Fallback UX ────────────────────────────────────────────────────────▶│
  └─────────────────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ ● PHASE 1: Accuracy Infrastructure                           [Feb W5–8]│
  │   Zero-setup onboarding ───────────────────────────────────────────────▶│
  │   Corrective-RAG ──────────────────────────────────────────────────────▶│
  │   HyDE ────────────────────────────────────────────────────────────────▶│
  │   Temporal metadata ───────────────────────────────────────────────────▶│
  └─────────────────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ ● PHASE 2: Value Demonstration                            [Mar W9–12] │
  │   Multi-hop reasoning ─────────────────────────────────────────────────▶│
  │   Temporal memory ─────────────────────────────────────────────────────▶│
  │   Feedback → eval ─────────────────────────────────────────────────────▶│
  │   ◉ RETENTION GATE CHECK ◉                                    [Mar W12]│
  └─────────────────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ ● PHASE 3: Growth (conditional)                            [Q2–Q4]     │
  │   Insight cards ───────────────────────────────────────────────────────▶│
  │   Multi-hop discovery ─────────────────────────────────────────────────▶│
  │   Team workspaces ─────────────────────────────────────────────────────▶│
  │   Enterprise / API ────────────────────────────────────────────────────▶│
  └─────────────────────────────────────────────────────────────────────────┘

KEY:  ───▶ = Timeline   ● = Milestone Start   ◉ = Decision Gate

═══════════════════════════════════════════════════════════════════════════════
```

### Key Dates

| Date | Milestone | Deliverable |
|------|-----------|-------------|
| Jan 6 | Phase 0 Kickoff | Technical spec finalization |
| Jan 20 | Redis + Prometheus complete | Monitoring dashboards live |
| Feb 3 | Confidence UI shipped | Production deployment |
| Feb 24 | Zero-setup onboarding live | User can connect first source in < 3 min |
| Mar 17 | Corrective-RAG + HyDE live | Self-critique loop operational |
| Mar 31 | Multi-hop + Temporal Memory | "What did I conclude in Q1?" works |
| **Apr 7** | **Retention Gate Review** | **Go/No-Go for Growth Phase** |
| Apr 21 | If gate passed: Insight cards alpha | Internal testing |
| May 19 | If gate passed: Team workspaces beta | Limited rollout |
| Jul 7 | Continual learning pipeline v1 | Feedback → eval → improved retrieval |
| Sep 30 | Confidence calibration production-ready | Calibrated probabilities on all answers |
| Dec 31 | API access public launch | Developer documentation published |

---

## 5. Dependencies

```
FEATURE DEPENDENCY GRAPH
═══════════════════════════════════════════════════════════════════════════════

[Redis fix] ──────────────────────────┐
      │                               │
      ▼                               │
[Prometheus metrics] ─────────────────┼──► [Confidence UI]
      │                               │           │
      │                               │           ▼
      │                               │    ["I'm not confident"]
      │                               │           │
      │                               │           ▼
      │                               │    ["Report Error"]
      │                               │           │
      └───────────────────────────────┼───────────┘
                                      │
                                      ▼
                           [Zero-setup onboarding]
                                      │
                                      ▼
                              [Corrective-RAG]
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                          ▼                       ▼
                   [HyDE]            [Temporal metadata]
                          │                       │
                          └───────────┬───────────┘
                                      │
                                      ▼
                              [Multi-hop reasoning]
                                      │
                                      ▼
                              [Temporal memory]
                                      │
                                      ▼
                         [Feedback → eval pipeline]
                                      │
                                      ▼
                           [Continual learning]
                                      │
                                      ▼
                            [Retention Gate Check]

═══════════════════════════════════════════════════════════════════════════════
```

### Dependency Rules

1. **No confidence UI without Redis fix** — Cache instability will cause inconsistent scores
2. **No Corrective-RAG without zero-setup onboarding** — Can't validate accuracy without users
3. **No multi-hop without Corrective-RAG** — Multi-hop builds on single-hop retrieval quality
4. **No continual learning without feedback pipeline** — Must collect feedback before automating improvement
5. **No growth investment without retention gate** — Q1 retention is the forcing function

---

## 6. Resource Requirements

### Engineering Capacity

| Role | Q1 Allocation | Q2–Q4 (if gate passed) |
|------|---------------|------------------------|
| **Backend / Infrastructure** | 2.5 FTE | 2 FTE |
| **Frontend / Product** | 1.5 FTE | 2 FTE |
| **ML / Retrieval** | 1 FTE | 1.5 FTE |
| **DevOps / Data** | 1 FTE | 1 FTE |
| **Total** | **6 FTE** | **6.5 FTE** |

### Infrastructure Needs

| Resource | Current | Q1 Target | Q2+ Target |
|----------|---------|-----------|------------|
| **Vector DB** | Qdrant (existing) | Scale to 10M vectors | Sharding for multi-tenant |
| **LLM API** | OpenAI (GPT-4) | Add Anthropic (Claude) fallback | Model routing for cost |
| **Compute** | 4x c6i.2xlarge | 8x for multi-hop parallelism | Auto-scale with queue depth |
| **Storage** | 500 GB | 2 TB (user documents) | 10 TB + compliance tier |
| **Monitoring** | Prometheus | Grafana + PagerDuty | Anomaly detection |

### External Dependencies

| Dependency | Vendor | Risk | Mitigation |
|------------|--------|------|------------|
| LLM API availability | OpenAI / Anthropic | API rate limits, downtime | Model routing, caching |
| Document parsing | Unstructured.io | Quality regressions | Test suite, vendor backup |
| Vector DB | Qdrant | Cluster failures | Multi-AZ deployment |
| Cloud infrastructure | AWS | Regional outages | Cross-region replication |

---

## 7. Risk Factors

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Corrective-RAG latency** — Self-critique loop adds 2–5s per query | High | Medium | Async generation, stream responses |
| **Multi-hop recall** — Poor retrieval across document boundaries | High | High | HyDE pre-query, ensemble retrieval |
| **Confidence score gaming** — Users upvote low-confidence answers | Medium | Medium | Entropy monitoring, periodic audits |
| **Temporal metadata quality** — Users don't tag/document versions | Medium | Low | Automatic metadata extraction |
| **Vector DB scaling** — 10M+ vector limit reached | Low | High | Sharding plan in Q1 |

### Market Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **OpenAI launches "Researcher Mode"** — Category commoditization | Medium | High | First-mover advantage on moats #2–5 |
| **Perplexity pivots to document Q&A** — Direct competitor moves first | Medium | High | Ship Corrective-RAG before Q2 |
| **Enterprise buyer cycle > 6 months** — Revenue delayed | Medium | Medium | Focus on individual → team adoption |
| **Price sensitivity** — Researchers unwilling to pay for accuracy | Low | Medium | Freemium for individuals, team pricing |

### Competitive Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Notion AI / Confluence AI** — Platform lock-in | High | Medium | Open document format support, export |
| **Open source alternatives** — Self-hosted RAG catches up | Low | Medium | Continual learning moat requires scale |
| **GitHub Copilot for research** — Code-first tool expands | Low | Low | Monitor, no action needed |

---

## 8. Go/No-Go Criteria

### Phase 0 (Week 4): Production Readiness

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| Cache stability | OOM errors = 0 over 7 days | Prometheus alert count |
| Metrics visibility | All key metrics in Grafana | Dashboard audit |
| Confidence UI | Displayed on 100% of answers | Canary rollout → 100% |
| Error pipeline | Reports in dashboard < 60s | Synthetic test |

**Go/No-Go:** Proceed to Phase 1 only if ALL criteria green.

---

### Phase 1 (Week 8): Accuracy Infrastructure

| Criterion | Threshold | Measurement |
|-----------|-----------|------------|
| Onboarding completion rate | ≥ 80% connect first source | Funnel analytics |
| Corrective-RAG accuracy | ≥ 85% on benchmark set | Internal eval harness |
| HyDE recall lift | ≥ 10% vs. baseline | A/B test on 5% traffic |
| Temporal metadata coverage | ≥ 90% of indexed docs | Sample audit |

**Go/No-Go:** Proceed to Phase 2 only if ALL criteria green.

---

### Phase 2 (Week 12): Value Demonstration

| Criterion | Threshold | Measurement |
|-----------|-----------|------------|
| Multi-hop accuracy | ≥ 80% on 2-hop queries | Internal benchmark |
| Temporal memory accuracy | ≥ 85% on time-anchored queries | User feedback survey |
| Feedback → eval pipeline | Auto-ingestion working | Pipeline audit |
| **Weekly Active Query Rate** | **≥ 70%** | **Retention Gate** |

**Go/No-Go:** Invest in growth only if **Weekly Active Query Rate ≥ 70%**. If < 70%, pause growth investment and run retention diagnostics.

---

### Q2: Growth Investment Decision

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GATE CHECK: Apr 7, 2025                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Weekly Active Query Rate (WAQR) ────────────────────────────────────────  │
│                                                                             │
│   WAQR = Active users who ran ≥1 query in last 7 days                       │
│          ─────────────────────────────────────────────── × 100             │
│          Total users who completed onboarding                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  GO (≥ 70% WAQR)                  │  NO-GO (< 70% WAQR)           │   │
│  │  • Launch insight cards           │  • Pause growth investment     │   │
│  │  • Team workspaces beta           │  • Run retention diagnostics    │   │
│  │  • Scale infrastructure           │  • A/B test onboarding changes │   │
│  │  • Hire 1 additional engineer     │  • Revisit gate in 30 days     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Q3: Differentiation Investment

| Criterion | Threshold | Measurement |
|-----------|-----------|------------|
| Continual learning pipeline | v1 shipped | Pipeline audit |
| Confidence calibration error | < 10% miscalibration | Calibration curve eval |
| Competitive benchmark | Beats Perplexity on researcher queries | Third-party eval |
| Net Promoter Score | ≥ 40 | User survey |

**Go/No-Go:** Invest in Q4 scale initiatives only if ≥ 3 of 4 criteria green.

---

### Q4: Scale Investment

| Criterion | Threshold | Measurement |
|-----------|-----------|------------|
| Team workspace MRR | ≥ $10K MRR from teams | Billing data |
| API usage | ≥ 100 active API keys | API logs |
| Enterprise pipeline | ≥ 5 signed NDAs | Sales CRM |

**Go/No-Go:** Launch API publicly only if ≥ 2 of 3 criteria green.

---

## Appendix: Success Metrics Summary

| Metric | Q1 Target | Q2 Target | Q3 Target | Q4 Target |
|--------|-----------|-----------|-----------|-----------|
| Weekly Active Query Rate | — | ≥ 70% gate | ≥ 75% | ≥ 80% |
| Answer accuracy | ≥ 85% | ≥ 88% | ≥ 90% | ≥ 92% |
| Onboarding completion | ≥ 80% | ≥ 85% | ≥ 85% | ≥ 90% |
| Multi-hop accuracy | ≥ 80% | ≥ 85% | ≥ 88% | ≥ 90% |
| P95 query latency | < 2s | < 1.5s | < 1.2s | < 1s |
| Team workspace MRR | $0 | $0 | $0 | ≥ $10K |
| API active keys | 0 | 0 | 0 | ≥ 100 |
| NPS | — | ≥ 30 | ≥ 40 | ≥ 50 |

---

*Document maintained by Product Team. For questions, contact the product roadmap owner.*
