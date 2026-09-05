# Orivory Documentation

Start here. Everything else is organized by purpose:

## For users

| Doc | Contents |
|---|---|
| [../README.md](../README.md) | Product overview + quick start |
| [LITE_MODE.md](LITE_MODE.md) | One-container lite mode (SQLite, no external services) |
| [LOCAL_RUN_GUIDE.md](LOCAL_RUN_GUIDE.md) | Run the stack locally (dev mode, per-service) |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment |
| [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) | Day-2 ops: logs, backups rotation, common failures |
| [BACKUP_RESTORE.md](BACKUP_RESTORE.md) | Backup/restore procedures |
| [ONBOARDING.md](ONBOARDING.md) | Product onboarding flow design + tours |

## Reference

| Doc | Contents |
|---|---|
| [API.md](API.md) | Full REST + MCP reference (§13 MCP hub, §14 erasure receipts, §15 import paths) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the system works — memory spine, MCP hub, erasure, imports, agents, eval |
| [ROADMAP.md](ROADMAP.md) | Shipped milestones + open follow-ups |
| [../CHANGELOG.md](../CHANGELOG.md) | Notable changes per release |
| [../SECURITY.md](../SECURITY.md) | Responsible disclosure |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guide |

## Deep dives

| Doc | Contents |
|---|---|
| [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) | RAG eval framework + benchmarks |
| [RAG_TECHNIQUES.md](RAG_TECHNIQUES.md) | Retrieval techniques used in the pipeline |
| [architecture/rag_pipeline_optimization.md](architecture/rag_pipeline_optimization.md) | RAG pipeline hardening notes |
| [../eval/benchmarks/README.md](../eval/benchmarks/README.md) | Benchmark protocol + leaderboard hygiene |

## Research (why the hub direction)

| Doc | Contents |
|---|---|
| [research/USER_RESEARCH.md](research/USER_RESEARCH.md) | Segments, pains, willingness to pay (community evidence) |
| [research/MARKET_RESEARCH.md](research/MARKET_RESEARCH.md) | Competitor map, white space, monetization, distribution |
| [research/PLATFORM_LANDSCAPE.md](research/PLATFORM_LANDSCAPE.md) | Memory-hub prior art + gaps (OpenMemory sunset, governance hole) |
| [research/PAPERS_AGENT_MEMORY.md](research/PAPERS_AGENT_MEMORY.md) | Agent-memory literature + benchmark selection |
| [research/PAPERS_HCI_PRIVACY.md](research/PAPERS_HCI_PRIVACY.md) | PKM abandonment, proactive-AI guardrails, erasure literature |
| [research/FLAGSHIP_DEMAND_EVIDENCE.md](research/FLAGSHIP_Demand_EVIDENCE.md) | Demand evidence per flagship candidate |
| [research/ICP_AND_TIMING.md](research/ICP_AND_TIMING.md) | ICP reachability, competitive window, spec-vs-impl precedents |
| [research/OSS_GROWTH_PLAYBOOK.md](research/OSS_GROWTH_PLAYBOOK.md) | Contributor growth playbook (evidence-ranked) |
| [research/CLAWHUB_SKILL_FORMAT.md](research/CLAWHUB_SKILL_FORMAT.md) | OpenClaw skill format + publish flow |
| [research/DEVELOPMENT_RECOMMENDATIONS.md](research/DEVELOPMENT_RECOMMENDATIONS.md) | The original recommendation set (superseded in part by the hub pivot) |
| [ideas/open-memory-hub.md](ideas/open-memory-hub.md) | The pivot decision one-pager (flagship, ICP, MVP scope) |

## Plans

Implementation plans (SDD-executed, with review evidence in git history):
[../docs/superpowers/plans/](superpowers/plans/) — mcp-hub-spine,
erasure-receipts, import-paths, benchmark-scaffold.
