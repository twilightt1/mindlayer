# Orivory Tech Health Sprint — Task List

## Phase 1: Quick Wins

### Task 1: Fix Python Version Mismatch 🔴
**Status:** ⏳ Deferred - System has 3.9.6, but venv uses 3.13 (tests pass)

**Description:** Align system Python with `.python-version` (3.13). Current runtime shows 3.9.6 which doesn't match project requirements.

**Acceptance criteria:**
- [ ] `python3 --version` returns 3.13.x
- [ ] `which python3` points to correct Python 3.13 installation
- [ ] All tests pass with Python 3.13

**Verification:**
- [ ] Run `python3 --version` and confirm 3.13.x
- [ ] Run `source .venv/bin/activate && python --version` confirms 3.13
- [ ] Run full test suite: `pytest -x`

**Dependencies:** None

**Files likely touched:**
- `.python-version`
- `.venv/` (recreate may be needed)
- `README.md` (if instructions mention specific Python)

**Estimated scope:** S (1-2 files, mostly config)

---

### Task 2: Fix Auth Tests — Mock Rate Limiter 🔴
**Status:** ✅ COMPLETE

**Description:** Auth tests were failing (4/5) because the rate limiter middleware blocks requests before they reach auth handlers. 

**Changes Made:**
- Added comprehensive `MockRedis` class in `tests/conftest.py`
- Mocks all Redis operations: `pipeline()`, `incr()`, `expire()`, `get()`, `setex()`, `delete()`, `zcard()`, `zadd()`, `zremrangebyscore()`
- Patched `get_redis` at all usage points: `rate_limiter`, `redis_client`, `auth_service`, `api/v1/auth`

**Acceptance criteria:**
- [x] `tests/test_auth.py::test_register_success` passes
- [x] `tests/test_auth.py::test_register_duplicate_email` passes
- [x] `tests/test_auth.py::test_login_unverified` passes
- [x] `tests/test_auth.py::test_login_wrong_password` passes
- [x] `tests/test_auth.py::test_forgot_password_unknown_email` still passes

**Verification:**
- [x] Run: `pytest tests/test_auth.py -v` → All 5 tests show PASSED

**Files touched:**
- `tests/conftest.py`

**Estimated scope:** M (3-4 files, test fixture + middleware understanding)

---

### Task 3: Fix Deprecated datetime.utcnow() 🟡
**Status:** ✅ COMPLETE

**Description:** Replaced all `datetime.utcnow()` calls with `datetime.now(UTC)` across the codebase. 16+ files affected.

**Changes Made:**
- Created `app/models/_datetime_helpers.py` with `utc_now()` helper for SQLAlchemy
- Updated 20+ files to use timezone-aware datetime
- Fixed RSS connector timezone comparison bug (naive vs aware)

**Acceptance criteria:**
- [x] No more `DeprecationWarning: datetime.datetime.utcnow()` in test runs
- [x] All datetime logic continues to work correctly
- [x] Uses consistent timezone-aware approach

**Verification:**
- [x] Run: `pytest --tb=short 2>&1 | grep -c "utcnow"` returns 0

**Files touched:**
- `app/models/_datetime_helpers.py` (NEW)
- `app/ingestion/dispatcher.py`
- `app/ingestion/connectors/rss.py`
- `app/ingestion/connectors/web_clipper.py`
- `app/ingestion/types.py`
- `app/graph/clustering.py`
- `app/graph/builder.py`
- `app/agents/memory_agent.py`
- `app/retrieval/memory/salience.py`
- `app/models/memory.py`
- `app/models/conversation.py`
- `app/models/document.py`
- `app/models/entity.py`
- `app/models/source.py`
- `app/models/system_setting.py`
- `app/models/user_quota.py`
- `app/models/user.py`
- `app/models/referral.py`
- `app/api/v1/sources.py`
- `app/api/v1/memories.py`
- `app/api/v1/entities.py`
- `app/services/analytics_service.py`

**Estimated scope:** M (5-8 files, automated find-replace + manual review)

---

