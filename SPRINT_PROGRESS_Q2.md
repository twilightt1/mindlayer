# MindLayer Sprint Progress Q2 2025

**Last Updated:** Auto-generated  
**Status:** 📋 Planning  
**Decision Gate:** Apr 7, 2025

---

## Q2 Decision Matrix

```
Retention Gate (Apr 7):
├── WAQR ≥ 70%? → LAUNCH GROWTH
│   ├── Insight Cards ("What I Didn't Know I Knew")
│   ├── Multi-hop Discovery Experience  
│   └── Team Knowledge Base Sharing
│
└── WAQR < 70%? → FIX RETENTION FIRST
    ├── Simplify onboarding to single-source
    ├── Improve Corrective-RAG recall
    └── Add "first insight" tutorial
```

---

## Growth Track: Q2 Tasks (If ≥70% WAQR)

### Insight Cards - Week 13-16

| Task | Status | Notes |
|------|--------|-------|
| Document connection analysis engine | 📋 Pending | Find unexpected connections |
| Proactive insight surfacing | 📋 Pending | Surface before user asks |
| Insight card UI component | 📋 Pending | Display cards in sidebar |
| User preference learning | 📋 Pending | Learn which insights matter |

### Multi-hop Discovery Experience - Week 17-20

| Task | Status | Notes |
|------|--------|-------|
| Graph visualization of document relationships | 📋 Pending | Interactive exploration UI |
| Guided discovery flows | 📋 Pending | Help users find connections |
| Cross-document reference highlighting | 📋 Pending | Show related content inline |
| Discovery analytics | 📋 Pending | Track insight discovery patterns |

### Team Knowledge Base Sharing - Week 21-24

| Task | Status | Notes |
|------|--------|-------|
| Workspace concept | 📋 Pending | Shared vs personal workspaces |
| Permission model | 📋 Pending | View/edit/share controls |
| Team admin dashboard | 📋 Pending | Manage team members |
| Invite flow | 📋 Pending | Email invite + SSO |

---

## Retention Fix Track: Q2 Tasks (If <70% WAQR)

### Onboarding Simplification - Week 13-16

| Task | Status | Notes |
|------|--------|-------|
| Single-source setup wizard | 📋 Pending | One-click connect |
| "3 documents" quick start | 📋 Pending | Upload → query immediately |
| Value proposition tutorial | 📋 Pending | Show first insight in < 2 min |
| Onboarding analytics | 📋 Pending | Funnel drop-off tracking |

### Corrective-RAG Improvement - Week 17-20

| Task | Status | Notes |
|------|--------|-------|
| Recall benchmarking | 📋 Pending | Establish baseline |
| Retrieval ensemble | 📋 Pending | Combine multiple retrievers |
| Query expansion tuning | 📋 Pending | Better handling of vague queries |
| Web fallback optimization | 📋 Pending | Faster, more relevant results |

### Trust Building - Week 21-24

| Task | Status | Notes |
|------|--------|-------|
| Confidence calibration | 📋 Pending | Calibrated probabilities |
| Source attribution UI | 📋 Pending | Show which doc answered |
| "Why this answer" explainability | 📋 Pending | Show reasoning path |
| Transparency report | 📋 Pending | Accuracy metrics public |

---

## Retention Gate Check Framework

### Weekly Active Query Rate (WAQR)

```
WAQR = Active users (≥1 query in 7 days)
       ───────────────────────────────── × 100
       Total users (completed onboarding)
```

### Retention Thresholds

| Metric | Minimum | Target | Current |
|--------|---------|--------|---------|
| Weekly Active Query Rate | 70% | 80% | — |
| Answer Accuracy | 85% | 90% | — |
| P95 Latency | < 2s | < 1.5s | — |
| Feedback Rate | 10% | 15% | — |
| Multi-hop Accuracy | 80% | 85% | — |

---

## Q2 Go/No-Go Criteria

| Criterion | Threshold | Date |
|-----------|-----------|------|
| Retention Gate | WAQR ≥ 70% | Apr 7 |
| Insight Cards Alpha | Shipped to internal | Apr 21 |
| Team Workspaces Beta | Limited rollout | May 19 |

---

## Dependencies

```
Q1 Retention Gate Check
        │
        ▼ (Apr 7 Decision)
        │
   ┌────┴────┐
   ▼         ▼
 GROWTH    RETENTION FIX
   │         │
   ▼         ▼
Insight   Onboarding
Cards     Simplify
   │         │
   ▼         ▼
Multi-hop Corrective-RAG
Discovery Improvement
   │         │
   ▼         ▼
Team     Trust
Workspaces Building
```

---

## Next Actions

1. 📋 Wait for retention data (Apr 7, 2025)
2. 📋 Based on WAQR decision: implement Growth or Retention Fix track
3. 📋 Weekly retention monitoring with RetentionGateChecker

---

*Document prepared based on Q1 completion - Apr 2025*
