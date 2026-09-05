# Orivory — Open Memory Hub (one-pager quyết định)

**Ngày:** 2026-09-02 · **Quyết định của founder:** D1 Memory Hub · ICP OpenClaw-first · Implementation-first + benchmark công khai
**Bằng chứng:** 9 file research tại [docs/research/](../research/) — đặc biệt [PLATFORM_LANDSCAPE](../research/PLATFORM_LANDSCAPE.md), [FLAGSHIP_DEMAND_EVIDENCE](../research/FLAGSHIP_DEMAND_EVIDENCE.md), [ICP_AND_TIMING](../research/ICP_AND_TIMING.md), [PAPERS_AGENT_MEMORY](../research/PAPERS_AGENT_MEMORY.md), [PAPERS_HCI_PRIVACY](../research/PAPERS_HCI_PRIVACY.md), [OSS_GROWTH_PLAYBOOK](../research/OSS_GROWTH_PLAYBOOK.md).

---

## Problem Statement

**How might we** biến Orivory từ một "AI second brain app" thành **memory hub tự chủ mà mọi AI agent (OpenClaw, Claude, Cursor…) đều đọc/ghi được — có phân quyền, có receipts, có benchmark chứng minh** — trong khi cửa sổ cạnh tranh còn mở (~2–3 quý) và lực lượng chỉ là 1 founder + AI agents?

## Recommended Direction

**Định vị: "The user-owned memory hub any agent can read — with receipts."**
Orivory tách thành 3 lớp: **Hub core** (memory store salience/decay + KG + hybrid retrieval + MCP server + per-agent permissions/audit + erasure receipts + portable export) → **Surfaces** (second-brain app = client đầu tiên; digest; graph) → **Ecosystem** (ClawHub skill, SDK, spec sau này). Thiết kế được validate độc lập bởi MemOS, Generative Agents và HippoRAG 2; không hệ thống self-hosted nào hiện kết hợp quality + governance + portability — đó là khoảng trống tích hợp của Orivory.

**Wedge = nỗi đau memory loss của agents, governance = khác biệt hoá.**
Cầu đã đo được: OpenClaw issues #3922 ("dementia effect"), #5429 ("mất ~45 giờ context"), cụm 5 issues đòi capture-before-compaction; claude-code #39961 ("50–75% thời gian mất vì lặp lại"). Governance/permissions không phải compliance story — là phòng thủ attack surface đã chứng minh (MEXTRA: >30% extraction trong 50 prompts; SPORE: 80% qua tool-call channel). MCP không truyền caller identity → phân quyền per-client là việc **phải giải ở tầng hub** — chính là chỗ Orivory sở hữu.

**Phân phối: OpenClaw-first.** Discord 174K, r/openclaw 131K, ClawHub 10.7K+ skills; chủ đề của ta đã có 126 mentions trong #showcase; cơ chế adoption rẻ đã chứng minh (Postiz: 1 skill trong bài X viral → +$40K MRR). Second-brain app giữ nguyên đón knowledge workers; import Rewind/Limitless/OpenRecall là lối phụ rẻ đón refugee capture.

**Chất lượng = bằng chứng công khai.** Công bố **LongMemEval-S (primary)** + **MemoryAgentBench (secondary — benchmark duy nhất chấm selective forgetting, chưa hệ thống nào pass)** với protocol rõ ràng; tránh bẫy LoCoMo (tranh cãi Mem0↔Zep cho cùng một hệ thống: 65.99 → 75.14 → 58.44 → 94.7). Spec/portability: ship trước (MCP + export + documented permission model = de facto spec artifacts), đề xuất chuẩn hoá qua AAIF/LF chỉ sau khi có adoption (precedent MCP: ship 11/2024 → LF 12/2025).

## Key Assumptions to Validate

