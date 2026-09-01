# Backlog Items — Deferred Work

This document tracks known gaps and deferred work identified during the PM review and development sessions.

---

## Priority: High

### 1. `parent_id` JSONB → Column Migration 🔴

**Issue:** The `parent_id` field is currently stored as JSONB (`metadata->'parent_id'`) instead of a proper foreign key column.

**Impact:**
- Slower queries for parent-child relationships
- No referential integrity
- Difficult to index and optimize

**Acceptance Criteria:**
- [ ] Add `parent_id` as nullable UUID column with FK constraint
- [ ] Write migration to backfill from JSONB
- [ ] Update all queries to use new column
- [ ] Remove JSONB handling after verification
- [ ] Add tests for parent-child traversal

**Estimated Effort:** M (1-2 days)

**Files Affected:**
- `app/models/memory.py`
- `app/retrieval/memory/vector_store.py`
- Database migrations

---

### 2. OAuth State Cookie Binding 🔴

**Issue:** OAuth state parameter validation may not properly bind to session cookies, potentially vulnerable to CSRF.

**Impact:**
- Security vulnerability in OAuth flow
- Could allow unauthorized account linking

**Acceptance Criteria:**
- [ ] Verify state parameter generation uses cryptographically secure random
- [ ] Confirm state is stored in HttpOnly cookie
- [ ] Add state validation with proper error handling
- [ ] Add OAuth CSRF tests

**Estimated Effort:** S (0.5 days)

**Files Affected:**
- `app/api/v1/auth.py`
- `app/services/auth_service.py`

---

### 3. Access Token Revocation Improvement 🔴

**Issue:** Access tokens are not being revoked on logout; only refresh tokens are invalidated.

**Impact:**
- Token leakage could allow persistent access
- No way for users to "sign out everywhere"

**Acceptance Criteria:**
- [ ] Implement token blacklisting in Redis
- [ ] Add `/auth/revoke` endpoint
- [ ] Update logout flow to revoke access token
- [ ] Add "sign out all devices" option

**Estimated Effort:** M (1-2 days)

**Files Affected:**
- `app/api/v1/auth.py`
- `app/services/auth_service.py`
- `app/middleware/auth.py`

---

## Priority: Medium

### 4. Mobile PWA Support 🟡

**Issue:** App lacks progressive web app (PWA) capabilities for mobile users.

**Impact:**
- Poor mobile experience
- Users can't install app
- No offline support

**Acceptance Criteria:**
- [ ] Add service worker for offline support
- [ ] Create web manifest
- [ ] Add install prompt
- [ ] Test on iOS Safari and Android Chrome

**Estimated Effort:** L (3-5 days)

**Files Affected:**
- `frontend/` (new PWA files)

---

### 5. Pricing Page 🟡

**Issue:** No pricing page exists; users directed to contact sales.

**Impact:**
- Conversion friction
- Can't self-serve for simple plans

**Acceptance Criteria:**
- [ ] Design pricing tiers (Free, Pro, Team, Enterprise)
- [ ] Implement pricing page
- [ ] Add Stripe integration for payments
- [ ] Add plan comparison table

**Estimated Effort:** L (5-7 days)

**Files Affected:**
- `frontend/src/app/pricing/`
- Stripe integration

---

### 6. Email Template Theming 🟡

**Issue:** Email templates use hardcoded styles; no white-label support.

**Impact:**
- Can't reskin emails for white-label
- Poor brand consistency

**Acceptance Criteria:**
- [ ] Extract email styles to config
- [ ] Add logo and colors to settings
- [ ] Support multiple themes (future)

**Estimated Effort:** M (2-3 days)

**Files Affected:**
- `app/services/email_service.py`
- Email templates

---

### 7. Workspace Analytics Dashboard 🟡

**Issue:** No analytics for workspace owners to see usage stats.

**Impact:**
- Owners can't see value from team usage
- Hard to identify inactive members

**Acceptance Criteria:**
- [ ] Add workspace metrics table
- [ ] Create analytics endpoints
- [ ] Build analytics dashboard UI
- [ ] Add scheduled metric collection

**Estimated Effort:** L (4-5 days)

**Files Affected:**
- `app/api/v1/analytics.py`
- `app/services/analytics_service.py`
- `frontend/src/app/workspace/analytics/`

---

## Priority: Low

### 8. Keyboard Shortcuts 🟢

**Issue:** No keyboard shortcuts for power users.

**Impact:**
- Slower navigation for frequent users

**Acceptance Criteria:**
- [ ] Document keyboard shortcuts
- [ ] Implement quick capture shortcut (Ctrl/Cmd + K)
- [ ] Add shortcut hints in UI

**Estimated Effort:** S (0.5 days)

**Files Affected:**
- `frontend/src/components/`

---

### 9. Dark Mode Persistence 🟢

**Issue:** Dark mode preference not persisted across sessions.

**Impact:**
- Users must toggle each visit

**Acceptance Criteria:**
- [ ] Save preference to localStorage
- [ ] Respect system preference as default
- [ ] Add to user settings

**Estimated Effort:** XS (0.25 days)

**Files Affected:**
- `frontend/src/app/layout.tsx`

---

### 10. Export to Notion/Confluence 🟢

**Issue:** Users can't export memories back to Notion/Confluence.

**Impact:**
- One-way sync only
- Can't use Orivory as a writing tool

**Acceptance Criteria:**
- [ ] Add export button to memories
- [ ] Implement Notion page creation
- [ ] Implement Confluence page creation

**Estimated Effort:** L (5-7 days)

**Files Affected:**
- `app/api/v1/memories.py`
- `app/services/export_service.py`
- New connectors

---

## Backlog Grooming Notes

| Date | Attendees | Notes |
|------|----------|-------|
| 2025-01-15 | PM, Engineering | Prioritized parent_id migration and token revocation as security items |

---

## Issue Templates

Use these labels when creating issues:
- `backlog-high` - Priority High items
- `backlog-medium` - Priority Medium items
- `backlog-low` - Priority Low items
- `security` - Security-related items
- `performance` - Performance optimization items
