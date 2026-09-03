# MCP Hub Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Open Memory Hub spine to Orivory: registered agent clients with per-client tokens, an MCP server exposing memory tools over streamable HTTP, and a complete access ledger ("which AI read/wrote what, when").

**Architecture:** Reuse the existing FastAPI app. Two new SQLAlchemy tables (`agent_clients`, `memory_access_logs`) track registered agents and every MCP tool call. A Starlette-compatible auth wrapper resolves the per-client bearer token into an `AgentPrincipal` (user + scopes); the official `mcp` SDK's `FastMCP` server (stateless HTTP mode) is mounted at `/mcp` and its tools enforce scopes + write ledger rows. Token plaintext is shown once at registration; only SHA-256 hashes are stored.

**Tech Stack:** FastAPI 0.115 (existing), SQLAlchemy 2.0 async + Alembic (existing), `mcp` python SDK (new dependency, official Anthropic python-sdk), Pydantic v2.

**Spec:** `docs/ideas/open-memory-hub.md` (MVP items 1 + 4; ledger feeds item 5's receipts later).

## Global Constraints

- Python 3.12+, ruff line-length 120, target py313 (`pyproject.toml`).
- All routes under `/api/v1`; routers use `Annotated[User, Depends(get_current_verified_user)]` and `Annotated[AsyncSession, Depends(get_db)]` (copy the pattern from `app/api/v1/memories.py:76-102`).
- Postgres is source of truth; Chroma/graph indexing stays best-effort (`app/retrieval/memory/write_back.py` helpers).
- Migrations: new revision `d4e5f6a7b8c9` with `down_revision = "f7a8b9c0d1e2"` (current head).
- New model files follow `app/models/memory.py` style: `from __future__ import annotations`, `Mapped[...]` columns, `_datetime_helpers.utc_now`, exports in `__all__` and `app/models/__init__.py`.
- Tokens: format `oa_` + 32 lowercase hex chars; store only `sha256` hex digest (64 chars) with a unique index. Never log or return the plaintext after the registration response.
- Scope names: `memory:read`, `memory:write` (exact strings).
- CI-safe tests only: no live Postgres/Redis/Chroma in unit tests; use fakes/monkeypatch like existing `tests/` suites. Register every new router in `tests/api/test_router_wiring.py:ROUTERS_TO_CHECK`.
- Every task ends with `ruff check app tests` green + the touched pytest subset green + a Conventional Commit.

---

### Task 1: AgentClient + MemoryAccessLog models and migration

**Files:**
- Create: `app/models/agent_client.py`
- Create: `app/models/memory_access_log.py`
- Modify: `app/models/__init__.py` (add exports)
- Create: `alembic/versions/d4e5f6a7b8c9_agent_clients_and_access_logs.py`
- Test: `tests/models/test_hub_models.py`

**Interfaces:**
- Produces: `AgentClient` (fields: `id: uuid.UUID`, `user_id: uuid.UUID`, `name: str`, `token_hash: str`, `scopes: list[str]`, `status: str` default `"active"`, `created_at`, `last_used_at: datetime | None`, `revoked_at: datetime | None`; property `is_active` → `status == "active" and revoked_at is None`) and `MemoryAccessLog` (fields: `id`, `user_id`, `agent_client_id: uuid.UUID | None`, `action: str`, `memory_id: uuid.UUID | None`, `detail: dict`, `created_at`). Later tasks import both from `app.models`.

- [ ] **Step 1: Write the failing test** — `tests/models/test_hub_models.py`:

```python
"""Unit tests for hub models: shape, defaults, active logic."""
from __future__ import annotations

import uuid

from app.models.agent_client import AgentClient
from app.models.memory_access_log import MemoryAccessLog


def test_agent_client_defaults():
    client = AgentClient(user_id=uuid.uuid4(), name="Claude Desktop", token_hash="a" * 64)
    assert client.is_active is True
    assert client.scopes == ["memory:read"]
    assert client.status == "active"


def test_agent_client_revoked_is_inactive():
    client = AgentClient(user_id=uuid.uuid4(), name="Old Agent", token_hash="b" * 64, status="revoked")
    assert client.is_active is False


def test_access_log_defaults():
    entry = MemoryAccessLog(user_id=uuid.uuid4(), action="mcp_search")
    assert entry.detail == {}
    assert entry.memory_id is None
    assert entry.agent_client_id is None
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/models/test_hub_models.py -v` → FAIL (ImportError).
- [ ] **Step 3: Write the models** — `app/models/agent_client.py`:

```python
"""Registered MCP/agent clients for the Open Memory Hub.

An AgentClient is one external agent (Claude Desktop, OpenClaw, Cursor, a
script) that the user has explicitly granted access to their memory store.
Tokens are stored as SHA-256 hashes only; the plaintext is shown once at
registration time by the agents API.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Index, String, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._datetime_helpers import utc_now


class AgentClient(Base):
    __tablename__ = "agent_clients"

    id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)  # FK added in migration
    name:        Mapped[str]       = mapped_column(String(100), nullable=False)
    token_hash:  Mapped[str]       = mapped_column(String(64), nullable=False, unique=True, index=True)
    scopes:      Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("'{memory:read}'::varchar[]"), nullable=False)
    status:      Mapped[str]       = mapped_column(String(16), server_default="active", nullable=False)

    created_at:   Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    revoked_at:   Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.revoked_at is None


__all__ = ["AgentClient"]
```

`app/models/memory_access_log.py`:

```python
"""Access ledger for the Open Memory Hub.

Every MCP tool call (and later, every sensitive read) appends a row here so
the user can answer "which AI saw what, and when". Rows are append-only;
deletion of a memory does NOT erase the ledger (the ledger records that the
memory was accessed before deletion).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, TIMESTAMP, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MemoryAccessLog(Base):
    __tablename__ = "memory_access_logs"

    id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    agent_client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action:          Mapped[str] = mapped_column(String(32), nullable=False)
    memory_id:       Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    detail:          Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    created_at:      Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)

    __table_args__ = (
        Index("ix_access_logs_user_time", "user_id", "created_at"),
        Index("ix_access_logs_client_time", "agent_client_id", "created_at"),
    )


__all__ = ["MemoryAccessLog"]
```

Then update `app/models/__init__.py` to import and export both (follow the file's existing import/export list style).

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/models/test_hub_models.py -v` → PASS.
- [ ] **Step 5: Write the migration** — `alembic/versions/d4e5f6a7b8c9_agent_clients_and_access_logs.py`, revision `d4e5f6a7b8c9`, down_revision `"f7a8b9c0d1e2"`, `op.create_table` for both tables (columns exactly as the models above, `sa.ForeignKey(["user_id"], "users.id", ondelete="CASCADE")`, `memory_access_logs.agent_client_id` → `agent_clients.id` ondelete `"SET NULL"`, `memory_id` → `memories.id` ondelete `"SET NULL"`), indexes `ix_agent_clients_user_id`, `ix_agent_clients_token_hash` (unique), `ix_access_logs_user_time`, `ix_access_logs_client_time`. Downgrade drops tables in reverse order.
- [ ] **Step 6: Lint + full unit suite** — `ruff check app tests && pytest tests/models tests/api -q` → green.
- [ ] **Step 7: Commit** — `git commit -m "feat: hub agent clients + access ledger models and migration"`.

---

### Task 2: Agent token service

**Files:**
- Create: `app/services/agent_token_service.py`
- Test: `tests/services/test_agent_token_service.py`

**Interfaces:**
- Produces (used by Tasks 3 and 4):
  - `generate_token() -> str` — `"oa_" + secrets.token_hex(16)`.
  - `hash_token(token: str) -> str` — sha256 hex digest.
  - `token_hash_prefix(token: str) -> str` — first 8 chars of the digest (for logs, safe).
  - `validate_scopes(scopes: list[str]) -> list[str]` — raises `ValueError` unless every item is in `{"memory:read", "memory:write"}`; returns deduped list; empty input → `["memory:read"]`.

- [ ] **Step 1: Write the failing test** — `tests/services/test_agent_token_service.py`:

```python
"""Unit tests for agent token generation and validation."""
from __future__ import annotations

import hashlib

import pytest

from app.services.agent_token_service import (
    generate_token,
    hash_token,
    token_hash_prefix,
    validate_scopes,
)


def test_generate_token_format():
    token = generate_token()
    assert token.startswith("oa_")
    assert len(token) == 3 + 32
    int(token[3:], 16)  # hex-parseable


def test_generate_token_unique():
    assert len({generate_token() for _ in range(100)}) == 100


def test_hash_token_is_sha256():
    assert hash_token("oa_abc") == hashlib.sha256(b"oa_abc").hexdigest()


def test_token_hash_prefix_is_safe():
    assert token_hash_prefix("oa_abc") == hash_token("oa_abc")[:8]
    assert len(token_hash_prefix("oa_abc")) == 8


def test_validate_scopes_ok():
    assert validate_scopes(["memory:read", "memory:write"]) == ["memory:read", "memory:write"]
    assert validate_scopes([]) == ["memory:read"]


def test_validate_scopes_rejects_unknown():
    with pytest.raises(ValueError, match="unknown scope"):
        validate_scopes(["admin:all"])
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/services/test_agent_token_service.py -v` → FAIL (ImportError).
- [ ] **Step 3: Implement** — `app/services/agent_token_service.py`:

```python
"""Token generation/hashing for Open Memory Hub agent clients.

Plaintext tokens look like ``oa_<32 hex>`` and are shown exactly once, in
the registration response. Only ``sha256`` digests are persisted, so a
database leak never leaks usable credentials. Log lines may carry the
8-char digest prefix (``token_hash_prefix``) for support correlation.
"""
from __future__ import annotations

import hashlib
import secrets

ALLOWED_SCOPES = ("memory:read", "memory:write")
DEFAULT_SCOPES: tuple[str, ...] = ("memory:read",)


def generate_token() -> str:
    return "oa_" + secrets.token_hex(16)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_hash_prefix(token: str) -> str:
    return hash_token(token)[:8]


def validate_scopes(scopes: list[str]) -> list[str]:
    if not scopes:
        return list(DEFAULT_SCOPES)
    for scope in scopes:
        if scope not in ALLOWED_SCOPES:
            raise ValueError(f"unknown scope: {scope!r} (allowed: {ALLOWED_SCOPES})")
    return list(dict.fromkeys(scopes))


__all__ = ["ALLOWED_SCOPES", "DEFAULT_SCOPES", "generate_token", "hash_token", "token_hash_prefix", "validate_scopes"]
```

- [ ] **Step 4: Run to verify it passes** — `pytest tests/services/test_agent_token_service.py -v` → PASS.
- [ ] **Step 5: Lint + commit** — `ruff check app tests && pytest tests/services -q`; `git commit -m "feat: agent token service (generate/hash/scopes)"`.

---

### Task 3: Agents management API (register / list / revoke / ledger)

**Files:**
- Create: `app/api/v1/agents.py`
- Modify: `app/api/v1/router.py` (register router)
- Modify: `tests/api/test_router_wiring.py` (append `"app.api.v1.agents"` to `ROUTERS_TO_CHECK`)
- Modify: `app/schemas/Orivory.py` (add response/request models)
- Test: `tests/api/test_agents_router.py` (wiring-level, no live DB)

**Interfaces:**
- Produces REST API:
  - `POST /api/v1/agents` body `{"name": str, "scopes": [str]}` → 201 `{"id", "name", "scopes", "status", "created_at", "token": "oa_..."}` (token only here).
  - `GET /api/v1/agents` → `{"items": [{...client fields, last_used_at}], "total": int}` (no token field).
  - `DELETE /api/v1/agents/{client_id}` → 204 (sets `status="revoked"`, `revoked_at=now()`; revoking twice is 404 if not owned/absent, 204 if already revoked by same owner).
  - `GET /api/v1/agents/access-log?agent_client_id=&limit=&offset=` → `{"items": [{id, agent_client_id, action, memory_id, detail, created_at}], "total": int}` (always scoped to `current_user.id`).
- Produces schemas in `app/schemas/Orivory.py`: `AgentClientCreate(name: str, scopes: list[str] = [])`, `AgentClientCreated(...)`, `AgentClientResponse(...)`, `AgentClientListResponse(items, total)`, `AccessLogResponse(...)` items, `AccessLogListResponse(items, total)`.

- [ ] **Step 1: Write the wiring test** — `tests/api/test_agents_router.py`:

```python
"""Wiring tests for the agents (hub clients) router — CI-safe, no live DB."""
from __future__ import annotations

from fastapi.routing import APIRoute

from app.api.v1.agents import router


def test_agents_routes_registered():
    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/agents" in paths
    assert "/agents/access-log" in paths
    assert "/agents/{client_id}" in paths


def test_agents_no_token_field_in_list_response():
    from app.schemas.Orivory import AgentClientResponse

    assert "token" not in AgentClientResponse.model_fields
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/api/test_agents_router.py -v` → FAIL (ImportError).
- [ ] **Step 3: Add schemas** to `app/schemas/Orivory.py` (follow existing style in that file, e.g. `MemoryResponse`): `AgentClientCreate`, `AgentClientCreated(id, name, scopes, status, created_at, token)`, `AgentClientResponse(id, name, scopes, status, created_at, last_used_at, revoked_at)`, `AgentClientListResponse(items: list[AgentClientResponse], total: int)`, `AccessLogItem(id, agent_client_id, action, memory_id, detail, created_at)`, `AccessLogListResponse(items: list[AccessLogItem], total: int)`.
- [ ] **Step 4: Implement the router** — `app/api/v1/agents.py`. Endpoints per Interfaces above. Registration flow: `validate_scopes(body.scopes)` → `generate_token()` → `AgentClient(user_id=current_user.id, name=body.name, token_hash=hash_token(token), scopes=scopes)` → commit → respond with plaintext token. List/revoke/ledger queries all filter `user_id == current_user.id`; revoke sets `status="revoked"`, `revoked_at=utc_now()`. Ledger endpoint orders by `created_at desc`, caps `limit` at 200. Auth dependency: `get_current_verified_user` (same as `memories.py`). Docstring at top documents that the token is shown once and that revocation is immediate.
- [ ] **Step 5: Wire the router** — add `agents` to the import list and `api_router.include_router(agents.router)` in `app/api/v1/router.py`; append `"app.api.v1.agents"` to `ROUTERS_TO_CHECK` in `tests/api/test_router_wiring.py`.
- [ ] **Step 6: Run to verify it passes** — `pytest tests/api/test_agents_router.py tests/api/test_router_wiring.py -v` → PASS.
- [ ] **Step 7: Lint + commit** — `ruff check app tests && pytest tests/api -q`; `git commit -m "feat: agent clients API (register/list/revoke) + access ledger endpoint"`.

---

### Task 4: MCP identity resolution (principal + DB lookup)

**Files:**
- Create: `app/mcp_hub/__init__.py`
- Create: `app/mcp_hub/identity.py`
- Test: `tests/mcp_hub/test_identity.py`

**Interfaces:**
- Produces (used by Task 5):
  - `AgentPrincipal` dataclass: `user_id: uuid.UUID`, `agent_client_id: uuid.UUID`, `name: str`, `scopes: frozenset[str]`; methods `can_read() -> bool` (`"memory:read" in scopes`), `can_write() -> bool`.
  - `extract_token(headers: Mapping[str, str]) -> str | None` — accepts `Authorization: Bearer oa_...` (case-insensitive scheme) or `X-Orivory-Agent-Token: oa_...`.
  - `async resolve_principal(db: AsyncSession, token: str | None) -> AgentPrincipal | None` — sha256 lookup on `agent_clients.token_hash`, active only (`is_active`), updates `last_used_at` when found, returns None otherwise.
  - `ACTION_*` string constants: `ACTION_SEARCH = "mcp_search"`, `ACTION_GET = "mcp_get"`, `ACTION_LIST = "mcp_list"`, `ACTION_ADD = "mcp_add"`, `ACTION_DELETE = "mcp_delete"`.

- [ ] **Step 1: Write the failing test** — `tests/mcp_hub/test_identity.py` (create `tests/mcp_hub/__init__.py` too):

```python
"""Unit tests for MCP principal resolution. DB access is faked."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.mcp_hub.identity import AgentPrincipal, extract_token
from app.services.agent_token_service import generate_token, hash_token


def test_extract_token_bearer():
    assert extract_token({"Authorization": "Bearer oa_abc123"}) == "oa_abc123"
    assert extract_token({"authorization": "bearer oa_abc123"}) == "oa_abc123"


def test_extract_token_custom_header():
    assert extract_token({"X-Orivory-Agent-Token": "oa_xyz"}) == "oa_xyz"


def test_extract_token_missing():
    assert extract_token({}) is None
    assert extract_token({"Authorization": "Basic zzz"}) is None


def test_principal_scopes():
    p = AgentPrincipal(
        user_id=uuid.uuid4(),
        agent_client_id=uuid.uuid4(),
        name="Claude",
        scopes=frozenset({"memory:read"}),
    )
    assert p.can_read() and not p.can_write()


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def scalars(self):
        return self

    def first(self):
        return self._row


class _FakeDB:
    def __init__(self, row):
        self._row = row
        self.committed = False

    async def execute(self, _stmt):
        return _FakeResult(self._row)

    async def commit(self):
        self.committed = True


async def test_resolve_principal_found_and_updates_last_used():
    from app.mcp_hub.identity import resolve_principal
    from app.models.agent_client import AgentClient

    client = AgentClient(user_id=uuid.uuid4(), name="OpenClaw", token_hash=hash_token("oa_ok"), scopes=["memory:read", "memory:write"])
    db = _FakeDB(client)
    principal = await resolve_principal(db, "oa_ok")
    assert principal is not None
    assert principal.can_write()
    assert db.committed
    assert client.last_used_at is not None and client.last_used_at.tzinfo is not None


async def test_resolve_principal_rejects_inactive_or_bad_token():
    from app.mcp_hub.identity import resolve_principal
    from app.models.agent_client import AgentClient

    revoked = AgentClient(user_id=uuid.uuid4(), name="Old", token_hash=hash_token("oa_rev"), status="revoked")
    assert await resolve_principal(_FakeDB(revoked), "oa_rev") is None
    assert await resolve_principal(_FakeDB(None), "oa_missing") is None
    assert await resolve_principal(_FakeDB(None), None) is None
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/mcp_hub/test_identity.py -v` → FAIL (ImportError). If pytest warns about async tests, ensure `pytest.ini`/`pyproject` already configures asyncio mode the way existing async tests do (check `pyproject.toml [tool.pytest.ini_options]`); follow whatever the repo already uses for `async def` tests.
- [ ] **Step 3: Implement** — `app/mcp_hub/identity.py`:

```python
"""Agent identity for MCP tool calls.

Every MCP request carries a per-client token (registered via the agents
API). ``resolve_principal`` maps it to an active AgentClient row and returns
a lightweight principal the tools can enforce scopes against. The MCP SDK
does not pass caller identity inside the protocol — so the hub is where
identity, scopes and the access ledger live.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Mapping

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_client import AgentClient
from app.services.agent_token_service import hash_token

ACTION_SEARCH = "mcp_search"
ACTION_GET = "mcp_get"
ACTION_LIST = "mcp_list"
ACTION_ADD = "mcp_add"
ACTION_DELETE = "mcp_delete"


@dataclass(frozen=True)
class AgentPrincipal:
    user_id: uuid.UUID
    agent_client_id: uuid.UUID
    name: str
    scopes: frozenset[str]

    def can_read(self) -> bool:
        return "memory:read" in self.scopes

    def can_write(self) -> bool:
        return "memory:write" in self.scopes


def extract_token(headers: Mapping[str, str]) -> str | None:
    auth = headers.get("Authorization") or headers.get("authorization")
    if auth:
        scheme, _, value = auth.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    return headers.get("X-Orivory-Agent-Token") or headers.get("x-orivory-agent-token")


async def resolve_principal(db: AsyncSession, token: str | None) -> AgentPrincipal | None:
    if not token:
        return None
    row = (
        await db.execute(select(AgentClient).where(AgentClient.token_hash == hash_token(token)))
    ).scalars().first()
    if row is None or not row.is_active:
        return None
    await db.execute(
        update(AgentClient).where(AgentClient.id == row.id).values(last_used_at=datetime.now(UTC))
    )
    await db.commit()
    return AgentPrincipal(
        user_id=row.user_id,
        agent_client_id=row.id,
        name=row.name,
        scopes=frozenset(row.scopes or []),
    )


__all__ = [
    "ACTION_ADD", "ACTION_DELETE", "ACTION_GET", "ACTION_LIST", "ACTION_SEARCH",
    "AgentPrincipal", "extract_token", "resolve_principal",
]
```

- [ ] **Step 4: Run to verify it passes** — `pytest tests/mcp_hub/test_identity.py -v` → PASS.
- [ ] **Step 5: Lint + commit** — `ruff check app tests`; `git commit -m "feat: mcp hub identity resolution (principal + scopes)"`.

---

### Task 5: MCP server (FastMCP, stateless HTTP) with scoped memory tools + ledger writes

**Files:**
- Create: `app/mcp_hub/server.py`
- Create: `app/mcp_hub/tools.py`
- Modify: `app/main.py` (mount at `/mcp` when enabled)
- Modify: `app/config.py` (add `MCP_HUB_ENABLED: bool = True` near the other feature flags)
- Modify: `pyproject.toml` (add `"mcp>=1.9.0"` to dependencies)
- Modify: `.env.example` (document `MCP_HUB_ENABLED`)
- Test: `tests/mcp_hub/test_tools.py`

**Interfaces:**
- Consumes: `AgentPrincipal`, `resolve_principal`, `ACTION_*` (Task 4); `Memory` model; `index_new_memory`, `safe_delete_from_chroma` (`app/retrieval/memory/write_back.py`); `AsyncSessionLocal` (`app/database.py`).
- Produces:
  - `app/mcp_hub/server.py::build_mcp_server() -> FastMCP` — `FastMCP("orivory-memory", stateless_http=True, json_response=True)`, registers the five tools from `tools.py`; `get_mcp_app() -> ASGI app` returns the streamable HTTP app (cached).
  - Five MCP tools, each returns a plain dict: `search_memory(query: str, limit: int = 8)`, `get_memory(memory_id: str)`, `list_recent(limit: int = 20)`, `add_memory(title: str, content: str, tags: list[str] | None = None)`, `delete_memory(memory_id: str)`. Read tools require `memory:read`; `add_memory`/`delete_memory` require `memory:write`. Every call appends a `MemoryAccessLog` row with the resolved principal, the action, affected `memory_id`(s), and `detail` (e.g. `{"query": q, "returned": n}`). Auth failure / missing scope returns `{"error": "..."}` dicts (never raises to the client).
  - Before implementing, fetch the current `mcp` python-sdk docs (context7: library `/modelcontextprotocol/python-sdk`) and verify: `FastMCP` stateless flags, how a tool receives the HTTP request (`Context.request_context.request`), and the lifespan/mount pattern for `streamable_http_app()`. Adjust the code below to the verified API if names differ — record the verified pattern in `app/mcp_hub/server.py`'s docstring.
- Mount pattern (adjust to verified SDK docs):

```python
# app/main.py
from app.config import settings

if settings.MCP_HUB_ENABLED:
    from app.mcp_hub.server import get_mcp_app

    app.mount("/mcp", get_mcp_app())
```

and in the existing `lifespan`, start/stop the MCP session manager per the verified SDK pattern (for `stateless_http=True` this is usually a no-op, but run the app's own lifespan context if the SDK requires it).

- [ ] **Step 1: Add dependency** — add `"mcp>=1.9.0"` to `pyproject.toml` dependencies; `pip install -e .` (or `pip install "mcp>=1.9.0"`) and record the installed version in the task notes.
- [ ] **Step 2: Verify SDK pattern** — use context7 (`/modelcontextprotocol/python-sdk`, queries: "streamable http mount FastMCP into FastAPI", "stateless http", "access HTTP request inside tool Context") and write the verified pattern into `server.py`'s docstring before coding tools.
- [ ] **Step 3: Write the failing test** — `tests/mcp_hub/test_tools.py`. Tools are tested through their plain function bodies with a fake DB session + monkeypatched retriever (CI-safe, no real Chroma). Structure:

```python
"""Unit tests for MCP hub tools: scope enforcement + ledger writes.

The DB is faked; the retriever is monkeypatched. These tests call the tool
implementations directly (the thin FastMCP wrappers are exercised by the
wiring test in test_server.py).
"""
from __future__ import annotations

import uuid

import pytest

from app.mcp_hub import tools as hub_tools
from app.mcp_hub.identity import AgentPrincipal
from app.services.agent_token_service import generate_token, hash_token


def _principal(scopes: tuple[str, ...]) -> AgentPrincipal:
    return AgentPrincipal(
        user_id=uuid.uuid4(),
        agent_client_id=uuid.uuid4(),
        name="TestAgent",
        scopes=frozenset(scopes),
    )


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.added = []
        self.committed = 0

    async def execute(self, _stmt):
        return _FakeResult(self.rows)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed += 1

    async def refresh(self, _obj):
        return None


@pytest.fixture()
def reader(monkeypatch):
    p = _principal(("memory:read",))
    db = _FakeDB()
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: p)
    monkeypatch.setattr(hub_tools, "_session", lambda: _FakeCtx(db))
    return p, db


@pytest.fixture()
def writer(monkeypatch):
    p = _principal(("memory:read", "memory:write"))
    db = _FakeDB()
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: p)
    monkeypatch.setattr(hub_tools, "_session", lambda: _FakeCtx(db))
    return p, db