## Checkpoint: Phase 1 ✅
- [ ] All Phase 1 tasks complete
- [ ] `pytest` shows 0 failures
- [ ] No deprecation warnings

---

## Phase 2: Test Coverage Improvement

### Task 4: Increase auth_service Coverage 19% → 50% 🟠
**Description:** Add unit tests for auth_service.py, focusing on uncovered code paths (209 lines uncovered). Key areas: token generation, refresh flow, password hashing edge cases.

**Acceptance criteria:**
- [ ] `auth_service.py` coverage increases from 19% to ≥50%
- [ ] New tests for: refresh token rotation, password change invalidation, OAuth helpers
- [ ] All new tests pass

**Verification:**
- [ ] Run: `pytest --cov=app/services/auth_service --cov-report=term-miss`
- [ ] Confirm coverage ≥50%

**Dependencies:** Task 2 (auth tests need to pass first)

**Files likely touched:**
- `tests/services/test_auth_service.py` (create)
- `app/services/auth_service.py`

**Estimated scope:** M (3-4 files)

---

### Task 5: Increase vector_store Coverage 25% → 50% 🟠
**Description:** Add tests for vector_store.py (117 lines uncovered). Key areas: async/sync upsert paths, ChromaDB interaction mocking, error handling.

**Acceptance criteria:**
- [ ] `vector_store.py` coverage increases from 25% to ≥50%
- [ ] Tests cover: upsert, delete, search, batch operations
- [ ] ChromaDB interactions properly mocked

**Verification:**
- [ ] Run: `pytest --cov=app/retrieval/memory/vector_store --cov-report=term-miss`
- [ ] Confirm coverage ≥50%

**Dependencies:** Task 2

**Files likely touched:**
- `tests/retrieval/test_vector_store.py` (create)
- `app/retrieval/memory/vector_store.py`

**Estimated scope:** M (2-3 files)

---

### Task 6: Add Celery Task Tests (ingestion_tasks, email_tasks) 🔴
**Description:** Current Celery tasks have 0% coverage. Critical for production reliability. Focus on ingestion_tasks (143 lines) and email_tasks (19 lines).

**Acceptance criteria:**
- [ ] `tasks/ingestion_tasks.py` coverage ≥40%
- [ ] `tasks/email_tasks.py` coverage ≥60%
- [ ] Tasks properly mocked (not actually sending emails or processing documents)

**Verification:**
- [ ] Run: `pytest --cov=app/tasks --cov-report=term`
- [ ] Confirm coverage targets met

**Dependencies:** Task 2

**Files likely touched:**
- `tests/tasks/test_ingestion_tasks.py` (create)
- `tests/tasks/test_email_tasks.py` (create)
- `app/tasks/ingestion_tasks.py`
- `app/tasks/email_tasks.py`

**Estimated scope:** M (4 files)

---

### Task 7: Integration Tests for Source Sync Flow 🟠
**Description:** Add end-to-end integration test for source sync: Notion/Gmail → Memory → ChromaDB → Recall.

**Acceptance criteria:**
- [ ] Integration test covers full sync path
- [ ] Tests verify: memory creation, ChromaDB indexing, recall ability
- [ ] Test can run in CI (with mocked external APIs)

**Verification:**
- [ ] Run: `pytest tests/integration/test_source_sync.py -v`
- [ ] Test completes successfully

**Dependencies:** Tasks 4, 5 (vector_store and auth working)

**Files likely touched:**
- `tests/integration/test_source_sync.py` (create)
- `app/ingestion/dispatcher.py`
- `app/retrieval/memory/vector_store.py`

**Estimated scope:** M (3-4 files)

---

## Checkpoint: Phase 2 ✅
- [ ] All Phase 2 tasks complete
- [ ] Overall test coverage ≥65%
- [ ] Critical paths (auth, ingestion) ≥50% coverage

---

## Phase 3: Feature Adoption Foundation

### Task 8: Document Simplified Onboarding Flow 🟡
**Status:** ✅ COMPLETE

**Description:** Created comprehensive documentation for streamlined onboarding experience.

