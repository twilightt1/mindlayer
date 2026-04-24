# Tasks: Admin Service Enhancements

- [ ] Task 1: Database Models & Migrations
  - Acceptance: `AdminActionLog` and `SystemSetting` models exist. `User` model has `is_deleted` (default False). Alembic migration generated and applied successfully.
  - Verify: Run `alembic upgrade head` and verify tables/columns exist in DB.
  - Files: `app/models/admin_audit.py`, `app/models/system_setting.py`, `app/models/user.py`, new alembic revision file.

- [ ] Task 2: Core Services (`AuditService` & `SettingsService`)
  - Acceptance: `AuditService` can log actions. `SettingsService` can CRUD settings with Redis caching and DB fallback. Unit tests written and passing.
  - Verify: `pytest tests/services/test_audit.py tests/services/test_settings.py` (or similar unit test files) pass with >80% coverage.
  - Files: `app/services/audit_service.py`, `app/services/settings_service.py`, `tests/unit/...`

- [ ] Task 3: User Management Admin Endpoints
  - Acceptance: `/admin/users/{user_id}` supports soft-delete (`is_deleted`). New endpoint for user activity summary (metadata). All mutating actions log via `AuditService`.
  - Verify: Integration tests for these endpoints pass.
  - Files: `app/api/v1/admin.py`, `tests/api/test_admin_users.py`

- [ ] Task 4: Document Management Admin Endpoints
  - Acceptance: Endpoints to list all documents (with filters), retry failed docs, soft-delete docs. All mutating actions log via `AuditService`.
  - Verify: Integration tests for these endpoints pass.
  - Files: `app/api/v1/admin.py` (or `app/api/v1/admin_docs.py`), `tests/api/test_admin_docs.py`

- [ ] Task 5: System Settings Admin Endpoints
  - Acceptance: Endpoints to CRUD global settings via `SettingsService`. Mutating actions log via `AuditService`.
  - Verify: Integration tests for these endpoints pass.
  - Files: `app/api/v1/system_settings.py`, `tests/api/test_admin_settings.py`