class _FakeCtx:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *exc):
        return False


async def test_search_requires_read_scope(monkeypatch):
    p = _principal(())  # no scopes
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: p)
    result = await hub_tools.search_memory(query="postgres")
    assert result == {"error": "scope memory:read required"}


async def test_search_returns_results_and_writes_ledger(reader, monkeypatch):
    p, db = reader
    memory = uuid.uuid4()
    monkeypatch.setattr(hub_tools, "_recall_memory_ids", _fake_recall([memory]))
    result = await hub_tools.search_memory(query="postgres indexing")
    assert result["results"][0]["id"] == str(memory)
    ledger = [o for o in db.added if type(o).__name__ == "MemoryAccessLog"]
    assert ledger and ledger[0].action == "mcp_search"
    assert ledger[0].detail["query"] == "postgres indexing"


async def test_add_memory_requires_write_scope(reader):
    result = await hub_tools.add_memory(title="t", content="c")
    assert result == {"error": "scope memory:write required"}


async def test_add_memory_creates_and_logs(writer):
    p, db = writer
    result = await hub_tools.add_memory(title="Decision", content="Use pgvector", tags=["db"])
    assert result["title"] == "Decision"
    assert any(type(o).__name__ == "Memory" for o in db.added)
    assert any(type(o).__name__ == "MemoryAccessLog" and o.action == "mcp_add" for o in db.added)
    assert db.committed >= 1