- [ ] **A1 — Người dùng OpenClaw sẽ cài hub ngoài thay vì chờ upstream Memory v2.** Test: ClawHub install rate + #showcase engagement trong 60 ngày. Nguy cơ: upstream hấp thụ (doc "Workspace Memory v2" đã validate salience/decay) → phải đạt adoption trước cuối quý 2.
- [ ] **A2 — Pain (memory loss) thắng văn hoá "files are enough".** Test: tỷ lệ click từ issues/threads sang benchmark page; reaction tại r/openclaw + Show HN.
- [ ] **A3 — Governance có pull khi gắn với attack surface.** Test: A/B landing (pain-led vs governance-led); engagement với access ledger sau khi user connect ≥2 agents.
- [ ] **A4 — Multi-agent usage thật sự xảy ra.** Test: ≥2 MCP clients connected per install trong 30 ngày (instrument ngay từ MVP).
- [ ] **A5 — Solo + AI agents giữ được tốc độ.** Test: shipping cadence 6 tuần đầu; áp dụng OSS playbook (7-day ack, public scope, GitHub Projects roadmap) để tránh bẫy Dokploy.

## MVP Scope (6–8 tuần)

1. ✅ **MCP server** — read/write memory, per-client endpoint tokens (giải caller-identity), Ollama/BYO-LLM. (backend done 2026-09-02; UI ledger page pending)
2. **ClawHub skill + 1-line install** — `docker compose up` tự chẩn đoán; import memory từ OpenClaw session logs.
3. ✅ **Import paths** — Rewind/Limitless/OpenRecall exports; ChatGPT/Claude/Gemini memory exports (PAM mappings). (backend done 2026-09-04: ChatGPT/Claude/generic/PAM adapters + `POST /api/v1/imports`; Rewind/Limitless adapter blocked on official export format — SQLCipher; Gemini/Copilot adapters = follow-ups; UI upload page pending)
4. ✅ **Permissions v0 + Access Ledger** — per-agent read/write scope; UI "AI nào đã đọc gì, khi nào". (backend done 2026-09-02; UI ledger page pending)
5. ✅ **Erasure receipts v0** — cascade deletion + verification report (RAG-store deletion: literature xác nhận sạch hơn weight-level; adversarially verified). (backend done 2026-09-02; deeper adversarial verification + entity pruning = follow-ups)
6. **Benchmark page** — LongMemEval-S + MemoryAgentBench, protocol công khai, chạy trong CI.
7. **Second-brain app giữ nguyên làm client đầu tiên**; digest tuân thủ guardrails từ papers (batched morning/evening, "should-I-speak" gate, action-attached).

## Not Doing (and Why)

- **Không lead bằng proactive digest** — ChatGPT Pulse chết sau ~9 tháng; literature: chỉ sống khi action-attached + user-configured. → feature, không flagship.
- **Không rebuild capture pipeline OS-level** — screenpipe (21.4K★, YC S26) chiếm slot; chỉ làm import destination.
- **Không làm graph UI mặt tiền** — consensus "beautiful but useless"; graph = engine dưới retrieval (+7–20% multi-hop khi ở trong graph).
- **Không đi sales compliance/enterprise** — unreachable pre-PMF, funded SaaS đã chiếm lane; permissions/audit để làm khác biệt hoá + upsell sau.
- **Không viết spec-first, không mời foundation ngay** — 6 spec chết + Solid 10 năm; mọi precedent thắng đều impl-first.
- **Không đụng meeting-notes, team-first, chat-with-docs positioning** — từ research vòng 1.
- **Không bounty/Hacktoberfest/RFC process ngay** — negative-EV ở solo scale (OSS playbook); chỉ good-first-issues + CONTRIBUTING + devcontainer.

## Open Questions

- OpenClaw upstream "Workspace Memory v2" sẽ ship gì, khi nào? (theo dõi #28930 + research doc của họ)
- Hosted tier định giá thế nào sau khi có dữ liệu compute của digest/agents?
- Giữ MIT thuần khiết hay Dokploy-style `proprietary/` cho enterprise sau này?
- Zalo/VN wedge — sau English PMF, multilingual embeddings (bge-m3) có nên có sớm từ MVP?

## North Star Metrics

≥2 MCP clients connected per install trong 30 ngày · ClawHub installs · LongMemEval-S score công bố · D30 retention ≥ 25% · digest open-rate > 40% (guardrail, không phải hero).
