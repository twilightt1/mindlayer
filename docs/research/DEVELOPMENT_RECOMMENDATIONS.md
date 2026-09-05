# Orivory — Khuyến nghị hướng phát triển (tổng hợp User + Market Research)

**Ngày:** 2026-09-02
**Đầu vào:** [USER_RESEARCH.md](USER_RESEARCH.md) (desk research, ~25 truy vấn có nguồn) + [MARKET_RESEARCH.md](MARKET_RESEARCH.md) (21 truy vấn có nguồn, bản đồ 20+ đối thủ).
**Phạm vi:** khuyến nghị chiến lược + thứ tự thực hiện cho 90 ngày tới. Không thay thế [NEXT_PHASE_ROADMAP.md](../ROADMAP.md) (P0–P4 đã xong) — mà là phase tiếp theo sau P0–P4.

> **⚠️ Đã được cập nhật (2026-09-02, muộn hơn):** sau 6 file research bổ sung ([PLATFORM_LANDSCAPE](PLATFORM_LANDSCAPE.md), [OSS_GROWTH_PLAYBOOK](OSS_GROWTH_PLAYBOOK.md), [FLAGSHIP_DEMAND_EVIDENCE](FLAGSHIP_DEMAND_EVIDENCE.md), [ICP_AND_TIMING](ICP_AND_TIMING.md), [PAPERS_AGENT_MEMORY](PAPERS_AGENT_MEMORY.md), [PAPERS_HCI_PRIVACY](PAPERS_HCI_PRIVACY.md)) và quyết định của founder, hướng phát triển chính thức là **Open Memory Hub (D1) — ICP OpenClaw-first, implementation-first + benchmark công khai**. Xem one-pager quyết định tại [docs/ideas/open-memory-hub.md](../ideas/open-memory-hub.md). Các khuyến nghị H1–H5 dưới đây vẫn có hiệu lực nhưng được xếp lại: MCP server + capture friction lên trước, digest xuống thành feature hỗ trợ theo guardrails từ papers.

---

## 1. Tóm tắt điều hành

1. **Thời điểm tốt để ra mắt.** "AI second brain" self-hosted đang là khe trống thật: Khoj Cloud đóng cửa (4/2026), Reor bị archive, Smart Connections đẩy tính năng vào paywall ~$20/mo gây làn sóng rời bỏ, Logseq đình trệ. Một cộng đồng lớn "mồ côi" (r/selfhosted ~830K thành viên, +42%/năm) đang không có nhà mới rõ ràng.
2. **Không một đối thủ OSS nào có đủ stack của Orivory.** Onyx mạnh retrieval nhưng là enterprise-search; AnythingLLM có teams+agents nhưng không có memory/KG/digest; Karakeep có capture nhưng không có "não"; Mem0/Zep/Cognee có memory/KG nhưng chỉ là infra cho dev. **Sự tổng hợp chính là sản phẩm.**
3. **Đừng lead bằng chat-with-docs** (đã bão hòa — Open WebUI 150K★, AnythingLLM 65K★). Hãy lead bằng **proactive digest** — nỗi đau cấu trúc lớn nhất của cả category ("notes apps are where ideas go to die", NotebookLM "amnesiac by design") và hiện chỉ có Saner.ai (closed, beta, nhỏ) đi hướng proactive-first.
4. **Nỗi đau số 1 khiến người dùng bỏ đi là capture friction**, số 2 là chất lượng retrieval, số 3 là setup friction. Ba cái này quyết định sống còn hơn bất kỳ feature mới nào.
5. **Tiền nằm ở hosted convenience + compute định kỳ, không nằm ở donate.** Plausible ~$3.1M ARR, Ghost $10.8M ARR — 0% doanh thu từ self-hoster nhưng 100% trust từ họ. Digest/agents tiêu compute định kỳ = đơn vị thu phí tự nhiên.

---

## 2. Vì sao là bây giờ (bối cảnh thị trường)

