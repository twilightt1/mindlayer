# ClawHub Skill Format & OpenClaw MCP Integration — Research for the Orivory Skill

**Date compiled:** 2026-09-03
**Prepared for:** Orivory (MIT-licensed, self-hosted AI second brain — FastAPI + Next.js, LangGraph corrective RAG, salience/decay memory store, knowledge graph, connectors, team workspaces; ships an MCP memory server that OpenClaw agents should be able to use)
**Method:** 11 web searches/fetches via Exa against primary sources — official docs at docs.openclaw.ai, the openclaw/clawhub and openclaw/openclaw GitHub repos, and the openclaw/skills catalog (plus third-party mirrors where noted). Every factual claim carries an inline source URL. Nothing in this document is inferred beyond what sources state; the "Minimal viable Orivory skill package" section is explicitly marked as a proposal, not fact.

---

## 1. What is a ClawHub skill? (file format, layout, versioning)

**ClawHub is the public skill registry for OpenClaw.** It publishes, versions, and searches "text-based agent skills (a `SKILL.md` plus supporting files)", with moderation hooks and vector search. It is a free service where all skills are public and visible to everyone ([docs.openclaw.ai/clawhub](https://docs.openclaw.ai/clawhub), [openclaw/clawhub README](https://github.com/openclaw/clawhub)).

**A skill is a folder.** Required: `SKILL.md` (lowercase `skill.md` and legacy `skills.md` also accepted). Optional: any supporting regular files, `.clawhubignore` (ignore patterns for publishing; legacy `.clawdhubignore`), `.gitignore` (also honored) ([docs.openclaw.ai/clawhub/skill-format](https://docs.openclaw.ai/clawhub/skill-format)).

**`SKILL.md` is Markdown with optional YAML frontmatter**; the server extracts metadata from frontmatter during publish, and `description` is used as the skill summary in UI/search. For portable Agent Skills, `name` should match the parent directory and use 1–64 lowercase letters, numbers, or hyphens. ClawHub keeps the routable slug and catalog display name separate, so existing names from other clients remain publishable ([skill-format](https://docs.openclaw.ai/clawhub/skill-format)).

**Frontmatter fields (full reference from official docs):**

- **Required:** `name`, `description` (per [tools/skills SKILL.md reference](https://docs.openclaw.ai/tools/skills), [tools/creating-skills](https://docs.openclaw.ai/tools/creating-skills), [skill-creator skill](https://github.com/openclaw/openclaw/blob/main/skills/skill-creator/SKILL.md))
- **Basic:** `name`, `description`, `version` (semver) — shown in the "Basic frontmatter" example ([skill-format](https://docs.openclaw.ai/clawhub/skill-format))
- **OpenClaw runtime metadata under `metadata.openclaw`** (aliases: `metadata.clawdbot`, `metadata.clawdis`) with the full field table:

| Field | Type | Description |
| --- | --- | --- |
| `requires.env` | `string[]` | Required environment variables your skill expects |
| `requires.bins` | `string[]` | CLI binaries that must all be installed |
| `requires.anyBins` | `string[]` | CLI binaries where at least one must exist |
| `requires.config` | `string[]` | Config file paths your skill reads |
| `primaryEnv` | `string` | The main credential env var for your skill |
| `envVars` | `array` | Env var declarations with `name`, optional `required`, optional `description`; `required: false` for optional vars |
| `always` | `boolean` | If `true`, skill is always active (no explicit install needed) |
| `skillKey` | `string` | Override the skill's invocation key |
| `emoji` | `string` | Display emoji for the skill |
| `homepage` | `string` | URL to the skill's homepage or docs |
| `os` | `string[]` | OS restrictions (e.g. `["macos"]`, `["linux"]`) |
| `install` | `array` | Install specs for dependencies (kinds: `brew`, `node`, `go`, `uv`) |
| `nix` | `object` | Nix plugin spec |
| `config` | `object` | Clawdbot config spec |

  All from [skill-format full field reference](https://docs.openclaw.ai/clawhub/skill-format) and [clawhub repo docs/skill-format.md](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md).
- **Other optional keys** (from the OpenClaw SKILL.md reference): `user-invocable` (default `true`), `disable-model-invocation` (default `false`), `command-dispatch` (set `tool` to bypass the model), `command-tool`, `command-arg-mode` (default `raw`), `homepage`, `license`, `allowed-tools`, `metadata` ([tools/creating-skills optional frontmatter keys](https://docs.openclaw.ai/tools/creating-skills), [skill-creator](https://github.com/openclaw/openclaw/blob/main/skills/skill-creator/SKILL.md), [tools/skills](https://docs.openclaw.ai/tools/skills)).

**Parsing note (important for multi-line blocks):** OpenClaw follows the AgentSkills spec; frontmatter is parsed as YAML first, and if that fails it falls back to a single-line-only parser. Nested `metadata` blocks (including multi-line YAML mappings) are flattened to a JSON string and re-parsed as JSON5, "so the block form shown under Gating works". Use `{baseDir}` in the body to reference the skill folder path ([tools/skills SKILL.md format](https://docs.openclaw.ai/tools/skills)).

**No `config.json`/manifest for skills.** Skills have no separate manifest file — all metadata lives in `SKILL.md` frontmatter; only the separate plugin system (code plugins) uses `openclaw.plugin.json` + `package.json` with `openclaw.compat.pluginApi` and `openclaw.build.openclawVersion` ([docs.openclaw.ai/clawhub publish-before checklist](https://docs.openclaw.ai/clawhub/publishing)). The CLI does write install-state files after install (not part of the format): `skills/<slug>/.clawhub/origin.json` and workdir-level `.clawhub/lock.json` ([clawhub CLI docs](https://docs.openclaw.ai/clawhub/cli), [skill-format on-disk section](https://docs.openclaw.ai/clawhub/skill-format)).

**Skill files & limits (server-side):** publish accepts all regular files in the skill folder regardless of extension; bounded UTF-8 files can be previewed and included in bounded text analysis; other files keep exact bytes. Total bundle size limit 50 MB; embedding text includes `SKILL.md` + up to ~40 bounded UTF-8 files (best-effort cap) ([skill-format skill files section](https://docs.openclaw.ai/clawhub/skill-format)).

**Slugs:** derived from folder name by default; package scopes must match the ClawHub publisher handle exactly (handles: lowercase letters, numbers, hyphens, dots, underscores; must start/end with lowercase letter or number); package slugs must be lowercase and npm-safe, e.g. `@example.tools/demo-plugin` or `demo-plugin` ([skill-format slugs](https://docs.openclaw.ai/clawhub/skill-format)).

**Versioning + tags:** each publish creates a new version (semver); tags are string pointers to a version; `latest` is commonly used. Publishing skips unchanged content; a new skill starts at `1.0.0`, later changes automatically publish the next patch version; `--version` overrides ([skill-format versioning](https://docs.openclaw.ai/clawhub/skill-format), [publishing](https://docs.openclaw.ai/clawhub/publishing)).

**License:** all skills published on ClawHub are licensed `MIT-0` — anyone may use, modify, redistribute commercially, no attribution required; do not add conflicting license terms in `SKILL.md`, per-skill license overrides are not supported. Paid skills, per-skill pricing, paywalls, and revenue sharing are not supported; if a skill integrates a paid third-party service, document the external cost and required account in the instructions and env declarations ([skill-format license/paid skills](https://docs.openclaw.ai/clawhub/skill-format)).

**Install command:** users install with `openclaw skills install @owner/<slug>` (ClawHub-native), `openclaw skills install @owner/<slug> --version <v>`, `git:owner/repo[@ref]`, `./path/to/skill --as custom-name`, or `skills-sh:owner/repo/slug` (external skills.sh listing resolved to an exact GitHub commit, shown as "Not scanned by ClawHub"). `--global` targets the shared managed directory (`~/.openclaw/skills`), `--agent <id>` targets one agent workspace; update via `openclaw skills update --all`; trust envelope via `openclaw skills verify @owner/<slug>` printing the `clawhub.skill.verify.v1` JSON envelope ([docs.openclaw.ai/cli/skills](https://docs.openclaw.ai/cli/skills), [tools/skills install details](https://docs.openclaw.ai/tools/skills)).

**Where skills load from (precedence, highest first):** workspace `/skills` → project agent `/.agents/skills` → personal agent `~/.agents/skills` → managed/local `<state>/skills` → bundled → custodian → extra dirs (`skills.load.extraDirs` + plugin skills). Skills discovered wherever `SKILL.md` appears under a configured root, up to 6 levels deep; folder path is organization-only, name/slash-command come from `name` frontmatter ([tools/skills loading order](https://docs.openclaw.ai/tools/skills)).

> **Source-quality caveat:** several third-party mirrors (docs2.openclaw.ai, clawdocs.org, clawskills.sh, openclaw-ai.com, tenten.co, tryopenclaw.io, clawhub-skills.com) describe additional frontmatter (`author`, `runtime`, `timeout`, `permissions`, `triggers`, `tags`, `tools`, `config`, `depends`) — e.g. [clawdocs skill-development](https://clawdocs.org/guides/skill-development) and [tenten masterclass module-03](https://tenten.co/openclaw/en/docs/masterclass/module-03-skills-system). These fields do **not** appear in the official docs.openclaw.ai skill-format/creating-skills pages or the clawhub repo docs, so treat them as unofficial; build to the official format only.

---

## 2. How do skills reference external MCP servers?

**Short answer from official docs: a `SKILL.md` cannot itself declare or configure an MCP endpoint.** Skills are instruction files ("teach the agent how and when to use tools" — [tools/skills](https://docs.openclaw.ai/tools/skills)); the frontmatter field table contains env/binary gating and install specs but **no MCP URL/headers field** ([skill-format full field reference](https://docs.openclaw.ai/clawhub/skill-format)). MCP server connections live in OpenClaw's config under `mcp.servers`, managed via `openclaw mcp *` commands — "OpenClaw is the MCP client-side registry and later projects those servers into eligible runtimes" ([cli/mcp](https://docs.openclaw.ai/cli/mcp)). So an OpenClaw agent reaches an external MCP server through user config, not through the skill.

**How a skill bridges to that config today (observed patterns):**

1. **Skill teaches CLI usage, gate via env:** the Postiz skill declares `requires.env: ["POSTIZ_API_URL", "POSTIZ_API_KEY"]` in frontmatter and its body instructs the agent to run `postiz` CLI commands against the external API — the actual endpoint/key live in environment variables, not in the skill ([postiz SKILL.md as mirrored on playbooks.com](https://playbooks.com/skills/openclaw/skills/postiz), [clawskills.sh postiz listing](https://clawskills.sh/skills/nevo-david-postiz)).
2. **Skill instructs the user/agent to register the MCP server in `mcp.servers`:** the third-party ClawSkills publishing guide documents the pattern for "MCP-based skills" — the skill's Install section shows how to add the MCP server to `~/.openclaw/openclaw.json`, Configure covers credentials, Verify runs `openclaw mcp doctor` ([clawskills.io publishing guide](https://clawskills.io/docs/skill-publishing-guide)). (Third-party guide, not official docs — pattern observed, not mandated.)
3. **Skill ships inside/alongside a plugin that connects to MCP servers at startup:** the `lunarpulse/openclaw-mcp-plugin` community skill is a plugin that "connects to MCP servers and exposes its tools" — configured via `plugins.entries.mcp-integration.config.servers` with `transport: "http"` + `url` per server, registering a unified `mcp` tool with `list`/`call` actions ([openclaw/skills lunarpulse/openclaw-mcp-plugin](https://github.com/openclaw/skills/tree/main/skills/lunarpulse/openclaw-mcp-plugin)). The separate `yongxinchen/openclaw-mcp-adapter` plugin connects at gateway startup, calls `listTools()`, and registers each MCP tool as a native agent tool, supporting `transport: "http"` + `url` + `headers: {Authorization: "Bearer ${API_TOKEN}"}` ([yongxinchen/openclaw-mcp-adapter](https://github.com/yongxinchen/openclaw-mcp-adapter)). (Both are community examples, not official mechanisms.)

**Real example skill that wraps an external API/MCP server: Postiz.** The `postiz` skill in the official `openclaw/skills` catalog is a ~21 KB `SKILL.md` (26 files total including `examples/`, `README.md`, `FEATURES.md`, `QUICK_START.md`, `HOW_TO_RUN.md`, etc.) with frontmatter:

```yaml
---
name: postiz
description: Postiz is a tool to schedule social media and chat posts to 28+ channels X, LinkedIn, ...
homepage: https://docs.postiz.com/public-api/introduction
metadata: {"clawdbot":{"emoji":"🌎","requires":{"bins":[],"env":["POSTIZ_API_URL","POSTIZ_API_KEY"]}}}
---
```

…whose body instructs the agent to install the `postiz` npm CLI globally, then run `postiz integrations:list`, `posts:create`, `upload`, `analytics:*` etc., with detailed workflows, platform-specific settings JSON, media-upload-verify patterns, and `{"missing": true}` analytics resolution steps ([postiz SKILL.md mirror](https://playbooks.com/skills/openclaw/skills/postiz), [clawskills.sh listing with setup](https://clawskills.sh/skills/nevo-david-postiz)). Note it uses the `metadata.clawdbot` alias, and its gating requires **both** `POSTIZ_API_URL` and `POSTIZ_API_KEY` as env vars.

**Custom headers like `Authorization: Bearer`** are configured at the MCP-client level, not skill level: `mcp.servers.<name>.headers` accepts an arbitrary key-value map (e.g. `Authorization: "Bearer ${MCP_API_KEY}"` or `x-api-key`), with `${ENV_VAR}` substitution supported in `url` and all `headers` values config-wide ([cli/mcp SSE/HTTP transport field table](https://docs.openclaw.ai/cli/mcp), [openclaw issue #72196 closure — headers already implemented with source refs](https://github.com/openclaw/openclaw/issues/72196), [PR #71035 — env expansion in headers/url](https://github.com/openclaw/openclaw/pull/71035)). mTLS (`clientCert`/`clientKey`), OAuth (`auth: "oauth"` + `openclaw mcp login`), `sslVerify`, and `toolFilter` are also server-config fields ([tools/mcp](https://docs.openclaw.ai/tools/mcp)).

---

## 3. Publishing to ClawHub: exact flow, review criteria, and the Postiz case

**The flow (official):**

1. `npm i -g clawhub` (or `pnpm add -g clawhub`) — standalone ClawHub CLI ([docs.openclaw.ai/clawhub](https://docs.openclaw.ai/clawhub)).
2. `clawhub login` — browser login; token cached in `~/Library/Application Support/clawhub/config.json` (macOS) / `~/.config/clawhub/config.json` (Linux) / `%APPDATA%\clawhub\config.json` (Windows) ([clawhub CLI docs](https://docs.openclaw.ai/clawhub/cli)).
3. `clawhub skill publish ./my-skill --slug my-skill --name "My Skill" --owner <owner>` — publishing to an org uses `--owner`; omit to publish as the authenticated user. Publishing skips unchanged content; new skill starts at `1.0.0`, later changes auto-publish next patch; `--version` for explicit versions. Optional `--categories` (max 3, from a fixed slug list — e.g. `integrations` for "Connect services, fetch data, reconcile records, and operate APIs") and `--topics` (max 5, free-form, ≤48 chars each; reserved topics like `official`, `verified`, `trusted` are rejected). A skill first published without `--categories` is stored as `other` ([docs.openclaw.ai/clawhub/publishing](https://docs.openclaw.ai/clawhub/publishing)).
4. Catalog repos can publish via the reusable GitHub Actions workflow `openclaw/clawhub/.github/workflows/skill-publish.yml@main` with `clawhub_token` secret — it calls `skill publish` for each immediate skill folder under `root` (default `skills`); `dry_run: true` previews ([publishing — publishing from a catalog repo](https://docs.openclaw.ai/clawhub/publishing)). This is how the openclaw/skills catalog repo publishes its skills.
5. Validation gates: "ClawHub checks that your token can publish for that owner, validates the metadata, name, version, files, and source information, then stores the release and starts automated security checks. If validation fails, nothing is published. New releases may also stay out of normal install and download surfaces until review finishes." Upload gate: publishing requires a GitHub account ≥14 days old (applies to web uploads, CLI publish, GitHub import, and comments) ([publishing](https://docs.openclaw.ai/clawhub/publishing), [clawhub repo docs/security.md upload gate](https://github.com/openclaw/clawhub/blob/main/docs/security.md), [docs.openclaw.ai/clawhub](https://docs.openclaw.ai/clawhub)).

**Web GitHub import (alternative to CLI):** the web importer only discovers `SKILL.md`/legacy `skills.md` files in public, non-fork repositories owned by the signed-in GitHub account — no private repos, forks, archived/disabled repos, or third-party public repos ([skill-format GitHub import](https://docs.openclaw.ai/clawhub/skill-format)).

**Review criteria (documented):** ClawHub runs automated audits on published releases combining (1) SkillSpector, (2) VirusTotal malware telemetry, and (3) ClawScan risk analysis, which "reviews each release as an agent-facing artifact: instructions, metadata, declared permissions, files, capability signals, static scan signals, SkillSpector findings, VirusTotal telemetry, and publisher-provided context", using the OWASP Agentic Skills Top 10 as a lens (prompt injection, tool misuse, credential exposure, unsafe execution, memory/context poisoning, excessive agency). Audit statuses: `Pass` / `Review` / `Warn` / `Malicious` / `Pending` / `Error`; risk levels Low/Medium/High. The main question is coherence — "do the name, summary, metadata, requested authority, and actual content line up with what users would reasonably expect?" Powerful behavior is fine if disclosed and proportionate. The skill-format page adds: security analysis checks declared metadata against actual behavior — an undeclared `TODOIST_API_KEY` reference is flagged as metadata mismatch ([docs.openclaw.ai/clawhub/security-audits](https://docs.openclaw.ai/clawhub/security-audits), [docs.openclaw.ai/clawhub/moderation](https://docs.openclaw.ai/clawhub/moderation), [skill-format "Why this matters"](https://docs.openclaw.ai/clawhub/skill-format)). Publisher guidance to reduce false positives: keep names/summaries/tags/changelogs accurate, declare required env vars and permissions, avoid obfuscated install commands, link to source, use dry runs, respond clearly to moderation questions ([moderation publisher guidance](https://docs.openclaw.ai/clawhub/moderation)).

**The Postiz case.** Postiz (open-source social-media scheduler, gitroomhq/postiz-app) published a skill on ClawHub under `nevo-david/postiz` (also mirrored as `openclaw-skills-postiz` on LobeHub, version 1.0.3, author "openclaw", 45 installs, and on playbooks.com as `openclaw/skills/postiz`). Install: `openclaw skills install @nevo-david/postiz` or `npx clawhub install postiz`. Setup: `export POSTIZ_API_KEY=...` (+ `POSTIZ_API_URL` for self-hosted); eligibility is checked automatically (skill gated on env vars); `openclaw skills list --eligible` verifies visibility. The skill's body teaches the agent the Postiz CLI's commands; Postiz's own marketing pages show the SKILL.md pattern (name/description/metadata with `requires.env` + `primaryEnv`-style gating). Postiz also maintains a first-party agent package `gitroomhq/postiz-agent` installable via `npx skills add gitroomhq/postiz-agent` — "When you install Postiz Agent globally, OpenClaw automatically discovers it by reading the bundled SKILL.md file." ([clawskills.sh postiz listing](https://clawskills.sh/skills/nevo-david-postiz), [postiz.com/agent](https://postiz.com/agent), [playbooks.com postiz mirror with full SKILL.md](https://playbooks.com/skills/openclaw/skills/postiz), [LobeHub mirror](https://lobehub.com/skills/openclaw-skills-postiz), [RapidDev Postiz-OpenClaw integration guide](https://www.rapidevelopers.com/openclaw-integrations/postiz)). The Postiz case demonstrates: vendor-published skill, gated purely on env vars, CLI wraps the vendor's REST API, extensive supporting docs bundled in the skill folder (26 files).

---

## 4. Skill quality bar: what top skills include

**Official signals (docs.openclaw.ai + openclaw repos):**

- **skill-creator (bundled skill in openclaw/openclaw)** teaches the official authoring contract: required frontmatter is `name` + `description` only; optional fields (`metadata`, `homepage`, `license`, `allowed-tools`, `user-invocable`, `disable-model-invocation`, `command-dispatch`, `command-tool`, `command-arg-mode`) should be added "only when they change runtime behavior or discovery". Structure: map shared ordered procedure to `SKILL.md`; "end every step with a checkable completion criterion and finish with verification"; keep routing conditions in `description`; map branch-only detail to `references/`, deterministic helpers to `scripts/`, output resources to `assets/`, optional UI metadata to `agents/`. Validate with `python {baseDir}/scripts/quick_validate.py <skill>` ([openclaw/openclaw skills/skill-creator/SKILL.md](https://github.com/openclaw/openclaw/blob/main/skills/skill-creator/SKILL.md)).
- **Best practices from the official creating-skills page:** be concise (instruct the model on what to do, not how to be an AI); safety first (if using `exec`, ensure prompts don't allow arbitrary command injection from untrusted input); test locally with `openclaw agent --message "..."` before sharing; browse ClawHub before building from scratch. `description` is shown to the agent and in slash-command discovery — one line, under 160 characters ([docs.openclaw.ai/tools/creating-skills](https://docs.openclaw.ai/tools/creating-skills)).
- **Postiz (flagship community skill) includes:** `SKILL.md` (21 KB of runbook-style instructions: core workflow steps, essential commands, common patterns, failure handling like `{"missing": true}` analytics resolution, media-upload-verify rule), plus `examples/` with `README.md` (18.7 KB), `FEATURES.md`, `QUICK_START.md`, `HOW_TO_RUN.md`, `INTEGRATION_SETTINGS_DISCOVERY.md`, `INTEGRATION_TOOLS_WORKFLOW.md`, `PROJECT_STRUCTURE.md`, `PROVIDER_SETTINGS*.md`, `PUBLISHING.md`, `SUMMARY.md`, `SUPPORTED_FILE_TYPES.md`, `SYNTAX_UPGRADE.md` — 26 files total ([playbooks.com postiz file listing](https://playbooks.com/skills/openclaw/skills/postiz)).
- **Security analysis quality bar:** declare every env var the skill uses under `requires.env`/`primaryEnv`/`envVars` — mismatches are flagged ([skill-format why-this-matters](https://docs.openclaw.ai/clawhub/skill-format)). Keep credentials out of skill content ("Skills attached to a shared session are inputs to that session, not secret storage" — [tools/skills personal skills section](https://docs.openclaw.ai/tools/skills)). Treat third-party skills as untrusted code; sandbox untrusted inputs ([tools/skills security note](https://docs.openclaw.ai/tools/skills)).
- **Community quality guidance (third-party, consistent with official):** the ClawSkills publishing guide requires a Quick Start with `### Install` / `### Configure` / `### Verify` subsections each containing fenced code blocks; an "Environment Variable Contract" table for skills with 2+ env vars; a Security & Guardrails section covering ≥3 topics (secrets handling, permissions/scopes, confirmation before risky actions, data minimization, network access disclosure, token revocation, etc.) for a badge; 3–5 troubleshooting entries; version-pinned installs (unpinned package installs are a hard fail); no `curl | bash` pipe-to-interpreter patterns; secrets go in OpenClaw runtime env sources, never shell-profile exports ([clawskills.io skill-publishing-guide](https://clawskills.io/docs/skill-publishing-guide)).
- **Skill template repo:** the official catalog `openclaw/skills` (which contains Postiz and the lunarpulse MCP plugin skill) serves as the de-facto template collection; the ClawHub docs' hello-world skill in `tools/creating-skills` is the minimal template ([github.com/openclaw/skills](https://github.com/openclaw/skills), [tools/creating-skills](https://docs.openclaw.ai/tools/creating-skills)). No separate official "skill-template" repo was found in the sources consulted.

---

## 5. OpenClaw MCP client config — how a user adds an external MCP server today

This is the more direct integration path for Orivory: **OpenClaw is itself an MCP client**; users register Orivory's MCP endpoint once and every OpenClaw agent gets the tools — no skill required for connectivity.

**Config location & shape:** MCP servers are configured in `~/.openclaw/openclaw.json` (JSON5 allowed) under `mcp.servers`. Each entry is either stdio (`command`, `args`, `env`) or remote HTTP. Canonical remote shape:

```json5
{
  mcp: {
    servers: {
      orivory: {
        url: "https://your-orivory-host/mcp",
        transport: "streamable-http",   // or "sse" (legacy)
        headers: {
          Authorization: "Bearer ${ORIVORY_TOKEN}",
        },
        connectionTimeoutMs: 5000,
        requestTimeoutMs: 20000,
        toolFilter: { include: ["search", "read_*"] },  // optional
        enabled: true,
      },
    },
  },
}
```

From [docs.openclaw.ai/tools/mcp — configure a server directly](https://docs.openclaw.ai/tools/mcp); field table from [cli/mcp — SSE/HTTP + Streamable HTTP transport](https://docs.openclaw.ai/cli/mcp): `url` (required), `transport` (`sse` | `streamable-http`), `headers` (arbitrary key-value map, e.g. auth tokens), `connectionTimeoutMs`, `requestTimeoutMs`, `auth: "oauth"` (credentials saved via `openclaw mcp login`), `sslVerify`, `clientCert`/`clientKey` (mTLS), `supportsParallelToolCalls`, `toolFilter.include/exclude`, `enabled`.

**Env substitution:** `${VAR_NAME}` is supported config-wide, including in `mcp.servers.*.url` and all `headers` values, resolved from the process environment at load; missing values preserve the placeholder so misconfiguration stays visible ([PR #71035 closure citing docs/gateway/configuration-reference](https://github.com/openclaw/openclaw/pull/71035), [issue #72196 closure — headers field with x-api-key example](https://github.com/openclaw/openclaw/issues/72196)). Sensitive values in `url`/`headers` are redacted in logs; `openclaw mcp doctor` warns when headers contain literal secrets so operators move them out of committed config ([cli/mcp](https://docs.openclaw.ai/cli/mcp)).

**Ways to add a server:**
- **Control UI:** Settings → MCP → Add server (pick transport: Streamable HTTP / SSE / Stdio; enter URL or command) — writes the `mcp.servers` entry through the Gateway; or from a chat composer: + → Connectors → Add MCP server… (requires admin; session-only or global scope) ([tools/mcp add from settings/composer](https://docs.openclaw.ai/tools/mcp)).
- **CLI:** `openclaw mcp add <name> --url https://... --transport streamable-http [--header ...] [--include 'search,read_*']` etc.; verify with `openclaw mcp doctor <name> --probe` (live probe — "Saving a definition proves nothing about reachability — the probe does"). Also `list`, `show`, `status`, `set`, `configure`, `tools`, `login`, `logout`, `reload`, `unset` ([tools/mcp add from CLI](https://docs.openclaw.ai/tools/mcp), [cli/mcp full command list](https://docs.openclaw.ai/cli/mcp)).
- **Note:** `list/show/set/unset` manage only OpenClaw-managed `mcp.servers` entries — mcporter servers (`config/mcporter.json`) are a separate registry not included here ([cli/mcp](https://docs.openclaw.ai/cli/mcp)).

**Gotchas:** the reserved server name `__proto__` is rejected; already-running Gateway/agent processes may need restart or `openclaw mcp reload` before picking up a new definition; changes under `mcp.*` hot-apply by disposing cached session MCP runtimes ([tools/mcp](https://docs.openclaw.ai/tools/mcp)). Tools exposed by connected MCP servers "go through the same tool-profile and tool-policy controls as everything else — connecting a server does not bypass your policy" ([tools/mcp opening](https://docs.openclaw.ai/tools/mcp)).

**Why this matters for Orivory:** a single `mcp.servers.orivory` entry (URL + `Authorization: Bearer ${ORIVORY_TOKEN}` header) makes Orivory's memory tools first-class agent tools in every OpenClaw runtime, with policy controls, tool filters, timeouts, and probe diagnostics — a strictly more native path than teaching a skill to call an API via CLI.

---

## Minimal viable Orivory skill package (PROPOSAL — not fact)

> The following is Orivory's own design proposal derived from the sourced facts above. Nothing here is an official OpenClaw/ClawHub requirement beyond what is cited in sections 1–5.

**Design decision: two artifacts, one repo.** The research shows (sections 2 & 5) that skills cannot configure MCP endpoints, while `mcp.servers` is the native path. So the proposal ships (a) the MCP endpoint config as the primary integration, and (b) a ClawHub skill that teaches agents *how to use Orivory's memory tools well* and walks the user through connecting the endpoint.

**File tree (skill lives at `skills/orivory/` in the Orivory repo, publishable via `clawhub skill publish`):**

```text
orivory/
└── skills/
    └── orivory/
        ├── SKILL.md                 # required — frontmatter + runbook body
        ├── .clawhubignore           # optional — excludes dev files from publish
        ├── README.md                # human-facing overview + MCP setup JSON
        ├── examples/
        │   ├── remember.md          # "save this decision to memory"
        │   ├── recall.md            # "what did we decide about X last week?"
        │   └── proactive-digest.md  # scheduled weekly digest workflow
        └── references/
            ├── tool-catalog.md      # every MCP tool: name, args, when to use
            └── error-handling.md    # 401/429/timeout/empty-result runbook
```

**Proposed `SKILL.md` frontmatter (all fields from the official reference, section 1):**

```yaml
---
name: orivory-memory
description: Persistent personal/team memory for OpenClaw agents — remember, recall, and curate long-term context via a self-hosted Orivory MCP server. Use when the user asks to remember, forget, recall past decisions, or surface related history.
version: 0.1.0
homepage: https://orivory.example   # real repo/docs URL
license: MIT-0                      # ClawHub default; do not conflict (see §1)
metadata:
  openclaw:
    primaryEnv: ORIVORY_TOKEN
    envVars:
      - name: ORIVORY_TOKEN
        required: true
        description: Bearer token for the user's self-hosted Orivory MCP endpoint.
      - name: ORIVORY_URL
        required: false
        description: Override endpoint URL if not set in mcp.servers config.
    emoji: "🧠"
---
```

**Proposed body structure** (modeled on Postiz's runbook pattern and skill-creator's "checkable completion criterion" rule): Quick Start → Connect the MCP server (the exact `mcp.servers` JSON block from §5, plus `openclaw mcp add` one-liner + `openclaw mcp doctor orivory --probe`) → Core tasks (natural-language prompts per ClawSkills guidance) → Tool catalog pointer → Error handling (`references/error-handling.md`) → Security notes (where the token lives, data minimization, what Orivory stores).

**Publish flow (per §3):** `clawhub login` → `clawhub skill publish ./skills/orivory --slug orivory-memory --owner <orivory-owner> --categories integrations,knowledge --topics "memory,second-brain,mcp,self-hosted"` → confirm audit status `Pass` on the ClawHub page. CI option: the reusable `skill-publish.yml` workflow against the Orivory repo.

---

## Key takeaways

- **ClawHub skill = a folder with `SKILL.md`** (YAML frontmatter: `name` + `description` required; `version`, `homepage`, `metadata.openclaw` gating/env/install specs, `os`, `emoji`, etc. optional) plus arbitrary supporting files, ≤50 MB total; every publish is a new semver version; all skills are MIT-0. ([skill-format](https://docs.openclaw.ai/clawhub/skill-format))
- **There is no `config.json` manifest for skills** — frontmatter is the manifest; only plugins (a separate surface) use `openclaw.plugin.json`. ([publishing](https://docs.openclaw.ai/clawhub/publishing))
- **Skills cannot configure MCP endpoints.** The frontmatter has no URL/headers field; MCP connections live in `~/.openclaw/openclaw.json` under `mcp.servers` with arbitrary `headers` (incl. `Authorization: Bearer ${TOKEN}`), OAuth, mTLS, and `toolFilter`. ([skill-format](https://docs.openclaw.ai/clawhub/skill-format), [cli/mcp](https://docs.openclaw.ai/cli/mcp))
- **The MCP client config is the more direct Orivory integration path**: one `mcp.servers.orivory` entry (streamable-http URL + Bearer header) exposes Orivory's memory tools to every OpenClaw agent as first-class tools under tool-policy controls; `openclaw mcp doctor orivory --probe` verifies reachability. ([tools/mcp](https://docs.openclaw.ai/tools/mcp))
- **A skill still adds real value on top**: it teaches the agent *when/how* to use Orivory (routing via `description`), bundles examples and error-handling runbooks, and gate-checks `ORIVORY_TOKEN` presence so it never loads without credentials. ([tools/skills](https://docs.openclaw.ai/tools/skills))
- **Publishing is CLI-first and free**: `npm i -g clawhub` → `clawhub login` → `clawhub skill publish ./skills/orivory --slug ... --owner ... --categories integrations,knowledge --topics ...`; GitHub-age gate (≥14 days) applies; catalog repos can automate via the `skill-publish.yml` reusable workflow. ([publishing](https://docs.openclaw.ai/clawhub/publishing))
- **Automated review is coherence-focused**: SkillSpector + VirusTotal + ClawScan risk analysis (OWASP Agentic Skills Top 10 lens) check that declared env/permissions match actual behavior — declare every env var the skill references or get flagged; `Pass`/`Review`/`Warn`/`Malicious` statuses with Low/Med/High risk levels. ([security-audits](https://docs.openclaw.ai/clawhub/security-audits))
- **Postiz is the model case**: vendor-published skill (`@nevo-david/postiz`) gated on `POSTIZ_API_KEY`/`POSTIZ_API_URL`, runbook-style 21 KB `SKILL.md` + 25 supporting doc files, installs via `openclaw skills install @nevo-david/postiz` — copy this pattern for Orivory. ([playbooks postiz mirror](https://playbooks.com/skills/openclaw/skills/postiz), [postiz.com/agent](https://postiz.com/agent))
