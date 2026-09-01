# Implementation Plan: Orivory Tech Health & Feature Adoption Sprint

## Overview

Address critical technical debt and test coverage gaps identified in the PM deep-dive review, plus create foundations for improving feature adoption. The goal is a healthier codebase that enables faster iteration on product improvements.

## Architecture Decisions

- **Python version alignment**: Use `.python-version` (3.13) as source of truth; document `pyproject.toml` requires >=3.13
- **Rate limiter test fixture**: Override rate limiter middleware in test conftest to allow test isolation
- **Datetime migration**: Use `datetime.now(UTC)` replacing all `datetime.utcnow()` calls via automated script + manual review
- **Incremental test coverage**: Target critical paths first (auth, ingestion, retrieval), then expand

## Task List

### Phase 1: Quick Wins (1-2 days)

- [ ] Task 1: Fix Python version mismatch — align runtime with `.python-version`
- [ ] Task 2: Fix auth tests — mock rate limiter in test fixtures
- [ ] Task 3: Fix deprecated datetime.utcnow() — automated replacement across codebase

### Checkpoint: Phase 1 Complete
- [ ] All tests pass (currently 5 failing)
- [ ] Python 3.13 confirmed in use

### Phase 2: Test Coverage Improvement (3-4 days)

- [ ] Task 4: Increase auth_service coverage from 19% → 50%
- [ ] Task 5: Increase vector_store coverage from 25% → 50%
- [ ] Task 6: Add Celery task tests (ingestion_tasks, email_tasks)
- [ ] Task 7: Add integration tests for source sync flow

### Checkpoint: Phase 2 Complete
- [ ] Overall test coverage ≥ 65%
- [ ] Critical paths (auth, ingestion) ≥ 50% coverage
- [ ] All existing tests pass

### Phase 3: Feature Adoption Foundation (3-4 days)

- [ ] Task 8: Document simplified onboarding flow
- [ ] Task 9: Wire up feature discovery hints system
- [ ] Task 10: Create A/B testing framework for onboarding experiments

### Checkpoint: Phase 3 Complete
- [ ] Onboarding documentation complete
- [ ] Feature hints system ready for data collection

### Phase 4: Integration & Polish (2-3 days)

- [ ] Task 11: Add CI smoke tests for Docker compose
- [ ] Task 12: Set up dependency scanning (pip-audit)
- [ ] Task 13: Document known gaps and create backlog items

### Checkpoint: Phase 4 Complete
- [ ] CI includes integration smoke tests
- [ ] Security scanning in place
- [ ] Backlog items created for deferred work

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Python 3.13 incompatibilities with dependencies | Medium | Test thoroughly; some libs may need version pins |
| Breaking auth during test fixture changes | High | Test locally before commit; review rate limiter override |
| Datetime migration introduces subtle bugs | Medium | Careful review; compare before/after for date logic |
| Feature adoption work without user research | Medium | Start with low-effort changes; validate with data |

## Open Questions

1. Should we prioritize feature adoption work over test coverage? (PM decision)
2. Is there budget for user research on adoption blockers?
3. What's the timeline pressure — can we spread this over multiple sprints?

## Dependencies

```
Task 1 (Python version)
    ↓
Task 2 (Auth tests) ← Task 3 can run in parallel
    ↓
Checkpoint 1
    ↓
Task 4-7 (Test coverage) ← Can parallelize across files
    ↓
Checkpoint 2
    ↓
Task 8-10 (Feature adoption)
    ↓
Checkpoint 3
    ↓
Task 11-13 (Integration & polish)
    ↓
Checkpoint 4 (Complete)
```
