# API Capabilities Matrix

This matrix summarizes the main backend capabilities exposed by MindLayer.
All application endpoints are versioned under `/api/v1` unless noted otherwise.

## Public Health and Readiness

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | Basic API liveness and version check. |
| `GET` | `/ready` | Public | Dependency readiness for Postgres, Redis, MinIO, and ChromaDB. Returns degraded status with HTTP 503 when dependencies fail. |

## Authentication

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Public | Register with email and password. |
| `POST` | `/auth/verify-email/otp` | Public | Verify email with OTP and receive onboarding-scoped access token. |
| `GET` | `/auth/verify-email/link` | Public | Verify email through a link and redirect through one-time exchange code. |
| `POST` | `/auth/verify-email/resend` | Public | Resend email verification. |
| `POST` | `/auth/onboarding` | User | Complete onboarding and receive full tokens. |
| `POST` | `/auth/login` | Public | Login with email/password. |
| `GET` | `/auth/google/authorize` | Public | Start Google OAuth flow. |
| `GET` | `/auth/google/callback` | Public | Handle Google OAuth callback and redirect through one-time exchange code. |
| `POST` | `/auth/exchange-code` | Public | Exchange short-lived redirect code for auth payload. |
| `POST` | `/auth/refresh` | Public | Rotate refresh token and receive new access/refresh pair. |
| `POST` | `/auth/logout` | User | Revoke refresh token and blacklist current access token JTI. |
| `POST` | `/auth/forgot-password` | Public | Start password reset. |
| `POST` | `/auth/forgot-password/verify-otp` | Public | Verify reset OTP. |
| `POST` | `/auth/reset-password` | Public | Complete password reset. |

## User Profile

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/users/me` | Verified user | Return current user profile. |
| `PATCH` | `/users/me` | Verified user | Update display name/profile fields. |
| `POST` | `/users/me/change-password` | Verified user | Change account password. |

## Conversations and Chat

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/chat/conversations` | Active user | List user conversations. |
| `POST` | `/chat/conversations` | Active user | Create a conversation. |
| `GET` | `/chat/conversations/{conversation_id}` | Active user | Get conversation details, documents, and messages. |
| `PATCH` | `/chat/conversations/{conversation_id}` | Active user | Update conversation title. |
| `DELETE` | `/chat/conversations/{conversation_id}` | Active user | Delete conversation and associated retrieval indexes. |
| `GET` | `/chat/conversations/{conversation_id}/messages` | Active user | List conversation messages. |
| `POST` | `/chat/conversations/{conversation_id}/message` | Active user | Ask a question and receive `text/event-stream` response events. |

## Documents

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/chat/conversations/{conversation_id}/documents` | Active user | List documents for a conversation. |
| `POST` | `/chat/conversations/{conversation_id}/documents` | Active user | Upload document and queue ingestion. |
| `GET` | `/chat/conversations/{conversation_id}/documents/{document_id}` | Active user | Get ingestion status and document metadata. |
| `DELETE` | `/chat/conversations/{conversation_id}/documents/{document_id}` | Active user | Delete document and cleanup storage/index data. |

## Admin Operations

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/admin/users` | Admin | List users. |
| `GET` | `/admin/users/{user_id}` | Admin | Get user details. |
| `GET` | `/admin/users/{user_id}/activity` | Admin | Summarize user conversations, messages, documents, and activity timestamps. |
| `PUT` | `/admin/users/{user_id}` | Admin | Update role, active/deleted state, and quota settings. |
| `POST` | `/admin/users/{user_id}/reset-quota` | Admin | Reset quota counters. |
| `GET` | `/admin/documents` | Admin | List documents across users with optional filters. |
| `POST` | `/admin/documents/{document_id}/retry` | Admin | Requeue failed document ingestion. |
| `DELETE` | `/admin/documents/{document_id}` | Admin | Delete document through shared cleanup logic. |
| `GET` | `/admin/stats` | Admin | Return high-level system statistics. |
| `GET` | `/admin/diagnostics` | Admin | Return dependency checks, Celery status, secret-safe config summary, and ingestion diagnostics. |

## Admin System Settings

| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/admin/settings` | Admin | List system settings. |
| `GET` | `/admin/settings/{key}` | Admin | Get a setting by key. |
| `PUT` | `/admin/settings/{key}` | Admin | Update or create a setting with audit logging. |
| `DELETE` | `/admin/settings/{key}` | Admin | Delete a setting with audit logging. |

## Streaming Event Types

| Event | Purpose |
| :--- | :--- |
| `status` | Graph progress, retry attempts, and current stage. |
| `token` | Answer token or fallback full-response chunk. |
| `sources` | Source snippets and rerank scores. |
| `trace` | Agent trace metadata for observability. |
| `done` | Final completion event with token count and retry count. |
| `error` | Safe client-facing error event. |

## Security Notes

- Admin endpoints require `require_admin`.
- User chat/document endpoints are scoped to the authenticated user's
  conversation.
- `/admin/diagnostics` intentionally excludes secrets and should not be exposed
  as a public health endpoint.
- Refresh token exchange uses request bodies instead of query strings.
- OAuth and email redirects use short-lived one-time exchange codes.