**Files Created:**
- `docs/ONBOARDING.md` - Full onboarding documentation including:
  - Current flow analysis (strengths & friction points)
  - Proposed 3-step onboarding design
  - Feature discovery hints system design
  - Migration plan and analytics tracking

---

### Task 9: Wire Up Feature Discovery Hints System 🟡
**Status:** ✅ COMPLETE

**Files Created:**
- `app/schemas/hint.py` - Hint schemas (FeatureHint, HintInteraction, etc.)
- `app/api/v1/hints.py` - Hint API endpoints
- `frontend/src/components/hints/FeatureHints.tsx` - React component

---

### Task 10: Create A/B Testing Framework 🟡
**Status:** ✅ COMPLETE

**Files Created:**
- `app/schemas/experiment.py` - Experiment schemas (Experiment, Variant, MetricEvent, etc.)
- `app/services/experiments_service.py` - A/B testing service with user assignment
- `app/api/v1/experiments.py` - Experiment API endpoints

---

## Checkpoint: Phase 3 ✅
- [ ] Onboarding documentation complete
- [ ] Feature hints system ready for data collection
- [ ] A/B testing framework operational

---

## Phase 4: Integration & Polish

### Task 11: CI Smoke Tests for Docker Compose 🟡
**Description:** Add integration smoke tests that run against Docker compose stack in CI. Ensures the full stack works together.

**Acceptance criteria:**
- [ ] CI runs smoke tests on PR
- [ ] Tests cover: database, Redis, ChromaDB, API health endpoint
- [ ] Tests run in parallel with existing unit tests

**Verification:**
- [ ] CI workflow includes smoke tests
- [ ] Tests fail if any service is unhealthy

**Dependencies:** Tasks 1-7

**Files likely touched:**
- `.github/workflows/ci.yml` (update)
- `tests/smoke/` (create)

**Estimated scope:** M (3-4 files)

---

### Task 12: Set Up Dependency Scanning 🟡
**Description:** Add pip-audit or similar to CI for security vulnerability scanning. Addresses known gap in security posture.

**Acceptance criteria:**
- [ ] `pip-audit` runs in CI on PR
- [ ] Report generated for vulnerabilities
- [ ] Critical vulnerabilities fail CI

**Verification:**
- [ ] CI workflow includes `pip-audit`
- [ ] Vulnerabilities are caught and reported

**Dependencies:** None

**Files likely touched:**
- `.github/workflows/ci.yml` (update)
- `requirements.txt` (update)
- `requirements-dev.txt` (update)

**Estimated scope:** S (1-2 files)

---

### Task 13: Document Known Gaps and Create Backlog Items 🟡
**Description:** Create GitHub Issues for all deferred work identified in the PM review.

**Acceptance criteria:**
- [ ] GitHub Issue created for: `parent_id` JSONB→column migration
- [ ] GitHub Issue created for: OAuth state cookie binding
- [ ] GitHub Issue created for: Access token revocation improvement
- [ ] GitHub Issue created for: Mobile PWA (if not exists)
- [ ] GitHub Issue created for: Pricing page (if not exists)

**Verification:**
- [ ] All issues created in GitHub
- [ ] Issues have clear acceptance criteria

**Dependencies:** None (can run parallel)

**Files likely touched:** None (GitHub only)

**Estimated scope:** S (documentation only)

---

## Checkpoint: Phase 4 ✅
- [ ] CI includes integration smoke tests
- [ ] Security scanning in place
- [ ] Backlog items created for deferred work

---

## Final Checkpoint: Sprint Complete ✅
- [ ] All 13 tasks complete
- [ ] Phase checkpoints verified
- [ ] Code reviewed by team member
- [ ] Ready to merge to main

---

## Summary Statistics

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| Phase 1: Quick Wins | 3 | 1-2 days |
| Phase 2: Test Coverage | 4 | 3-4 days |
| Phase 3: Feature Adoption | 3 | 3-4 days |
| Phase 4: Integration | 3 | 2-3 days |
| **Total** | **13** | **9-13 days** |

---

*Plan created: 2026-09-01*
*Based on: PM Deep Dive Review findings*
