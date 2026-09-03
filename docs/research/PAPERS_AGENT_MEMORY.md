# Papers: Agent Memory — What the Academic Frontier Says (2023–2026)

**Date:** 2026-09-02
**Scope:** Literature review for Orivory's strategic direction as an open "memory hub" for AI agents — memory store with salience/decay + time-aware recall, knowledge graph from entity extraction, corrective RAG, proactive digest.

**Method note (papers-first):** Every claim below carries a source URL (arXiv / ACL Anthology / OpenReview–PMLR–AAAI / official project pages / vendor blog posts where the primary artifact is a blog or GitHub issue, and labeled as such). Findings were gathered via 24 distinct web searches/fetches against primary sources; quotes and numbers are transcribed from the linked sources, not paraphrased from memory. Vendor-reported numbers are marked **[vendor]** and should be treated as marketing-grade until independently reproduced — the LoCoMo controversy (§3.1) shows exactly why.

---

## 1. Surveys & Cognitive Architectures

### 1.1 CoALA — Cognitive Architectures for Language Agents
- **Title/venue:** Sumers, Yao, Narasimhan, Griffiths. *Transactions on Machine Learning Research (TMLR), 2024*. https://arxiv.org/abs/2309.02427
- **Mechanism:** Positions the LLM as the core of a cognitive architecture with modular memory: **working memory** (perception + active state carried across LLM calls), plus long-term **episodic** (past decision cycles), **semantic** (world/self knowledge), and **procedural** (skills/recipes) memory. Action space is split into internal (reasoning, retrieval, learning) and external (grounding) actions, wrapped in a plan-execute decision loop.
- **Open problems:** Short-term: rigorous agent design methodology (specify memory/actions/decision procedure per application) and learning how to *use* memory (the paper notes retrieval and learning actions are underexplored relative to reasoning). Long-term: grounding in cognitive science (Section 7 of the paper) — e.g., what consolidation should look like for agents.
- **Why it matters for Orivory:** CoALA's episodic/semantic/procedural split is the de-facto vocabulary the field now uses (MemOS, MIRIX, and the 2026 surveys all build on it). A memory hub whose data model maps onto CoALA types is instantly legible to researchers and adopters.

