# Implementation Plan: Admin Service Enhancements

## 1. Major Components and Dependencies
- **Database Models & Migrations (Foundation):**
  - `AdminActionLog` model (depends on `User` for `admin_id` and `target_entity_id`).
  - `SystemSetting` model.
  - Update `User` model to add `is_deleted` (boolean, default False).
- **Core Services:**
  - `AuditService`: Reusable logic to write to `AdminActionLog`.
  - `SettingsService`: Logic to read/write `SystemSetting` with Redis caching and fallback to hardcoded defaults.
- **Admin API Endpoints (Depends on Models & Services):**
  - **User Management:** Update `/users/{user_id}` (deactivate/soft-delete), add endpoint for user activity summary.
  - **Document Management:** Add endpoints to list all documents (filtered), retry failed documents, and soft-delete documents.
  - **System Settings:** Add endpoints to CRUD system settings.

## 2. Implementation Order (Sequential vs. Parallel)

**Phase 1: Foundation (Sequential - Must be done first)**
1. Update `User` model with `is_deleted`.
2. Create `AdminActionLog` and `SystemSetting` models.
3. Generate and apply Alembic migrations for these changes.
*Verification Checkpoint 1:* DB schema is updated successfully and the application starts.

**Phase 2: Core Services (Can be done in parallel)**
- **Track A:** Implement `AuditService`.
- **Track B:** Implement `SettingsService` (with Redis caching logic and fallback).
*Verification Checkpoint 2:* Unit tests for `AuditService` and `SettingsService` pass (mocking DB/Redis where appropriate).

**Phase 3: API Endpoints (Depends on Phase 1 & 2)**
- **Track C:** Implement User Management endpoints & wire up `AuditService` for these actions.
- **Track D:** Implement System Settings endpoints & wire up `AuditService` + `SettingsService`.
- **Track E:** Implement Document Management endpoints & wire up `AuditService`.
*Verification Checkpoint 3:* Integration tests for the new admin endpoints pass, confirming permissions, expected behavior, and audit log creation.

## 3. Risks and Mitigation Strategies
- **Risk:** Redis cache invalidation issues for System Settings.
  - **Mitigation:** Keep cache TTL relatively short (e.g., 5-10 minutes) as a fallback, and explicitly delete/update the Redis key whenever a setting is updated via the API.
- **Risk:** Soft-deleting users breaking foreign key constraints (e.g., UserQuota, Messages, Documents).
  - **Mitigation:** Ensure application logic checks `is_deleted` when fetching users. Foreign keys don't need to cascade delete if we are soft deleting, but queries must exclude soft-deleted users.
- **Risk:** Audit logging slowing down admin API responses.
  - **Mitigation:** If performance is an issue, audit logs could be written asynchronously (e.g., background tasks). For MVP, synchronous writes within the same transaction are acceptable since admin volume is low.

## 4. Verification Checkpoints
- **Checkpoint 1 (DB):** Migrations apply cleanly on a fresh database.
- **Checkpoint 2 (Services):** Core logic works in isolation with unit tests (>80% coverage).
- **Checkpoint 3 (API):** Endpoints correctly require the admin role, perform the action, and leave an audit trail in the database.