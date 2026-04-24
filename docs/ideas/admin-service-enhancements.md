# Admin Service Enhancements

## Problem Statement
How Might We empower Operations and Support teams to effectively manage users, troubleshoot issues, and oversee system health without requiring engineering intervention, while maintaining strict data privacy and an auditable trail of all administrative actions?

## Recommended Direction
**The "Auditable Support Toolkit"**
This direction focuses on building a cohesive suite of admin endpoints specifically designed for support workflows. It prioritizes safety and observability (Audit Logging, Data Privacy) over raw power.

Instead of generic CRUD endpoints, we will build purpose-driven actions:
1.  **User Lifecycle Management:** Endpoints to deactivate, delete, and view recent activity of users.
2.  **Troubleshooting & Impersonation:** Secure, read-only "impersonation" or debug views for a user's workspace, with PII masking in chat logs.
3.  **Document Operations:** Ability to list all documents, pinpoint stuck/failed processing, and force retries or deletions.
4.  **System Settings:** Dynamic configuration for quotas, maintenance modes, and global feature flags, reducing the need for environment variable changes and redeploys.

*Why this direction?* It directly addresses the "incomplete features" pain point for the specified audience (Operations/Support) while strictly adhering to the core constraints of Data Privacy and Audit Logging.

## Key Assumptions to Validate
- [ ] **Assumption:** Support staff need to view chat content to debug issues effectively. *Validation:* Interview 2-3 support reps to confirm if metadata (errors, token counts, latency) is sufficient, or if message content is truly required.
- [ ] **Assumption:** PII masking can be done reliably enough to satisfy data privacy constraints. *Validation:* Prototype a PII masking solution (e.g., using Presidio or a dedicated LLM pass) on sample data and review with security/legal.
- [ ] **Assumption:** A simple audit log table (AdminActionLog) will suffice for tracking changes. *Validation:* Verify if existing compliance frameworks require shipping these logs to an immutable external system (like Datadog or a SIEM).

## MVP Scope
**In Scope for V1:**
- **Audit Foundation:** A new `admin_audit_logs` table recording `admin_id`, `target_entity_type`, `target_entity_id`, `action`, and `changes`. A dependency to automatically log actions in the admin router.
- **User Management:** Deactivate user, delete user (soft delete), view user activity summary.
- **Document Management:** List all documents (with filtering by status/user), delete specific document, retry failed document.
- **System Configuration:** Basic key-value store for global settings (e.g., default quotas) editable via API.

**Out of Scope for V1:**
- **Full Impersonation / Chat Debugging:** PII masking and read-only impersonation are complex. V1 will only provide metadata about errors and usage, not raw chat content.
- **Bulk Operations:** Modifying thousands of users at once introduces performance risks and complex rollback scenarios.
- **Admin UI Dashboard:** This effort is API-only. We assume the team uses an internal tool (Retool, Appsmith) or scripts to hit these APIs.

## Not Doing (and Why)
- **Direct Database Access / Raw SQL Endpoints:** Too risky, violates auditability and data privacy constraints. All actions must be scoped through typed endpoints.
- **Hard Deletes for Users/Documents:** To preserve data integrity and allow for recovery from mistakes, we will use soft deletes (e.g., setting an `is_deleted` flag) for the MVP.
- **Exposing Raw Chat Logs:** Violates the Data Privacy constraint. Until a robust PII masking solution is validated (post-MVP), support will debug using metadata (errors, system prompts used, token usage).

## Open Questions
- How should we handle the transition of existing hard-coded defaults (like quotas) to the new dynamic system settings?
- Do we need granular role-based access control (RBAC) within the "admin" tier (e.g., `support_tier_1` vs `super_admin`), or is a single `admin` role sufficient for now?