### 1.2 A Survey on the Memory Mechanism of LLM-based Agents
- **Title/venue:** Zhang, Bo, Ma, Li, Chen, Dai, Zhu, Dong, Wen. arXiv 2024; **accepted at ACM TOIS, July 2025**. https://arxiv.org/abs/2404.13501 · https://dl.acm.org/doi/10.1145/3748302 · repo: https://github.com/nuster1128/LLM_Agent_Memory_Survey
- **Taxonomy:** Three axes — **memory sources** (inside-trial / cross-trial / external knowledge), **memory forms** (textual vs. parametric; the survey's own trade-off: "textual memory is more efficient in writing, while parametric memory is more efficient in reading"), and **memory operations** (writing, management — reflecting/merging/forgetting — and reading). Evaluation is split into direct (of the memory module) and indirect (end-to-end tasks).
- **Open problems (Section 8):** more advances in parametric memory, memory in multi-agent applications, memory-based lifelong learning, memory in humanoid agents.
- **Why it matters:** This is the first comprehensive memory survey and the "write / manage / read" triad is the standard systems framing. Orivory's salience/decay + consolidation loop sits squarely in the "management" column the survey flags as under-designed.

### 1.3 MemOS — A Memory OS for AI System
- **Title/venue:** Li et al. (MemTensor). arXiv July 2025 (long: https://arxiv.org/abs/2507.03724; short MAG version: https://arxiv.org/abs/2505.22101). Code: https://github.com/MemTensor/MemOS
- **Mechanism:** Treats memory as a **first-class schedulable system resource**. The **MemCube** unifies three memory types — plaintext, activation (KV-cache), parameter (LoRA-style) — each carrying metadata: provenance, versioning, access policies, TTL/expiry, usage counts. Components: MemScheduler (type-aware dispatch: stable hot content → activation memory; abstract reusable patterns → parameters; time-sensitive facts → plaintext), MemLifecycle (Generated → Activated → Merged → Archived → Expired state machine), MemGovernance (**access permissions + audit trails**, explicitly modeled on OS resource management).
- **Results:** Design paper; the repo **[vendor]** claims 35.24% token savings and graph-structured memory "inspectable and editable by design, not a black-box embedding store."
- **Open problems:** Bridging retrieval with parameter-based learning; unified lifecycle governance across memory types; the paper itself frames "systematic memory governance" as the next stage after the tool-based phase.
- **Why it matters:** MemOS independently arrived at Orivory's thesis — salience/decay (its scheduler uses "contextual similarity, access frequency, temporal decay, and priority tags") *plus* metadata-bearing memory units *plus* governance. It validates the design; differentiation must come from being open, self-hosted, and actually shipped.

### 1.4 The 2025–2026 survey wave
- **Memory in the Age of AI Agents** (arXiv, Dec 2025). https://arxiv.org/abs/2512.13564 — Forms (token-level / parametric / latent) × functions (factual / experiential / working) × dynamics (formation, evolution, retrieval). Argues traditional long/short-term taxonomies are insufficient. Frontiers it names: automation-oriented memory design, RL × memory, multimodal memory, **shared memory for multi-agent systems, and trustworthiness** — the last two are directly Orivory-relevant.
- **Rethinking Memory in AI** (arXiv, May 2025). https://arxiv.org/abs/2505.00675 — Six atomic operations: **consolidation, updating, indexing, forgetting, retrieval, compression**. Open challenges: unified memory representation, parametric retrieval, lifelong learning (stability–plasticity).
- **Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers** (arXiv, Mar 2026, covers 2022–early 2026). https://arxiv.org/abs/2603.07670 — Write–manage–read loop in a POMDP-style agent cycle; five mechanism families; blunt aggregate findings (verbatim): "Long context is not memory… Nobody evaluates forgetting well… The parametric–non-parametric gap is real… Evaluation must include cost." Also: "models that score near-perfectly on LoCoMo plummet to 40–60% in MemoryArena." Closing thesis: memory "deserves the same level of engineering investment as the LLM itself."
- **A Survey of Agent Memory in the Second Half: Towards Self-Evolving and Long-Horizon Agents** (arXiv, Aug 2026). https://www.alphaxiv.org/abs/2602.06052 — Substrate (internal/external) × cognitive mechanism × memory subject (user-centric personalization vs agent-centric experience); documents that memory *management itself* is becoming trainable via RL and that memory is "the substrate of agent self-evolution."
- **From Storage to Experience: A Survey on the Evolution of LLM Agent Memory** (Findings of ACL 2026). https://aclanthology.org/2026.findings-acl.2069.pdf — Evolutionary stages: **Storage → Reflection → Experience**; open problems: active memory perception, working-memory organization, *benchmarks for experience*, distributed shared memory, multimodal memory.

---

## 2. Memory System Papers

### 2.1 Generative Agents (the founding retrieval-scoring design)
- **Title/venue:** Park et al., *UIST 2023*. https://arxiv.org/abs/2304.03442 · https://dl.acm.org/doi/10.1145/3586183.3606763
- **Mechanism:** Memory stream of observations with creation + last-access timestamps. Retrieval score = **recency** (exponential decay, factor 0.995 per sandbox hour since last retrieval) + **importance** (LLM-asked 1–10 "poignancy" score at write time) + **relevance** (cosine similarity of embeddings), each min-max normalized, equal weights; top-k fit to context. **Reflection**: when summed importance of recent events crosses a threshold (150), the agent generates higher-level insights that re-enter the stream as retrievable memories (trees of reflections).
- **What it validates for Orivory:** The recency × importance × relevance trio is exactly a salience/decay design, and ablations in the paper show observation, planning, and reflection each contribute critically to believability. It is the strongest citation for time-aware retrieval + salience scoring.

### 2.2 MemGPT / Letta
- **Title/venue:** Packer et al., arXiv Oct 2023. https://arxiv.org/abs/2310.08560
- **Mechanism:** OS-style **virtual context management**: main context (system instructions + read/write working context + FIFO queue with recursive summarization) vs external context (recall + archival storage); the LLM self-edits and pages memory via function calls. DMR benchmark: 93.4% accuracy with gpt-4-turbo (as reported by Zep, arXiv 2501.13956).
- **Follow-ons:** Letta's productization exposes **memory blocks** (in-context blocks the agent edits) and **sleep-time agents** that rewrite memory off the interaction path (see 2.8). Letta's blog notes the design motivation: in MemGPT "memory management, conversation, and other tasks are all bundled into a single agent," making it slower and less reliable; offloading to a sleep-time agent lets memory formation be asynchronous and continuously cleaned. https://www.letta.com/blog/sleep-time-compute/
- **What it validates/contradicts:** Validates memory tiering and self-directed editing. Note that MemGPT scores *poorly* on LoCoMo in the Mem0 paper (J 25.52 temporal, weakest among baselines) — paging alone doesn't solve long-horizon recall; retrieval quality does.

### 2.3 Mem0
- **Title/venue:** Chhikara et al., arXiv Apr 2025. https://arxiv.org/abs/2504.19413 · https://github.com/mem0ai/mem0
- **Mechanism:** Pipeline of **extraction → consolidation** (LLM decides ADD/UPDATE/DELETE/NOOP against retrieved similar memories) → **retrieval**; optional graph variant (**Mem0g**) stores entities/relations. Paper numbers (LLM-as-Judge, J): single-hop 67.13, multi-hop 51.15, open-domain 72.93, temporal 55.51; claims 26% relative improvement over OpenAI's memory and ~2% overall over base Mem0 for Mem0g; **91% lower p95 latency and >90% token savings** vs full-context.
- **April 2026 algorithm update [vendor]:** README claims LoCoMo **92.5** (from 71.4), LongMemEval **94.4**, BEAM 64.1 (1M tokens) / 48.6 (10M) — explicitly flagged as the **managed platform with proprietary optimizations**, "open-source users should expect directionally similar gains but not identical numbers"; new mechanism is single-pass ADD-only extraction + entity linking + multi-signal fused retrieval (semantic/BM25/entity) + time-aware temporal ranking. https://github.com/mem0ai/mem0
- **What it validates/contradicts for Orivory:** Validates that structured salient-fact extraction beats raw-history retrieval on token/latency grounds. Notably *contradicts* a pure-KG story: in their own paper Mem0g **hurt multi-hop** (F1 24.32 vs 28.64 text-only) — the authors attribute it to "inefficiencies or redundancies in structured graph representations for complex integrative tasks." Also note Mem0 has no decay/forgetting-by-time mechanism; its memory management is purely LLM-judged consolidation.

### 2.4 A-MEM (Agentic Memory)
- **Title/venue:** Xu et al., arXiv Feb 2025; **NeurIPS 2025**. https://arxiv.org/abs/2502.12110 · proceedings: https://proceedings.neurips.cc/paper_files/paper/2025/file/19909c36f51abc4856b4560aff3d36d6-Paper-Conference.pdf
- **Mechanism:** Zettelkasten: each memory is an **atomic note** with structured attributes (context description, keywords, tags, embedding). On insert: embedding-similarity prefilter → LLM-judged **link generation** ("boxes" = connected note clusters) → **memory evolution** (neighbors' context/keywords/tags may be updated by the new note). Retrieval pulls linked notes too.
- **What it validates:** Memory networks that *evolve structurally* (new links, updated notes) beat static vector stores across six foundation models. This is the strongest academic support for Orivory's knowledge-graph-from-entity-extraction direction — but note A-MEM's graph is note-level (Zettelkasten), not entity-relation KG, and it has no salience/decay either.

### 2.5 MemoryBank
- **Title/venue:** Zhong et al., **AAAI 2024**. https://arxiv.org/abs/2305.10250 · https://doi.org/10.1609/aaai.v38i17.29946
- **Mechanism:** First paper to implement a forgetting policy for LLM memory: **Ebbinghaus curve R = e^(−t/S)** where t = time since last recall and S = memory strength (integer, +1 and t→0 on each recall — a spaced-repetition reinforcement). Daily distillation of conversations into summaries + personality insight accumulation (SiliconFriend companion).
- **What it validates/limits:** Validates salience/decay + time-aware recall in production-shaped form. The authors are explicit it is "an exploratory and highly simplified memory updating model." Benchmark-era scores are weak (in Mem0's LoCoMo table MemoryBank is the worst baseline, e.g., J 9.68 open-domain) — evidence that a raw Ebbinghaus curve without strong retrieval/extraction is not sufficient by itself.

### 2.6 HippoRAG and HippoRAG 2
- **HippoRAG:** Gutiérrez et al., **NeurIPS 2024**. https://arxiv.org/abs/2405.14831 — Hippocampal indexing theory: LLM-as-neocortex performs OpenIE into a schemaless **KG = artificial hippocampal index**; retrieval-encoder synonymy edges; at query time, query entities seed **Personalized PageRank** → multi-hop association in a *single* retrieval step. Results: up to **+20%** over SOTA RAG on multi-hop QA (MuSiQue/2Wiki); 10–30× cheaper and 6–13× faster than iterative retrieval (IRCoT); complementary gains when combined with IRCoT.
- **HippoRAG 2 ("From RAG to Memory"):** Gutiérrez et al., **ICML 2025**. https://arxiv.org/abs/2502.14802 · https://proceedings.mlr.press/v267/gutierrez25a.html — Fixes the key negative result: prior KG-augmented RAG "performance on more basic factual memory tasks drops considerably below standard RAG" (the concept–context trade-off: entity-centric indexing loses context). HippoRAG 2 integrates **passages themselves into the PPR graph**, uses query-to-triple matching and an LLM "recognition memory" filter. Result: **+7% average over standard RAG on associative tasks with no factual/sense-making degradation**; also "significantly fewer resources for offline indexing compared to other graph-based solutions such as GraphRAG, RAPTOR, and LightRAG" (repo: https://github.com/OSU-NLP-Group/HippoRAG).
- **What it validates for Orivory:** KG structure measurably helps *associative/multi-hop* retrieval and is the best-evidenced graph-memory architecture; but the graph must keep passages/context in the loop, or factual recall degrades. This is the single most important design constraint for Orivory's KG layer.

### 2.7 Zep / Graphiti (temporal KG memory)
- **Title/venue:** Rasmussen et al. (Zep), arXiv Jan 2025. https://arxiv.org/abs/2501.13956
- **Mechanism:** **Graphiti** — a temporally-aware knowledge graph where facts (edges) carry **t_valid/t_invalid validity windows** and are ingested incrementally from conversations + business data; retrieval returns relevant edges + entity summaries.
- **Results:** DMR 94.8% (gpt-4-turbo) vs MemGPT 93.4% and full-context 94.4%; **LongMemEval: 71.2% (gpt-4o) vs 60.2% full-context, with ~90% latency reduction** (1.6k-token context vs 115k). Per-question type, biggest gains on single-session-preference (+184%) and temporal-reasoning (+38.4%); notable regression on single-session-assistant (−17.7%). Later vendor page **[vendor]** claims LoCoMo 94.7% @155ms p95 and LongMemEval 90.2%. https://www.getzep.com/ai-agents/how-to-give-ai-agents-long-term-memory/
- **What it validates for Orivory:** This is the closest published system to "salience/decay + time-aware recall + KG": temporal validity windows on facts *directly implement* decay-as-invalidation, and it wins precisely on **temporal reasoning and preference (knowledge-update) questions** — the categories where flat vector stores fail.

### 2.8 Sleep-time Compute (Letta / UC Berkeley)
- **Title/venue:** Lin, Snell, Wang, Packer, Wooders, Stoica, Gonzalez. arXiv Apr 2025. https://arxiv.org/abs/2504.13171 · code: https://github.com/letta-ai/sleep-time-compute · product: https://www.letta.com/blog/sleep-time-compute/
- **Mechanism:** When idle, an agent re-represents context c into a "learned context" c′ (S(c) → c′) that anticipates likely queries; c′ is shared across queries. Results: same accuracy with **~5× less test-time compute** on Stateful GSM-Symbolic/AIME; scaling sleep-time compute adds **up to +13% / +18%** accuracy; amortized **2.5× cheaper per query at 10 queries/context**; efficacy correlates with **query predictability**.
- **Productization:** Letta sleep-time agents hold the memory-editing tools and continuously reorganize the primary agent's memory blocks "in an anytime fashion." MIRIX later shipped an equivalent "auto-dream" consolidation endpoint (merge duplicates, resolve stale/conflicting entries): https://github.com/Mirix-AI/MIRIX
- **What it validates for Orivory:** Strongest academic support for **proactive digest / idle-time consolidation** — i.e., Orivory's digest is not a gimmick but a Pareto-improving compute allocation, provided queries are predictable (true for a personal assistant, where topics recur).

### 2.9 MemInsight
- **Title/venue:** Salama et al. (AWS AI), **EMNLP 2025**. https://arxiv.org/abs/2503.21760 · https://aclanthology.org/2025.emnlp-main.1683/
- **Mechanism:** Autonomous **attribute mining + annotation** of memory (entity-centric / conversation-centric; turn/session granularity; priority augmentation), then attribute-filtered or embedding retrieval over augmented memories. Results: **+34% recall over DPR on LoCoMo retrieval**; +14% recommendation persuasiveness on LLM-REDIAL.
- **What it validates:** Enriching memory entries with structured metadata at write time (entity attributes) is a cheap, additive win — supports Orivory's entity-extraction pipeline, orthogonal to graph structure.

### 2.10 SeCom
- **Title/venue:** Pan et al. (Microsoft), arXiv Feb 2025. https://arxiv.org/abs/2502.05589
- **Mechanism:** Memory granularity finding: **segment-level units beat turn-level, session-level, and summarization** for retrieval accuracy + semantic quality; plus **compression-based denoising** (LLMLingua-2) of memory units. Removing denoising costs up to 9.46 GPT4Score points on LoCoMo.
- **What it validates for Orivory:** What you store (topical segments) and how clean it is matters as much as how you index it; supports dedup/cleanup as a first-class operation.

### 2.11 MIRIX (multi-agent, typed memory) and M+ (latent memory)
- **MIRIX:** Wang & Chen, arXiv Jul 2025. https://arxiv.org/abs/2507.07957 · https://github.com/Mirix-AI/MIRIX — Six memory types (Core, Episodic, Semantic, Procedural, Resource, **Knowledge Vault** for verbatim sensitive facts) each with a dedicated manager agent + Meta Memory Manager; Active Retrieval. Results: ScreenshotVQA (up to ~20k screenshots/user): **+35% over RAG with 99.9% storage reduction**; LoCoMo **85.38%** overall (their eval: Zep 79.09%, full-context upper bound 87.52%) [vendor-run numbers].
- **M+:** Wang et al., arXiv Feb 2025. https://arxiv.org/abs/2502.00592 — Latent-space memory (MemoryLLM successor) with a **co-trained retriever**; extends knowledge retention from <20k to >160k tokens at similar GPU budget. The parametric/latent counterpoint to external stores.
- **What they validate:** MIRIX validates typed memory + consolidation jobs ("dreaming"); M+ shows the parametric frontier is real but sits outside a self-hosted hub's control plane.

### 2.12 Governance-relevant entrants (see also §6)
- **Memory Worth** (arXiv Apr 2026). https://arxiv.org/abs/2604.12007 — A two-counter per-memory estimator of Pr(task success | memory retrieved), with a.s. convergence proof (ρ=0.89 vs true utility in controlled experiments); supports staleness detection, retrieval suppression, deprecation. This is the first *outcome-based* (rather than recency/LLM-judged) salience signal — a direct upgrade path for Orivory's salience scores.
- **What to Keep, What to Forget: A Rate–Distortion View of Memory Compaction** (arXiv Jul 2026). https://arxiv.org/abs/2607.08032 — Unifies KV eviction, prompt pruning, and agent-memory consolidation as one rate-distortion problem. Two cross-cutting findings: (1) "At every layer the signal that decides what to keep is attention magnitude or recency, and it fails in the same way everywhere — by discarding, before the query is known and with no way to undo it, information the query later needs"; (2) irreversible compaction (UPDATE/DELETE, lossy summarization) composes losses across events, while reversible, retrieval-backed memory stays flat. It explicitly reads MemoryBank's Ebbinghaus curve as "a recency-and-reinforcement-weighted decay" prior that is portable to other layers, and recommends **reversibility + query-conditioning + calibrated stop rules**. Also notes no benchmark measures repeated-compaction degradation (it proposes one).

---

## 3. Benchmarks (critical section)

### 3.1 LoCoMo — and the controversy
- **Paper:** Maharana et al., **ACL 2024**. https://arxiv.org/abs/2402.17753 · https://aclanthology.org/2024.acl-long.747.pdf · data: https://github.com/snap-research/locomo
- **What it measures:** Very long-term *conversations* (LLM-generated, human-edited, grounded in personas + temporal event graphs). Released set: **10 conversations**, ~300–600 turns, **~16k–26k tokens**, up to 32–35 sessions. Tasks: QA over five reasoning types (single-hop, multi-hop, temporal, open-domain, adversarial), event-graph summarization, multimodal dialog generation. Headline: best long-context LLM ≈ 33–38 F1 vs **human 87.9**; models fail hardest on temporal reasoning and hallucinate on adversarial questions.
- **The controversy (both sides):**
  - **Zep's critique** (blog, May 2025): "Is Mem0 Really SOTA in Agent Memory?" https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/ — Claims (a) LoCoMo is too short (16–26k tokens fits modern context windows; "Mem0's own results show their system being outperformed by a simple full-context baseline… ~73% J vs Mem0's best ~68%"); (b) it doesn't test knowledge updates; (c) data-quality problems: category 5 (adversarial) unusable due to missing ground truth, BLIP image-caption errors, speaker-attribution errors, underspecified questions; (d) Mem0's Zep evaluation had implementation errors (wrong user model, timestamps appended to message text instead of `created_at`, sequential searches inflating latency). Corrected result: **Zep 75.14% ± 0.17 J** (corrected down from their initial 84% claim) vs 65.99% reported for Zep in the Mem0 paper.
  - **Mem0's rebuttal** (GitHub issue, May 2025): https://github.com/getzep/zep-papers/issues/5 — Claims Zep's re-evaluation wrongly *included* the excluded adversarial category-5 answers, used a modified system prompt ("prompt tampering") and a single run; re-running under the paper protocol yields **Zep 58.44% ± 0.20** vs 65.99% for Zep's prior algorithm. Also notes `created_at` support was added to Zep's SDK after the paper's runs (Zep disputes this; the issue thread contains the full exchange).
  - **Aftermath:** third-party trackers carry both numbers side by side (e.g., https://github.com/memodb-io/memobase/issues/101, "Updated Zep LoCoMo scores: Zep scores 75.13%"). Later vendor claims diverge further: Zep 94.7% [vendor], MIRIX 85.38% [vendor], Mem0 92.5% [vendor] — same benchmark, ±10–20 point spread, all evaluation-protocol-dependent.
- **Verdict:** LoCoMo is a useful *stress test for temporal/multi-hop conversational recall* but is **not decision-grade for vendor comparison**: tiny n (10 conversations), broken category 5, LLM-judge variance, full-context beats specialized systems, and protocol sensitivity so high that the two principals can't agree on the same system's score to within ~17 points.

### 3.2 LongMemEval
- **Paper:** Wu et al., **ICLR 2025**. https://arxiv.org/abs/2410.10813 · https://github.com/xiaowu0162/LongMemEval
- **What it measures:** 500 manually curated questions over scalable chat histories; five abilities — information extraction, multi-session reasoning, **temporal reasoning, knowledge updates, and abstention** (30 "false premise" questions); seven question types. LongMemEval_S ≈ 115k tokens/history (~40 sessions); LongMemEval_M ≈ 500 sessions (~1.5M tokens). Finding: commercial assistants + long-context LLMs show a **30% accuracy drop** vs short-history settings.
- **Design guidance the paper contributes:** session decomposition → value granularity; fact-augmented key expansion for indexing; **time-aware query expansion** (+11.3% recall with rounds as values; +6.8% with sessions).
- **Known flaws/notes:** _M is enormous and costly to run, so most systems report _S; oracle-retrieval variant available; Zep's published run showed a regression on single-session-assistant questions — worth replicating. SOTA ranges [vendor/mixed]: full-context gpt-4o 60.2%, Zep 71.2% (Jan 2025 run), Zep later 90.2% [vendor], Mem0 94.4% [vendor, April 2026 platform]. Treat cross-vendor numbers as non-comparable until a neutral harness runs them.

### 3.3 MemBench
- **Paper:** Tan et al., **Findings of ACL 2025**. https://aclanthology.org/2025.findings-acl.989/ · https://arxiv.org/abs/2506.21605
- **What it measures:** Factual + **reflective** memory (summarization-level), in **participation** (agent converses) and **observation** (agent watches a message stream) scenarios; metrics: accuracy, recall, **capacity** (degradation as store grows) and **temporal efficiency** — the only mainstream benchmark that scores cost/capacity, not just accuracy. Noise-injection allows tuning difficulty to 100k+ tokens.

### 3.4 MemoryAgentBench
- **Paper:** Hu, Wang, McAuley, arXiv Jul 2025. https://arxiv.org/abs/2507.05257
- **What it measures:** Four competencies from memory science: **accurate retrieval, test-time learning, long-range understanding, and selective forgetting**; existing long-context datasets rebuilt as incremental multi-turn interactions + two new sets (EventQA, FactConsolidation). Finding: **no evaluated system masters all four; most fail conspicuously on selective forgetting** — the only benchmark that tests forgetting at all.

### 3.5 PersonaMem
- **Paper:** Jiang et al., **COLM 2025**. https://arxiv.org/abs/2504.14225 · https://github.com/bowen-upenn/PersonaMem · v2 (implicit personas, Dec 2025): https://arxiv.org/abs/2512.06688
- **What it measures:** Evolving user profiles: 180+ simulated interaction histories, up to 60 sessions, 15 personalization tasks, 7 in-situ query types (recall facts, acknowledge latest preference, track evolution, revisit reasons, preference-aligned recommendations, etc.). Contexts 32k → **1M tokens**.
- **Results:** Frontier models ≈ **50% overall** (multiple choice); recall/track 60–70% but **applying latest preferences 30–50%**; reasoning models no better. Directly relevant negative result for Orivory: in their tests **plain RAG outperformed Mem0 on most question types while being cheaper**.

### 3.6 PrefEval
- **Paper:** Zhao et al., **ICLR 2025 Oral**. https://arxiv.org/abs/2502.09597 · https://prefeval.github.io/
- **What it measures:** 3,000 curated preference–query pairs, 20 topics, explicit + implicit preferences, multi-session up to 100k tokens; tests proactive *preference adherence*, not just recall. Result: zero-shot preference-following accuracy **< 10% at just 10 turns (~3k tokens)**; reminders/RAG help; SFT on the benchmark significantly improves and generalizes in length.

### 3.7 Emerging 2026 benchmarks (for roadmap awareness)
- **MemoryArena** (He et al., 2026; described and analyzed in https://arxiv.org/abs/2603.07670): memory evaluation inside full agentic tasks (web navigation, preference-constrained planning, progressive search); models near-perfect on LoCoMo drop to **40–60%** — passive recall ≠ decision-relevant memory.
- **Evo-Memory** (arXiv Nov 2025): streaming **test-time learning** benchmark; unifies 10+ memory modules (incl. Mem0, MemOS, A-MEM, AWM) under a search–predict–evolve protocol; proposes ExpRAG + ReMem. https://arxiv.org/abs/2511.20857
- **BEAM** (used by Mem0 for 1M/10M-token production-scale eval [vendor], https://github.com/mem0ai/mem0) — mentioned for completeness; independent methodology not yet examined here.

### 3.8 Benchmark comparison table

| Benchmark | Venue/Year | What it measures | Scale | Known results (best reported) | Known flaws |
|---|---|---|---|---|---|
| **LoCoMo** | ACL 2024 | Long-conversation memory: QA (5 types incl. adversarial), event summarization, multimodal dialog | 10 convs, ~16k–26k tokens, 32–35 sessions | Human 87.9 F1; systems [vendor/mixed]: Zep 75.14 J (corrected) / 94.7 [vendor]; Mem0 68–92.5 [vendor]; MIRIX 85.38 [vendor] | Too short for "long-term"; full-context beats memory systems; broken adversarial category; BLIP-caption & speaker errors; protocol-sensitive (±17 pts between principals); tiny n |
| **LongMemEval** | ICLR 2025 | Extraction, multi-session reasoning, temporal reasoning, **knowledge updates**, abstention | 500 Qs; S ≈ 115k tokens, M ≈ 1.5M | Full-context gpt-4o 60.2%; Zep 71.2% (paper run); Zep 90.2 / Mem0 94.4 [vendor] | _M rarely run (cost); judge-based scoring; some single-session-assistant regressions unexplained |
| **MemBench** | Findings ACL 2025 | Factual + reflective memory; participation vs observation; accuracy/recall/**capacity/temporal efficiency** | ~10k & ~100k-token variants | 7 mechanisms compared on Qwen2.5-7B (no SOTA race) | Synthetic dialogues; smaller adoption so far |
| **MemoryAgentBench** | arXiv Jul 2025 | Accurate retrieval, test-time learning, long-range understanding, **selective forgetting** | Multi-turn reconstructed datasets (~355k–421k) | No system masters all four; selective forgetting weakest | New; limited system coverage (budget-constrained) |
| **PersonaMem** | COLM 2025 | Evolving user profiling & personalized response selection; preference application | 180+ histories, ≤60 sessions, up to 1M tokens | Frontier ≈ 50%; preference application 30–50% | Multiple-choice framing partially; synthetic personas |
| **PrefEval** | ICLR 2025 Oral | Proactive preference following (infer/memorize/adhere), explicit + implicit | 3,000 pairs, ≤100k tokens | Zero-shot <10% @10 turns; reminder/RAG best among prompt methods | Generation scored by LLM evaluator; preference-centric only |
| **MemoryArena** | 2026 (per survey 2603.07670) | Memory *inside agentic tasks* (cross-session decision relevance) | Agentic task suites | LoCoMo-strong models drop to 40–60% | Very new; not yet widely adopted |
| **Evo-Memory** | arXiv Nov 2025 | Test-time learning / self-evolving memory over task streams | 10 datasets, 10+ memory modules | ReMem/ExpRAG best; evolving > static retrieval | Research harness, not a leaderboard |

**Which 1–2 benchmarks should an open-source memory hub publish scores on?**
1. **LongMemEval (S)** — first choice. It is peer-reviewed (ICLR 2025), human-curated, tests exactly the capabilities a time-aware memory hub claims (knowledge updates + temporal reasoning + abstention), is long enough to stress retrieval rather than the context window, and is the benchmark both Zep and the field's surveys endorse as the more credible alternative to LoCoMo. Publishing here buys comparability with Zep's and Mem0's published runs.
2. **MemoryAgentBench** — second. It is the only benchmark that scores **selective forgetting** (Orivory's differentiator) and test-time learning, it's from a neutral academic group (UCSD), and no commercial system has gamed it yet. Reporting both would let Orivory claim: "competitive on recall (LongMemEval), uniquely strong on forgetting/consolidation (MemoryAgentBench)."
   - Use LoCoMo only as a *secondary, protocol-explicit* number (fixed judge prompt, ≥10 runs with variance, adversarial category excluded-and-stated), because the community will ask for it — but never lead with it.

---

## 4. Forgetting / Consolidation / Salience

**What the literature endorses for "what to keep, what to fade":**
- **Foundational triad (Generative Agents):** recency decay + write-time importance + query relevance; reflection triggered by accumulated salience (threshold 150). https://arxiv.org/abs/2304.03442
- **Ebbinghaus decay (MemoryBank):** R = e^(−t/S) with recall-driven strength increments — principled, human-plausible, but the authors flag it as "exploratory and highly simplified," and benchmark-era results show raw decay without strong retrieval is insufficient. https://arxiv.org/doi/10.1609/aaai.v3817.29946 (AAAI 2024)
- **Idle-time consolidation (Sleep-time Compute):** moving reasoning to idle periods is a Pareto improvement (~5× test-compute reduction; accuracy +13–18% when scaled; amortized 2.5× per query with multiple queries/context) — directly validates proactive digests. https://arxiv.org/abs/2504.13171
- **Typed consolidation (MemOS lifecycle, MIRIX auto-dream):** memory as state machine (Generated → Activated → Merged → Archived → Expired) with merge/dedup/conflict-resolution jobs run offline. https://arxiv.org/abs/2507.03724 · https://github.com/Mirix-AI/MIRIX
- **Critique of naive decay (Rate–Distortion view, 2026):** the unifying failure mode of every compaction signal in use (attention magnitude, recency, LLM-judged salience) is discarding — *irreversibly, before the query is known* — information the query later needs; repeated lossy compaction compounds errors, and **no benchmark measures this degradation**. Recommended design: prefer **reversible, retrieval-backed** retention (archive instead of delete), make compaction **query-conditioned** where possible, and add calibrated **stop rules** (bounded estimated output error). https://arxiv.org/abs/2607.08032
- **Beyond recency — outcome-based salience (Memory Worth):** track per-memory success/failure co-occurrence (two counters) and deprecate memories that reliably co-occur with failure; converges to conditional success probability; ρ=0.89 vs true utility. https://arxiv.org/abs/2604.12007
- **Value-based vs time-based forgetting (FSFM):** empirical comparison shows value/importance-driven forgetting beats random and old-first deletion on retention accuracy, efficiency, and speed. https://arxiv.org/abs/2604.20300
- **Field consensus (2026 survey):** "current systems handle it crudely: hard time-based expiration, storage-limit eviction, or nothing at all. The research problem is to learn selective forgetting policies that maximize long-term utility under safety and compliance constraints." https://arxiv.org/abs/2603.07670
- **Privacy-driven forgetting:** SP-Mem (§6) shows forgetting also has a governance dimension (sanitize at rest, hydrate on consent).

**Synthesis — the design the literature actually endorses:** keep raw/episodic records (reversible), fade *prominence* rather than existence (decay affects retrieval ranking, not deletion), reinforce on access (spaced-repetition strength), consolidate summaries upward during idle time (sleep-time compute), and gate destructive deletion on value signals or explicit policy (Memory Worth / FSFM / GDPR erasure). Orivory's salience/decay should therefore decay *rank*, archive *content*, and only hard-delete on consent/compliance — this is simultaneously the accuracy-optimal and compliance-optimal design per the sources above.

---

## 5. Knowledge-Graph Memory: does graph structure measurably help?

**Positive evidence:**
- **HippoRAG (NeurIPS 2024):** OpenIE KG + Personalized PageRank gives up to **+20%** over SOTA RAG on multi-hop QA and single-step retrieval at 10–30× lower cost than iterative retrieval. https://arxiv.org/abs/2405.14831
- **Zep/Graphiti (2025):** temporal KG on LongMemEval = **+18.5% accuracy over full-context baseline with ~90% latency reduction**, largest gains on preference and temporal-reasoning questions. https://arxiv.org/abs/2501.13956
- **GraphRAG (Microsoft, 2024):** LLM-built entity KG + community summaries → substantial comprehensiveness/diversity gains on **global sensemaking** questions over 1M-token corpora (not a memory benchmark, but the canonical "graph for global questions" evidence). https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/
- **LightRAG (Findings of EMNLP 2025):** dual-level (entity/concept + theme) graph retrieval with incremental updates; improves retrieval accuracy/efficiency vs flat RAG. https://aclanthology.org/2025.findings-emnlp.568/
- **A-MEM (NeurIPS 2025):** note-level linking ("boxes") improves long-term conversational performance across six models. https://arxiv.org/abs/2502.12110
- **G-Memory (2025):** hierarchical graph memory for multi-agent systems: up to **+20.89%** embodied success, +10.12% QA, plug-and-play. https://arxiv.org/abs/2506.07398

**Negative results / conditions (the honest part):**
- **HippoRAG 2's central finding:** KG-augmented RAG of the HippoRAG-1/vintage type **drops considerably below standard RAG on basic factual tasks** (concept–context trade-off); fixed only by putting passages into the graph and query-to-triple matching. https://arxiv.org/abs/2502.14802
- **Mem0's own ablation:** graph memory (Mem0g) **reduced multi-hop performance** vs text-only memory (F1 24.32 vs 28.64) — relational structure "provides limited utility" for single-turn targets and underperformed on integration tasks. https://arxiv.org/abs/2504.19413
- **G-Memory's negative finding:** single-agent memory baselines (Voyager, MemoryBank) can **degrade** multi-agent performance (−4.17% on PDDL for AutoGen). https://arxiv.org/abs/2506.07398
- **HippoRAG 2 repo:** its graph indexing uses "significantly fewer resources… compared to other graph-based solutions such as GraphRAG, RAPTOR, and LightRAG" — graph quality/cheapness varies enormously across implementations. https://github.com/OSU-NLP-Group/HippoRAG

**Conclusion:** Graph structure measurably helps **when the query requires association across items** (multi-hop, temporal ordering, cross-session synthesis, sensemaking) and when the graph preserves **context alongside concepts** (passages-as-nodes / validity-windowed edges). It is neutral-to-harmful for single-hop factual recall if built entity-first without context, and it always costs more to build/maintain. Design rule for Orivory: **hybrid retrieval** — vector + keyword + graph signals fused (as Mem0's April 2026 algorithm and LongMemEval's key-expansion results both indicate), with the graph reserved for relational/temporal structure, not as the sole index.

---

## 6. WHITE SPACE check (permissions / audit / portability)

Searched queries used (verbatim):
1. `user-facing permissions governance consent control over AI agent memory personal data access control paper`
2. `audit log transparency what AI agents read from personal memory access logging privacy paper arxiv`
3. `portable interchangeable memory format for AI agents interoperability memory transfer across agents paper`
4. `Towards Automating Data Access Permissions in AI Agents` / `GAAP agent privacy execution environment` (follow-ups)
5. Plus coverage found via: `SP-Mem`, `Agent-Memory Protocol`, `AudAgent`, `PrivacyPeek`, `DP-MemView`, `Portable Agent Memory`, `AIMEM IETF draft`, `Portable AI Memory spec`

**Finding: the space is NOT empty anymore — 2025–2026 saw the first entrants, but none of them is (a) peer-reviewed as a *system benchmark*, or (b) an integrated self-hosted implementation. The gap has narrowed from "nothing exists" to "no standard, no benchmark, no integrated OSS system." Details:**

**(a) User-facing permissions / governance for agent memory — early work exists:**
- *From Rights to Runtime: Privacy Engineering for Agentic AI* (Navaie; AAAI-style venue, 2025): opinion/design-patterns paper — optional, bounded, user-visible memory; TTL labels; cascade erasure with receipts; purpose-aware egress gates. https://doi.org/10.1002/aaai.70036
- *Towards Automating Data Access Permissions in AI Agents* (arXiv Nov 2025): user study + ML permission-prediction assistant (85.1% overall accuracy, 94.4% high-confidence) because install-time/runtime permission models don't fit agents. https://arxiv.org/html/2511.17959v1
- *GAAP* (arXiv Apr 2026): execution environment enforcing user permission specs via information-flow control; blocks all disclosure attacks in their threat model without trusting the agent. https://arxiv.org/html/2604.19657v1
- *SP-Mem: What to Remember, What to Reveal* (arXiv Aug 2026): consent-gated retrieval — sanitize at rest, restore exact private values only when task-required AND user-authorized; PAR precision 1.00, exposure reduced from 16.0% (full-context) to 0.33%. https://arxiv.org/html/2608.16551v1
- *Agent-Memory Protocol (AMP)* (PMLR 2026): redact-at-rest / pack-for-purpose / hydrate-on-return protocol. https://proceedings.mlr.press/v317/wu26a.html
- Note: MemOS also sketches OS-style "MemGovernance" (access permissions + audit trails) as a design component. https://arxiv.org/abs/2507.03724

**(b) Audit / access logs for what agents read — early work exists:**
- *AudAgent* (PoPETs 2026; arXiv Nov 2025): real-time auditing of agent data practices against formalized privacy policies; explicit finding that "post hoc logs are insufficient: users need to identify privacy risks in real time." https://doi.org/10.56553/popets-2026-0077 · https://arxiv.org/html/2511.07441v4
- *PrivacyPeek* (arXiv Jun 2026): benchmark auditing the **acquisition stage** (what the agent pulled into context, not just what it said): 1,182 cases; widespread over-acquisition (CER 51.95% on Claude-Sonnet-4; "one careless action… away from an outright leak"). https://arxiv.org/html/2606.00152v1
- *DP-MemView* (arXiv Aug 2026): differentially private memory-view interface with per-attribute DP ledgers capping cumulative exposure of memory-conditioned transcripts. https://arxiv.org/html/2608.03130

**(c) Portable / interchangeable memory formats — protocol-level work exists, none standardized or peer-reviewed as a benchmark:**
- *Portable Agent Memory (PAM-protocol)* (arXiv May 2026): five-component memory model, Merkle-DAG provenance (BLAKE3 + Ed25519), capability-scoped access tokens, injection-resistant re-hydration; pilot TCS 0.83–0.92 vs 0.28–0.45 no-memory baseline; single-author preprint + SDK. https://arxiv.org/abs/2605.11032 · https://github.com/santhoshravindran7/portable-agent-memory
- *IETF Internet-Draft: Memory Interchange Bundle Format (AIMEM)* (draft-vu-aimem-bundle-00): vendor-neutral JSON bundle with export/import HTTP profile, GDPR Art. 17/20 alignment — an individual draft, not a working-group item. https://www.ietf.org/archive/id/draft-vu-aimem-bundle-00.html
- *Portable AI Memory (PAM) spec* (GitHub, community spec): vCard-for-memory positioning, provenance, decay models in the format, access control; explicitly notes "AI providers do not natively support PAM." https://github.com/portable-ai-memory/portable-ai-memory/blob/master/spec.md

**Explicit white-space statement for Orivory:**
- No paper found that treats **memory governance/audit as a benchmarkable property of memory systems** — the 2026 surveys name trustworthiness/governance as an open frontier (https://arxiv.org/abs/2512.13564; https://arxiv.org/abs/2603.07670) but no benchmark scores a memory system on permission enforcement, audit-log completeness, or erasure correctness. (PrivacyPeek audits *agents*, not *memory stores*.)
- No paper found that provides an **integrated, self-hosted memory hub** combining quality (salience/decay + KG + time-aware recall) with governance (consent, audit, erasure) and portability (interchange format) — the pieces exist only as separate prototypes/specs.
- The portability layer specifically is **protocol drafts and single-author preprints with no adoption and no neutral evaluation** — an open-source project publishing a real interchange format + conformance tests + migration tooling would be first mover.
- Caveat: the adjacent privacy-agent literature (GAAP, SP-Mem, AudAgent, DP-MemView, AMP) is moving *fast* — the window for "first" is months, not years. Differentiate on integration + benchmarks + OSS distribution rather than on a single mechanism.

---

## 7. Trajectory: what 2025–2026 papers converge on

1. **Memory management becomes learned, not hand-designed.** RL over memory operations (store/retrieve/update/summarize/discard as tools — AgeMem, per https://arxiv.org/abs/2603.07670), trained curation policies, and outcome-based signals (Memory Worth) are displacing fixed heuristics. Survey framing: "memory management itself is becoming a trainable, self-evolving capability." (https://www.alphaxiv.org/abs/2602.06052)
2. **Test-time learning / self-evolving agents.** A dedicated benchmark line (Evo-Memory, StreamBench, LABench, MemoryBench — tabled in the ACL 2026 survey) evaluates agents that improve from their own experience streams; memory is the substrate that makes self-evolution possible. (https://arxiv.org/abs/2511.20857; https://aclanthology.org/2026.findings-acl.2069.pdf)
3. **Parametric vs non-parametric is a real, unresolved trade-off.** Parametric memory integrates seamlessly but "fails at targeted deletion and auditing"; non-parametric memory is inspectable/governable but "can feel bolted on." Deployed systems favor non-parametric stores for auditability. (https://arxiv.org/abs/2603.07670; https://arxiv.org/abs/2404.13501)
4. **Multi-agent memory becomes a distributed-systems problem.** Shared-vs-distributed memory hierarchies, cache-sharing and memory-access protocols, consistency models (https://arxiv.org/abs/2603.10062); governed shared memory with scoped access, provenance, temporal supersession and measured failure modes (https://arxiv.org/abs/2606.24535); inter-agent semantic protocols (Mesh Memory Protocol, https://arxiv.org/abs/2604.19540); hierarchical MAS memory (G-Memory, https://arxiv.org/abs/2506.07398). Several surveys list shared multi-agent memory as a top frontier (https://arxiv.org/abs/2512.13564).
5. **Trustworthiness/governance moves into the memory stack.** MemOS MemGovernance; SP-Mem consent gating; DP interfaces; audit tooling; the "Memory in the Age of AI Agents" survey lists trustworthiness as a named frontier. (links in §6)
6. **Multimodal memory** (screenshots, wearables) as the next data frontier — MIRIX ScreenshotVQA; multimodal memory named open problem in both 2026 surveys.
7. **Evaluation shifts from passive recall to agentic, cost-aware, forgetting-aware tests.** MemoryArena (LoCoMo-aces drop to 40–60% in agentic settings), MemoryAgentBench (selective forgetting), MemBench (capacity/efficiency metrics), the rate–distortion proposal for repeated-compaction benchmarks, and the 2026 survey's demand to "mandate reporting of at least token consumption and latency overhead alongside accuracy."

**Roadmap alignment for a 2026–2027 memory product:** ship non-parametric (inspectable) memory with hybrid retrieval; make salience outcome-feedback-driven rather than purely recency-driven; productize idle-time consolidation; expose governance (permissions, audit, erasure) as API surface, not settings menus; adopt/seed a memory interchange format; and evaluate on LongMemEval + MemoryAgentBench with cost metrics reported.

---

## Implications for Orivory

1. **The core design is validated, twice over.** Salience/decay + time-aware recall is independently endorsed by Generative Agents (recency 0.995-decay × importance × relevance), MemoryBank (Ebbinghaus), Zep (temporal validity windows — the winning ingredient on temporal/knowledge-update questions), and MemOS's scheduler (similarity + access frequency + temporal decay + priority). Ship it, but cite all four.
2. **Decay rank, don't delete.** The rate–distortion analysis (arXiv 2607.08032) shows irreversible compaction compounds errors and no one can re-derive what was lost; the endorsed pattern is reversible archival retention + faded prominence + query-conditioned compaction. Hard-delete only on user consent/compliance. Orivory's decay should modulate retrieval score and trigger archiving, never silently destroy data.
3. **Upgrade salience with outcome feedback.** Memory Worth (arXiv 2604.12007) gives a two-counter, provably-convergent per-memory success signal. Logging retrieval→outcome pairs and blending outcome-worth into salience would make Orivory's scoring a generation ahead of recency-only decay — and it's cheap.
4. **Keep the KG, but hybrid.** HippoRAG 2 proves graph structure helps multi-hop/associative recall (+7–20%) *only when passages/context stay in the graph*; Mem0g's own negative result and HippoRAG 1's factual degradation show entity-only graphs hurt single-hop recall. Orivory's KG should carry validity windows (Zep-style) and coexist with vector + BM25 in fused retrieval.
5. **Publish on LongMemEval-S (primary) and MemoryAgentBench (secondary).** LongMemEval is peer-reviewed, human-curated, tests knowledge-update/temporal/abstention — exactly Orivory's pitch — and both Zep and Mem0 have published runs for comparability. MemoryAgentBench is the only benchmark that scores selective forgetting, Orivory's differentiator. Use LoCoMo only as a protocol-explicit secondary number (≥10 runs, variance reported, category-5 exclusion stated) — the Mem0/Zep fight (75.14 vs 58.44 for the same system) shows it is not decision-grade.
6. **Proactive digest = sleep-time compute.** Orivory's digest has direct academic cover (arXiv 2504.13171: 5× test-compute reduction, +13–18% accuracy, 2.5× amortization; query predictability is the enabling condition — true for personal assistants). Position the digest as consolidation, with MIRIX-style dedup/conflict resolution.
7. **The governance white space is real but closing.** Permissions (GAAP, permission-automation), audit (AudAgent, PrivacyPeek), consent-gated retrieval (SP-Mem), and portability (PAM, AIMEM draft) all appeared in 2025–2026 — but no benchmark scores memory governance, and no integrated self-hosted system combines quality + governance + portability. Orivory should (a) ship audit/access logs and consent/erasure as first-class API surface, (b) publish the first memory-governance benchmark (permission enforcement, audit completeness, erasure correctness, portability round-trip) — that is a genuinely publishable gap.
8. **Portability is the open-standard land grab.** MCP/A2A cover tools and tasks; memory portability is contested by one preprint, one IETF individual draft, and one community spec with zero adoption. A memory hub that exports/imports a documented interchange format with conformance tests — aligned with GDPR Art. 20 — can own this layer before it standardizes elsewhere.
9. **Roadmap should chase the field's convergent "next things":** learned/RL memory policies (start by logging outcome data now), self-evolving/test-time learning agents (Evo-Memory-style streaming evals), multi-agent shared memory as governed distributed state (scoped access + provenance + supersession — matches Orivory's hub role for fleets of local agents), and cost-aware reporting (tokens + latency) in all published results.
10. **Treat every vendor leaderboard number as marketing until reproduced.** The LoCoMo controversy — Zep 65.99 in Mem0's paper, 75.14 in Zep's correction, 58.44 in Mem0's rebuttal, 94.7 in Zep's later page — is the field's clearest lesson: fixed prompts, ≥10 runs with variance, excluded categories stated, and full-context baselines included, or don't publish numbers at all.