| Tín hiệu | Bằng chứng |
|---|---|
| Khe trống "second brain" self-hosted | Khoj Cloud đóng 4/2026 ([app.khoj.dev](https://app.khoj.dev/)); Reor archived 8.6K★; Smart Connections paywall churn ([forum](https://forum.obsidian.md/t/alternatives-to-smart-connections/108886)) |
| Cộng đồng mục tiêu đang tăng nhanh | r/selfhosted ~830K (+42%/năm), r/LocalLLaMA ~815K (+54%), r/ObsidianMD ~359K (+47%), r/notebooklm ~148K (+183%) |
| Category đang được xác nhận bằng tiền | Mem0 $24M raise; Onyx $10M seed; Granola $125M Series C; NotebookLM 30M→110M visits/tháng trong 2025 |
| Trend agentic memory + MCP | MCP: 10K+ servers, 97M+ monthly SDK downloads, Linux Foundation governance; "proactive/agentic assistant" là trend 2026–2030 |

Chi tiết đầy đủ: [MARKET_RESEARCH.md §1–2, §6](MARKET_RESEARCH.md).

---

## 3. Người dùng mục tiêu (thứ tự ưu tiên)

| Ưu tiên | Segment | Vì sao | Bằng chứng chính |
|---|---|---|---|
| **ICP đầu tiên** | **Researcher / reader nặng RSS+clipper+Gmail** (kiểu NotebookLM/Recall demographic nhưng muốn self-host) | Không OSS nào ghép RSS + clipper + Gmail + RAG/memory; NotebookLM 110M visits chứng minh nhu cầu "chat với nguồn có trích dẫn" | [MARKET §3(e)](MARKET_RESEARCH.md) |
| **Sóng phản ứng đầu tiên** | Self-hoster / PKM privacy-first bị Khoj/Reor/Smart Connections bỏ lại | Đang orphaned, receptive với "kế nhiệm" đáng tin; r/selfhosted là kênh phân phối tốt nhất | Khoj postmortem; Reor HN 411 điểm |
| Mở rộng 1 | Developers / AI builders | Muốn MCP + agent-writable memory; chi trả infra cao nhất | Atomic được khen vì MCP day-one (HN) |
| Mở rộng 2 | Students / researchers phổ thông | $10/mo là điểm giá đã được chứng minh (Recall Plus, Mem) | r/notebooklm +183%/năm |
| **Tier 2 — KHÔNG phải đòn bẩy** | Teams nhỏ / gia đình | Free multi-user self-host đã là table stakes; Onyx sở hữu lane trả phí $20/user; Khoj sụp đổ vì cá cược team-cloud trước | [MARKET §3(d)](MARKET_RESEARCH.md) |

Chi tiết: [USER_RESEARCH.md §1 + Segments table](USER_RESEARCH.md).

---

## 4. Năm hướng phát triển được khuyến nghị (xếp theo mức ưu tiên)

### H1 — Đưa Proactive Digest lên làm hero feature 🔵 (khác biệt hóa lớn nhất)

**Là gì:** "Bộ não của bạn tự viết thư cho bạn mỗi sáng" — daily/weekly briefing: theme trong tuần, "on this day", liên kết mới giữa thực thể, gợi ý revisit. Email + in-app + (sau) Telegram/Zalo push.

**Vì sao:**
- Nỗi đau cấu trúc số 1 của category là "dumping ground / landfill of stale notes / organizing tax" — đúng cái digest giải quyết ([HN #46826277](https://news.ycombinator.com/item?id=46826277), [USER §3](USER_RESEARCH.md)).
- Chỉ có Saner.ai đi proactive-first và họ closed/beta/nhỏ — "your brain emails you every morning" **chưa ai chiếm trong OSS** ([MARKET §3(b)](MARKET_RESEARCH.md)).
- Là bề mặt kiếm tiền tự nhiên: digest + proactive agents = **compute định kỳ** → subscription logic mà self-hoster khó tự replicate (Plausible pattern).

**Cơ sở trong repo:** P2.1 salience loop + P2.2 digest endpoint đã xong; SendGrid path tồn tại. Việc còn lại là **nâng digest từ endpoint lên sản phẩm**: scheduled email delivery, lựa chọn tần suất, chất lượng briefing (LLM-generated themes), onboarding đưa user vào digest ngay ngày đầu.

### H2 — Giảm capture friction xuống dưới 2 giây 🔴 (nỗi đau số 1)

**Là gì:** bộ capture đa kênh, ưu tiên theo chi phí/th doPost:
1. **Telegram + Zalo bot** (Telegram trước — bot API rẻ; Zalo sau cho VN). Cả ecosystem bot DIY Telegram→Obsidian tồn tại chỉ vì sản phẩm lớn không làm — đó là tín hiệu cầu sẵn.
2. **Email ingest** (forward vào địa chỉ riêng của user) — Karakeep #183, Memento xây cả sản phẩm trên cái này.
3. **Mobile PWA + share-sheet** (backlog #4) — Karakeep #1077 (51👍, "dealbreaker").
4. Browser extension đã có web clipper → harden + đưa lên hàng đầu trong onboarding.

**Vì sao:** capture friction là nguyên nhân bỏ đi được trích dẫn nhiều nhất — "the killer", "the entire game" ([USER §3](USER_RESEARCH.md)). Non-brand: connector infra (dispatcher, sync_cursor, dedup) đã có sẵn sau P0–P1.

### H3 — Biến chất lượng retrieval thành bằng chứng công khai 🟢 (uy tín + phân biệt checkable)

**Là gì:** public benchmark/eval page (đánh giá retrieval + grounded answer trên dataset cố định, cập nhật CI), citation luôn hiển thị, trả lời "tôi không nhớ" khi context thiếu, grounding confidence hiện trong UI.

**Vì sao:** mọi đối thủ đều bị "đốt công khai" vì retrieval yếu/hallucination (Obsidian Copilot #1224, Smart Connections #305/#1287, NotebookLM regression, Reor "so weak it was nonsensical"). Onyx thắng mindshare doanh nghiệp bằng cách publish blind evals — đó là playbook. Orivory đã có corrective RAG + hybrid search + eval harness + grounding confidence (P3) — chỉ thiếu **khoe ra**.

**Cơ sở trong repo:** `eval/` harness + `agent_trace.grounding` + `/admin/quality/trend` đã tồn tại. Cần: dựng benchmark public trang tĩnh + đưa confidence/citations lên UI chat.

### H4 — Ship MCP server ngay từ đầu 🔵 (kênh phân phối rẻ nhất)

**Là gì:** MCP server expose read/write memory (search, save_note, recall, digest) — dùng được trong Claude Desktop/ChatGPT/Cursor.

**Vì sao:** 97M+ monthly SDK downloads; dev segment đòi hỏi; Atomic được khen ngay trên HN vì MCP day-one; mọi đối thủ OSS nghiêm túc (Khoj, AnythingLLM, Trilium, Graphiti, Cognee) đều đã ship. Đây cũng là future paid/hosted hook (API-first memory store).

**Cơ sở trong repo:** REST API đầy đủ → wrap thành MCP server là việc nhỏ (days, không weeks).

### H5 — Zero-friction setup 🟠 (điều kiện ra mắt, không phải feature)

**Là gì:** `docker compose up` chạy được ngay lần đầu với self-diagnosis: health checks, indexing progress hiển thị, error messages actionable; BYO-LLM Ollama/OpenAI-compatible là mặc định; import từ Obsidian/markdown vault.

**Vì sao:** setup hell là top-3 pain ("90% của Open WebUI problems là một networking mistake"; AnythingLLM cần cả trang troubleshooting riêng cho Ollama URL). Obsidian/markdown import là cánh cửa đón refugee từ Smart Connections/Khoj — và "plain Markdown, leave anytime" là trust lever chống lock-in anxiety (nỗi đau #9).

---

## 5. Thứ tự thực hiện — kế hoạch 90 ngày

```text
Giai đoạn A — Tuần 1–4: "Launch-ready spine"
  ▸ H5: docker compose self-diagnosis + Ollama BYO-LLM mặc định
  ▸ H4: MCP server (read/write memory)
  ▸ H2.1: Telegram capture bot (Zalo để sau)
  ▸ H1.1: digest email định kỳ (tận dụng SendGrid path)
  ▸ Smoke test integration thật (Postgres/Redis/Chroma/Celery) + alembic upgrade — nợ tồn từ P0–P4

Giai đoạn B — Tuần 5–8: "Proof + welcome the refugees"
  ▸ H3: public eval benchmark page + citations/grounding confidence lên UI chat
  ▸ H2.2: email ingest (forward address) + harden web clipper
  ▸ Obsidian/markdown import + export đầy đủ (anti-lock-in, nói to trong marketing)
  ▸ H1.2: nâng chất lượng briefing (LLM themes, lựa chọn tần suất)

Giai đoạn C — Tuần 9–12: "Launch + learn"
  ▸ Landing page định vị: proactive digest là hero, self-hosted + MIT + citations
  ▸ Launch tuần tự: Show HN (chuẩn bị tinh thần bị ném đá lần 1 — Khoj lần 2 đạt 565 điểm), r/selfhosted build-in-public, awesome-selfhosted + selfh.st listing, Product Hunt
  ▸ Pricing page: Free self-host (MIT) / Cloud ~$8–10/mo / pledge "core miễn phí mãi mãi"
  ▸ Thu tín hiệu: 20 user interview (bù giới hạn desk research), đo D7/D30 retention
```

Sau giai đoạn C mới xem xét: graph visualization UI (H-có-thể: demo-gold nhưng retention-risky — prototype trước khi đầu tư), workspace trả phí (tier 2), Zalo/VN localization, mobile app native.

---

## 6. Định vị & giá

**Định vị đề xuất:**
> *Orivory — the self-hosted AI second brain that talks to you first.*
> Không phải "chat với tài liệu của bạn" (bão hòa) — mà là **não chủ động nhắc bạn** mỗi sáng, chạy trên hạ tầng của bạn, trả lời có trích dẫn kiểm chứng, MIT license.

**Giá (theo Obsidian/Recall pattern, không theo Notion):**
| Tier | Giá | Ghi chú |
|---|---|---|
| Self-host | Miễn phí (MIT) | Đừng thu phí feature cốt lõi; Bitwarden/Plex chứng minh self-hoster vẫn chi trả cho premium/hosting |
| Cloud | ~$8–10/mo | Convenience + compute digest/agents; đúng điểm giá cá nhân đã được chứng minh (Recall Plus $10, Mem $14.99) |
| Teams | ~$20/seat (sau) | Chỉ khi cá nhân đã có gravity; SSO/RBAC/audit vào `proprietary/` hoặc cloud-only (Onyx/Dokploy pattern) + pledge công khai |

**Cái không dùng để kiếm tiền:** donations (chỉ 40% self-hoster donate cho *bất kỳ* dự án nào trong năm; Plausible thời đầu có đúng 6 lần donate $5).

---

## 7. Những gì KHÔNG nên làm (chống chỉ định có bằng chứng)

1. **Đừng lead bằng chat-with-docs** — bão hòa (Open WebUI 150K★, AnythingLLM 65K★, LibreChat).
2. **Đừng lead bằng teams/workspace** — free multi-user self-host đã là table stakes; Khoj sụp đổ vì cá cược cloud-first team trước khi có sản phẩm cá nhân vững.
3. **Đừng đi vào meeting-notes AI** — sub-market đông nhất (30+ players: Otter, Fireflies, Granola, Fathom).
4. **Đừng trông chờ donations** — không phải chiến lược, chỉ là cử chỉ.
5. **Đừng làm VN-first** — ngôn ngữ không phải moat (Việt Nam đã có 5 national LLMs, ChatGPT Go ~$5/mo); VN/Zalo là *distribution wedge* sau khi có English PMF. Multilingual embeddings (bge-m3-class) nên có sớm vì cross-lingual retrieval failure được ghi nhận ở NotebookLM/Copilot — lợi thế rẻ.
6. **Đừng đầu tư nặng graph UI trước khi có bằng chứng retention** — graph view "được ngắm nhiều hơn được dùng" (bài học Obsidian graph); giữ nó ở mức demo surface cho đến khi digest/capture tạo thói quen.
7. **Đừng đóng chat-with-your-brain vào walled garden** — no-export là churn story của NotebookLM/Mem; export Markdown luôn.

---

## 8. Rủi ro chính & cách đối phó

| Rủi ro | Khả năng | Đối phó |
|---|---|---|
| Onyx hướng xuống personal tier | Trung bình | Chạy nhanh ở capture + digest (chúng không làm); benchmark công khai để không thua mặt retrieval |
| Mem0/Zep/Cognee ship app layer cho end-user | Thấp–TB | Chúng là infra; nếu có app sẽ là cloud → self-hosted privacy vẫn là sở nhà; cân nhắc tích hợp thay vì đối đầu |
| Fork do MIT | Có | Moat = tốc độ + hosted quality + MCP surface + community; Dokploy-style pledge giữ thiện chí |
| Churn cấu trúc của category (graveyard dynamic) | Cao (có sẵn) | Thiết kế cho resurfacing thay vì filing: salience/decay + digest là trung tâm sản phẩm, không phải phụ |
| Solo-founder bandwidth | Cao | Chấp nhận cắt: Zalo/mobile-app/graph-UI đều được đẩy sau launch; giữ 5 hướng H1–H5 là trần |

---

## 9. Metric thành công (north star + guardrails)

- **North star:** số user có ≥5 ngày capture *và* ≥1 lần recall/tuần (capture-recall loop đang chạy).
- Time-to-first-value < 5 phút từ `docker compose up` (H5).
- Capture latency < 2s qua bot/PWA (H2); tỷ lệ capture qua kênh không phải web UI > 50% sau tháng 1.
- Digest open rate > 40% sau tháng 1 (H1) — chỉ số retention sớm nhất của proactive angle.
- Retrieval benchmark public: hit-rate/citation-rate ≥ baseline competitor tốt nhất có thể đo (H3).
- D30 retention ≥ 25% trên cohort launch (ngưỡng sống của PKM tools theo Supernotes observation).

---

## 10. Giới hạn của khuyến nghị này

Desk research trên community/public sources — **chưa có primary interview**. HN/Reddit over-represents technical users (tiện thay, trùng target của Orivory nhưng không đại diện cho student/knowledge-worker phổ thông). Việc đầu tiên của Giai đoạn C là 20 user interview để thay thế giả định bằng dữ liệu. Market dollar figures từ aggregator firms được coi là low-confidence; các khuyến nghị ở trên chỉ dựa trên tín hiệu cộng đồng, funding events và survey microdata.
