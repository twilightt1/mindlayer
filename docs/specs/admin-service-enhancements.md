# Spec: Admin Service Enhancements

## Objective
Empower Operations and Support teams to effectively manage users, troubleshoot issues, and oversee system health without engineering intervention. This will be an API-only enhancement prioritizing safety, data privacy, and observability via an "Auditable Support Toolkit".

## Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL with SQLAlchemy (Async) and Alembic for migrations
- **Caching:** Redis (for dynamic settings)
- **Authentication:** Existing JWT/session mechanisms (FastAPI Depends)

## Commands
- **Dev:** `fastapi dev app/main.py`
- **Build/Migration:** `alembic upgrade head`
- **Lint:** `ruff check app`
- **Format:** `black app`
- **Test:** `pytest --cov=app/api/v1/admin.py`

## Project Structure
```text
app/
├── api/
│   └── v1/
│       ├── admin.py           → Update existing router with new endpoints
│       └── system_settings.py → New router for dynamic settings
├── models/
│   ├── admin_audit.py         → New: AdminActionLog model
│   ├── system_setting.py      → New: SystemSetting model
│   └── user.py                → Update: Add `is_deleted` for soft deletes
├── schemas/
│   ├── admin_audit.py         → New: Pydantic models for audit logs
│   └── system_setting.py      → New: Pydantic models for settings
├── services/
│   └── audit_service.py       → New: Logic for recording audit logs
│   └── settings_service.py    → New: Logic for reading/updating settings with Redis cache
└── tests/
    └── api/
        └── test_admin.py      → Add/update tests
docs/
├── specs/                     → Specifications (this file)
└── ideas/                     → Idea drafts
```

## Code Style
Use modern Python type hints, Pydantic for validation, and dependency injection for DB sessions and auth.

```python
# Example: Audit Logging Dependency
async def log_admin_action(
    action: str,
    target_type: str,
    target_id: UUID,
    changes: dict,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    log = AdminActionLog(
        admin_id=admin_user.id,
        target_entity_type=target_type,
        target_entity_id=target_id,
        action=action,
        changes=changes
    )
    db.add(log)
    # Commit handled by the endpoint
```

## Testing Strategy
- **Framework:** `pytest`
- **Location:** `tests/api/test_admin.py`
- **Coverage:** >= 80% on new files and endpoints
- **Strategy:** Write unit tests for the settings service and audit service. Write integration tests for the new admin endpoints to ensure permissions (`require_admin`) and audit logging work correctly.

## Boundaries
- **Always:** Log mutating admin actions (`PUT`, `POST`, `DELETE`) to the `admin_audit_logs` table. Use soft deletes (`is_deleted = True`) instead of hard deletes. Check DB for settings and fallback to hardcoded defaults if missing.
- **Ask first:** Modifying the core User model or auth mechanisms beyond adding soft delete.
- **Never:** Expose raw chat logs/message content in admin APIs (violates privacy). Never allow direct SQL execution endpoints.

## Success Criteria
- Support staff can deactivate/soft-delete users via API.
- Support staff can view a user's recent activity summary (metadata only, no PII).
- Support staff can list all documents, filter by status, and retry/delete them.
- Admins can update global settings (e.g., default quotas) via API, which take effect immediately (via Redis cache).
- Every mutating action performed by an admin is successfully recorded in the `admin_audit_logs` table.

## Open Questions
- None. (Hard-coded defaults transition resolved: DB with fallback).