async def test_delete_requires_write_scope(reader):
    result = await hub_tools.delete_memory(memory_id=str(uuid.uuid4()))
    assert result == {"error": "scope memory:write required"}
```

Implement `_fake_recall` as a module-level helper returning an async closure mapping a query to `[(memory_id, 0.9)]`-style results. The point of the fixtures: tool bodies must call `hub_tools._current_principal()` and `hub_tools._session()` (thin indirections defined in `tools.py` so tests can monkeypatch them); every tool resolves the principal itself, checks scope, then does the work and appends a `MemoryAccessLog`.

- [ ] **Step 4: Run to verify it fails** — `pytest tests/mcp_hub/test_tools.py -v` → FAIL (ImportError/AttributeError).
- [ ] **Step 5: Implement `app/mcp_hub/tools.py`**. Key shape (full bodies required in the real file):

```python
"""MCP memory tools — the hub's public surface to agents.

Design rules:
  - Every tool resolves its own AgentPrincipal (from the MCP Context's HTTP
    request headers) and enforces scopes; failures return {"error": ...}.
  - Every tool appends a MemoryAccessLog row — the ledger is the product.
  - Reads bump nothing (salience bumping stays in the chat pipeline); writes
    reuse index_new_memory so embedding + graph stay best-effort.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.database import AsyncSessionLocal
from app.mcp_hub.identity import (
    ACTION_ADD, ACTION_DELETE, ACTION_GET, ACTION_LIST, ACTION_SEARCH, AgentPrincipal,
)
from app.models.agent_client import AgentClient
from app.models.memory import Memory
from app.models.memory_access_log import MemoryAccessLog
from app.retrieval.memory.write_back import index_new_memory, safe_delete_from_chroma
from app.services.agent_token_service import hash_token

log = logging.getLogger(__name__)


def _current_principal() -> AgentPrincipal | None:  # monkeypatched in tests
    raise RuntimeError("_current_principal must be patched or provided by the MCP context")


def _session():  # monkeypatched in tests
    return AsyncSessionLocal()
```

…plus the actual tool implementations. For the SDK context path, each real FastMCP tool receives `ctx: Context` and derives the token via `ctx.request_context.request.headers`; the exported module-level functions (`search_memory(query, limit=8)` etc. used by tests) do the work given an `AgentPrincipal | None` resolved by the thin FastMCP wrappers in `server.py`. Scope failures return exactly `{"error": "scope memory:read required"}` / `{"error": "scope memory:write required"}`. `search_memory` filters `Memory.user_id == principal.user_id` ordered by `salience desc, captured_at desc`, `limit` capped at 20, returns `{"results": [{"id", "title", "content", "salience", "captured_at"}], "query": ...}`; `add_memory` creates the `Memory` (`source_type="mcp_agent"`, `source_ref=f"agent:{principal.name}"`), commits, calls `await index_new_memory(memory)` in a try/except (best-effort), logs `ACTION_ADD` with `detail={"title": ..., "memory_id": ...}`; `delete_memory` verifies ownership, deletes the row, calls `safe_delete_from_chroma`, logs `ACTION_DELETE`; `get_memory`/`list_recent` log `ACTION_GET`/`ACTION_LIST` with the memory id(s) in `detail`.

- [ ] **Step 6: Implement `app/mcp_hub/server.py`** — builds `FastMCP("orivory-memory", stateless_http=True, json_response=True)`, registers five `@mcp.tool()` wrappers that (a) extract the token from `ctx.request_context.request.headers`, (b) open `AsyncSessionLocal()`, (c) `resolve_principal`, (d) call the `tools.py` function bodies with the principal, returning tool dicts verbatim. `get_mcp_app()` returns `mcp.streamable_http_app()` (module-level cached). Include the verified-from-docs mount/lifespan notes in the docstring.
- [ ] **Step 7: Wire into `app/main.py` + `app/config.py`** per the mount pattern above; add `MCP_HUB_ENABLED: bool = True` next to the other flags in `app/config.py`; document it in `.env.example`.
- [ ] **Step 8: Run to verify it passes** — `pytest tests/mcp_hub -v` → PASS.
- [ ] **Step 9: Smoke the server boots** — `python -c "from app.main import app; print([r.path for r in app.routes if 'mcp' in getattr(r, 'path', '')])"` → prints `/mcp` mount. (Full live MCP handshake is deferred to the integration suite — noted in the plan's follow-ups.)
- [ ] **Step 10: Lint + commit** — `ruff check app tests && pytest tests/mcp_hub tests/api -q`; `git commit -m "feat: MCP memory hub server (scoped tools + access ledger)"`.

---

### Task 6: Ledger read model helper (shared by API + future receipts)

**Files:**
- Create: `app/services/access_ledger_service.py`
- Test: `tests/services/test_access_ledger_service.py`

**Interfaces:**
- Produces: `async def list_entries(db, user_id, *, agent_client_id=None, limit=50, offset=0) -> tuple[list[MemoryAccessLog], int]` (newest first; validates `limit` in [1, 200]); `async def count_for_client(db, user_id, agent_client_id) -> int`. `app/api/v1/agents.py`'s ledger endpoint may be refactored to call this (do it in this task and keep the endpoint's response schema unchanged).

- [ ] **Step 1: Write the failing test** — fake-DB style like Task 4 (`_FakeResult` supporting `.scalars().all()` and `.scalar_one()`), asserting ordering cap (`limit=min(limit,200)`) and user scoping.
- [ ] **Step 2: Verify fail → implement → verify pass** — same TDD loop; queries use `select(MemoryAccessLog).where(MemoryAccessLog.user_id == user_id, ...)` ordered `created_at desc`.
- [ ] **Step 3: Refactor the ledger endpoint** in `app/api/v1/agents.py` to use the service; endpoint behavior unchanged.
- [ ] **Step 4: Lint + tests + commit** — `ruff check app tests && pytest tests/services tests/api -q`; `git commit -m "refactor: extract access ledger service"`.

---

### Task 7: Docs + environment wiring

**Files:**
- Modify: `docs/API.md` (new "Agent Clients & MCP Hub" section: registration flow, token-once warning, scopes, ledger endpoint, MCP endpoint URL + headers, example `claude_desktop_config.json` snippet pointing at `http://localhost:8000/mcp` with the token header)
- Modify: `README.md` (short "Open Memory Hub (MVP)" section under Key Features)
- Modify: `docs/ideas/open-memory-hub.md` (check off MVP items 1 + 4 with a status note)

- [ ] **Step 1: Write docs** (content per Interfaces; include the token-once warning and a curl example for `POST /api/v1/agents`).
- [ ] **Step 2: Update the one-pager** MVP checklist (items 1 and 4 → "done (backend); UI ledger page pending").
- [ ] **Step 3: Full verification** — `ruff check app tests && pytest -q` (the CI-safe suite) → all green.
- [ ] **Step 4: Commit** — `git commit -m "docs: MCP hub registration, scopes, ledger + one-pager status"`.

---

## Follow-ups (explicitly NOT in this plan)

- Access Ledger UI page in `frontend/` (MVP item 4's UI half).
- Erasure receipts v0 (MVP item 5) — builds on `MemoryAccessLog` + cascade delete; own plan.
- Import paths (MVP item 3) and ClawHub skill (item 2) — own plans.
- Live integration smoke test for the MCP handshake (needs running server; belongs with the existing integration-suite debt).
