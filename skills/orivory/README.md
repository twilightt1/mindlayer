# Orivory Memory — OpenClaw skill

The OpenClaw integration for [Orivory](../../README.md), the self-hosted AI
memory hub. This folder is a [ClawHub](https://docs.openclaw.ai/clawhub/skill-format)-publishable
skill: it teaches agents how to use Orivory's six MCP memory tools well and
walks the user through connecting the MCP endpoint.

> **Heads-up:** skills cannot declare MCP endpoints (the skill format has no
> field for it). The actual tool connection lives in your OpenClaw
> `mcp.servers` config — see the Quick Start in [SKILL.md](SKILL.md) or the
> copy-paste block below.

```json
{
  "mcp": {
    "servers": {
      "orivory": {
        "url": "http://localhost:8000/mcp",
        "transport": "streamable-http",
        "headers": { "Authorization": "Bearer ${ORIVORY_TOKEN}" }
      }
    }
  }
}
```

## Layout

| File | Purpose |
|---|---|
| `SKILL.md` | Agent-facing runbook (frontmatter manifest + quick start + core tasks) |
| `examples/` | Three full prompt workflows: remember, recall, proactive digest |
| `references/tool-catalog.md` | All six tools: args, scopes, when to use which |
| `references/error-handling.md` | 401 / empty-result / timeout / 422 runbook |

## Publishing

```bash
npm i -g clawhub
clawhub login
clawhub skill publish ./skills/orivory \
  --slug orivory-memory \
  --categories integrations,knowledge \
  --topics "memory,second-brain,mcp,self-hosted"
```

Every release runs ClawHub's automated security analysis (SkillSpector +
VirusTotal + ClawScan) — keep secrets out of the skill content and declare
every env var you reference.
