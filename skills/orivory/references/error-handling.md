# Error handling runbook — Orivory memory tools

## 401 Unauthorized (token rejected)

Cause: the agent token was revoked, expired, or never set.

1. Tell the user: "My Orivory access token was rejected — it may have been revoked."
2. The user re-registers: `POST /api/v1/agents` → new `oa_...` token (shown once).
3. User updates `ORIVORY_TOKEN` in the OpenClaw runtime env (not shell profile).
4. Re-probe: `openclaw mcp doctor orivory --probe`.

Do not retry the same call more than once — a revoked token stays revoked.

## Empty results (search returns nothing)

Not an error. Say: "I don't recall that in your memories." Then offer:
- a broader query (fewer words),
- saving the fact now (`add_memory`).

Never pad the answer from general knowledge while presenting it as memory.

## Timeout / connection refused

Orivory may be starting or down (`docker compose up` state). Suggest:

```bash
openclaw mcp doctor orivory --probe
curl -s http://localhost:8000/health
```

If `/health` answers but `/mcp` doesn't, the user's `mcp.servers` URL or
transport is wrong — re-check the Quick Start block in SKILL.md.

## 422 invalid memory id

Ids are UUIDs. If you must pass an id you read earlier, pass it verbatim —
do not truncate, re-format, or "helpfully" shorten it. On repeated 422,
re-run `search_memory` to get a fresh id.

## 413 payload too large (writes)

`add_memory` content is capped (10k chars is the memory cap; the upload cap
applies to imports). Split long material into multiple titled memories
instead of one giant blob — titles are what search ranks on.

## "I'm not sure which memory to forget"

For erasure intent, list the candidates (`search_memory`), show titles, and
ask the user to pick. `forget_memory` cascades children, links and vectors
and is receipted — but the receipt does not ask "are you sure?" for you.
