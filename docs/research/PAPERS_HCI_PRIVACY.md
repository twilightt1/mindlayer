# PAPERS_HCI_PRIVACY.md — Academic Evidence for Capture Friction, Proactive AI, and Memory Privacy

**Date:** 2026-09-02
**Prepared for:** Orivory (self-hosted personal AI memory system / second-brain + memory hub for AI agents)

**Method note.** Literature review conducted 2026-09-02 via 18 distinct web searches/fetches (Exa) against primary sources (arxiv.org, dl.acm.org, aclanthology.org, openreview.net, publisher pages). Every paper card links to a verified source page; findings and numbers below are drawn from the linked abstracts/papers as surfaced in those sources, not from memory. Two honesty caveats: (1) no peer-reviewed academic evaluation of Tiago Forte's PARA/BASB methodology itself was found — the closest is the 2025 Obsidian case study below, which cites Forte's book; the BASB canon remains practitioner literature. (2) Items dated CHI 2026 are conference-program entries / recent preprints and should be treated as preliminary evidence. Older (pre-2022) papers are included where they remain the canonical evidence (PIM abandonment, interruption cost).

---

## Section 1 — PKM: capture friction, abandonment, and AI-assisted auto-organization

**1.1 "I give up! Five factors that contribute to the abandonment of information management strategies" — Jones, Bruce, Klasnja & Jones, ASIS&T 2008**
Link: https://doi.org/10.1002/meet.2008.14504503115
Six-month interview study (22 participants, 33 documented strategy-abandonment cases). Five recurring reasons people give up on organizing systems: **visibility** (out of peripheral vision → forgotten), **integration** (doesn't interconnect with existing systems), **co-adoption** (others don't use it → effort feels wasted), **scalability**, and **return on investment**.
Design implication: a capture tool must earn a permanent slot in the user's existing workflow and show ROI quickly, or it becomes another abandoned system.

**1.2 "Finders/Keepers: A Longitudinal Study of People Managing Information Scraps in a Micro-note Tool" — Van Kleek, Styke, Karger & schraefel, CHI 2011**
Link: https://people.csail.mit.edu/emax/papers/chi2011-finders-keepers.pdf
Two-year, 420-user deployment of the List-it micro-note tool (66k+ notes). Users were drawn to it by **ease and speed of capture** and the ability to record arbitrary scraps that escape the rigid types imposed by structured PIM tools; keeping behavior fell into four distinct strategies. The paper documents why information "eludes" structured PIM tools: the time/effort/attention demanded at capture exceeds what's available, information doesn't fit any one tool, and filed items lose visibility ("once it's filed it's gone").
Design implication: sub-10-second, structure-free capture; organization must happen after or without the user, never as a gate to capture.

**1.3 "Note to self: examining personal information keeping in a lightweight note-taking tool" — Bernstein, Van Kleek, Karger & schraefel, CHI 2009**
Link: https://dl.acm.org/doi/10.1145/1518701.1518924
10-day field study (42 participants). Notes were recorded extremely quickly and tersely, mixed types freely, and were **rarely revised or deleted**; lower time investment led users to capture information they would otherwise have lost. 16/42 participants still used the tool a week after the study ended.
Design implication: every second of capture friction is measurable behavioral loss; free-text + search beats imposed taxonomies for capture-stage retention.

**1.4 "'Stuff goes into the computer and doesn't come out': a cross-tool study of personal information management" — Boardman & Sasse, CHI 2004**
Link: https://dl.acm.org/doi/10.1145/985692.985766
Cross-tool (files, email, bookmarks) + longitudinal PIM study. Users employ rich, inconsistent strategies within and across tools; the "supporting nature" of PIM discourages reflection, so strategies decay silently.
Design implication: fragmentation across tools is the norm — a memory layer that unifies capture across surfaces addresses a documented, structural problem, not a niche one.

**1.5 "How People Manage Knowledge in their 'Second Brains': A case study with industry researchers using Obsidian" — Ferreira, Segura, Souza & Brasil, INTERACT 2025 (arXiv:2509.20187)**
Link: https://arxiv.org/abs/2509.20187
Interview + observation study with 7 Obsidian users. Key finding: users' **planned retrieval strategy drives how they build and maintain** their knowledge base (inbox folders, tags, links are chosen for how they expect to re-find). The authors explicitly propose AI-driven features to support this process.
Design implication: the "second brain" methodology (Forte's PARA/CODE is cited as the reference frame) has entered academic study in 2025, and the academically-endorsed direction is AI assistance aligned to retrieval intent — organize for how the person will look, not for a taxonomy's sake.

**1.6 "Beyond Abandonment to Next Steps: Understanding and Designing for Life after Personal Informatics Tool Use" — Epstein et al., CHI 2016**
Link: https://dl.acm.org/doi/10.1145/2858036.2858045
Survey (193) + interviews (12) on why people stop self-tracking tools: six reasons for quitting and five "life after tracking" perspectives; designs keep influencing behavior even after abandonment.
Design implication: adjacent-domain evidence that abandonment is a designed-for lifecycle stage — plan graceful pauses/resumption, not just activation.

**1.7 "Hoarding and Minimalism: Tendencies in Digital Data Preservation" — Vitale, Janzen & Odom, CHI 2018**
Link: https://dl.acm.org/doi/10.1145/3173574.3174161
Interviews with 23 participants; preservation behavior spans hoarding↔minimalism. Hoarding is partly emotional (fear of forgetting) and partly a rational response to curation cost — verbatim: "it costs so little to add stuff but it takes a lot of time to sort the stuff you want to delete," so unlimited storage tilts people toward never deleting.
Design implication: the organizing tax is real and quoted; automating sort/delete- candidate work removes the mechanism that produces clutter anxiety.

**1.8 "Digital hoarding and personal use digital data" — Sillence et al., Human–Computer Interaction (published online Dec 2023)**
Link: https://www.tandfonline.com/doi/full/10.1080/07370024.2023.2293001
167-participant questionnaire study. Digital-hoarding scores correlate with **difficulty deleting, difficulty finding items, attachment, and distress at potential loss** of items; hoarders store significantly more.
Design implication: auto-organization is also a well-being feature — reducing find-difficulty and deletion-difficulty attacks the measured correlates of digital hoarding.

**1.9 "CoNotate: Suggesting Queries Based on Notes Promotes Knowledge Discovery" — Palani et al., CHI 2021**
Link: https://dl.acm.org/doi/10.1145/3411764.3445618
Within-subjects study (n=38). Mining a user's notes to suggest queries produced significantly more queries, higher self-rated knowledge gain, and more discovered domain terminology than standard search; 23/38 preferred the notes-based suggestions.
Design implication: AI suggestions *derived from the user's own notes* are measurably useful — the personal corpus is the moat.

**1.10 "NoTeeline: Supporting Real-Time, Personalized Notetaking with LLM-Enhanced Micronotes" — Huq et al., arXiv 2024 (v2 Mar 2025)**
Link: https://arxiv.org/abs/2409.16493
LLM expands terse "micronotes" into full notes in the user's own style while they work. Within-subjects study: significantly fewer words and less time than manual note-taking, generated notes rated ~6.0/7, 93.2% factual correctness (HHEM), and all participants preferred it to the baseline. Users valued being able to **toggle between original and generated text** — control over content was the trust mechanism.
Design implication: the "capture fast now, let AI write it up later" pattern is validated; keep the raw human input visible and editable.

**1.11 "NoteBar: An AI-Assisted Note-Taking System for Personal Knowledge Management" — arXiv 2509.03610 (Sep 2025)**
Link: https://arxiv.org/abs/2509.03610
Auto-routes notes into semantic kinds (task/idea/insight…) with efficient encoder models instead of expensive LLM calls; releases a 3,173-note dataset. Its design principles center a **user-in-the-loop accept/reject/edit feedback loop** (flagged as not yet implemented) for exactly the reason that auto-classification "cannot fully capture user intent."
Design implication: auto-tagging should be a suggestion stream with acceptance telemetry, and cheap local models are a viable, privacy-friendlier backbone for it.

**1.12 "Generative AI in Knowledge Work: Design Implications for Data Navigation and Decision-Making" (Yodeai) — Zhang et al., arXiv 2025**
Link: https://arxiv.org/abs/2503.18419
Study of 20 knowledge workers + 16 product managers. Three requirements for AI in knowledge work: **adaptable user control, transparent collaboration mechanisms, integration of background knowledge with external information**; observed failure modes include overreliance and user isolation. Notably, "sources in Q&A outputs… increased trust in LLM output."
Design implication: control + transparency are user requirements, not nice-to-haves; showing sources measurably raises trust.

**1.13 "Augmenting Expert Cognition in the Age of Generative AI: Insights from Document-Centric Knowledge Work" — CHI 2025**
Link: https://arxiv.org/abs/2503.24334
Two empirical studies (survey authoring; business document sensemaking). Experts happily delegate **repetitive information-foraging** (screening, extraction, structuring) to AI but insist on keeping synthesis and interpretation; a GenAI system that preserved **provenance of extracted snippets** made participants 16% faster with no accuracy loss, and trace-to-evidence was the trusted verification mode.
Design implication: automate the organizing tax (foraging/filing), never the judgment layer; always keep a link from every AI artifact back to its source.

**1.14 "A Survey on the Memory Mechanism of Large Language Model based Agents" — Zhang et al., arXiv 2024; and "Rethinking Memory in AI: six atomic operations" — Du et al., arXiv 2025**
Links: https://arxiv.org/abs/2404.13501 ; https://arxiv.org/abs/2505.00675
The 2024 survey formalizes agent memory as write → manage → read, with management including **merging, forgetting, and reflection**; the 2025 survey defines six atomic operations — Consolidation, Updating, Indexing, **Forgetting**, Retrieval, Compression — treating forgetting as a first-class operation. A-MEM (https://arxiv.org/abs/2502.12110) builds agent memory on **Zettelkasten** principles (atomic notes, dynamic linking, memory evolution) and outperforms static-structure baselines.
Design implication: Orivory's memory-hub architecture sits squarely on the academic mainstream; forgetting and linking are canonical operations to expose as product features, not internal details.

### What the literature endorses / warns against (Section 1)
**Endorses:** near-zero-friction capture (speed of capture predicts whether things get captured at all — 1.2, 1.3); organization deferred and automated (1.7, 1.10, 1.13); AI suggestions grounded in the user's own corpus with accept/reject control (1.9–1.12); provenance-preserving automation (1.13); retrieval-strategy-aligned organization (1.5).
**Warns against:** imposing structure at capture time (1.2, 1.3); ignoring integration/visibility/ROI — the measured abandonment factors (1.1, 1.6); assuming people will curate or delete manually (1.7, 1.8); full automation without user control or raw-input visibility (1.10–1.12).

---

## Section 2 — Proactive AI: digests, notifications, timing, and churn

**2.1 "No Task Left Behind? Examining the Nature of Fragmented Work" — Mark, González & Harris, CHI 2005**
Link: https://dl.acm.org/doi/10.1145/1054972.1055017
Observed 24 information workers in detail: work is highly fragmented; **57% of working spheres are interrupted**, and although 77% of interrupted work is resumed the same day, people first do **more than two intervening activities** — a "fairly high cognitive cost to resume work." Self-initiated resumption is faster (21 min) than externally prompted resumption (62 min).
Design implication: every unrequested interruption costs real reorientation; proactive systems should bundle and schedule rather than stream.

**2.2 "The Cost of Interrupted Work: More Speed and Stress" — Mark, Gudith & Klocke, CHI 2008**
Link: https://dl.acm.org/doi/10.1145/1357054.1357072
Experimental study: interrupted tasks were completed *faster* (people compensate by speeding up) with no quality difference — but at significantly **higher stress, frustration, time pressure, and effort**; after only 20 minutes of interrupted work the workload measures rose significantly.
Design implication: "it didn't slow the user down" is the wrong success metric for proactive features; stress/annoyance is the hidden tax that produces churn.

**2.3 "Proactive Conversational AI: A Comprehensive Survey of Advancements and Opportunities" — Deng et al., ACM TOIS 43(3), 2025**
Link: https://dl.acm.org/doi/10.1145/3715097
Definitive survey of proactive dialogue: defines proactivity via **anticipation + initiative**, taxonomizes turn-/sub-dialogue-/dialogue-level proactivity, and names **evaluation protocols and ethics of proactivity** ("a precarious line between benefit and harm") as the key open challenges for LLM-era systems.
Design implication: proactivity is a design discipline with known failure modes; treat intensity, timing, and ethics as first-class design dimensions.

**2.4 "Proactive Agent: Towards Proactive Artificial Intelligence" (ProactiveBench) — Lu et al., arXiv 2410.12361 (2024)**
Link: https://arxiv.org/abs/2410.12361
Data-driven proactivity: collects real human activity streams, has annotators label candidate agent-initiated tasks as accepted/rejected, and trains a reward model (up to 91.8% consistency with human judgments; F1 66.5% for the fine-tuned model) to predict *which* proactive interventions humans would accept.
Design implication: acceptance/rejection of AI-initiated actions is the trainable signal — Orivory should log and learn from digested-item acceptance from day one.

**2.5 "Proactive Conversational Agents with Inner Thoughts" — Liu, Fang, Shi, Wu, Igarashi & Chen, CHI 2025**
Link: https://doi.org/10.1145/3706598.3713760 (arXiv:2501.00383)
Agents continuously form covert "thoughts" and decide **when** to speak by evaluating intrinsic motivation, with **three adjustable layers of proactivity**. In user studies, participants preferred the Inner Thoughts agent 82% of the time and rated it significantly better on turn appropriateness, coherence, and initiative.
Design implication: a tunable proactivity dial + a "should I even speak" internal gate beat both passive-only and always-on designs.

**2.6 "Need Help? Designing Proactive AI Assistants for Programming" — CHI 2025**
Link: https://dl.acm.org/doi/10.1145/3706598.3714002
Controlled study of a proactive coding assistant: proactivity increased completed tasks by **12–18%**, but the highest-frequency variant reduced preference for the proactive assistant over a non-proactive baseline **by half** despite the productivity gain. Actionable suggestions (brainstorming, debugging) were accepted (~69 accepts vs 6 rejects); purely informational ones were ignored or rejected. Key design rules: time suggestions to detected work modes, cap frequency, and let accept/reject adapt future behavior.
Design implication: usefulness is real but fragile — frequency discipline and actionability are what keep proactive features loved.

**2.7 "Assistance or Disruption? Exploring and Evaluating the Design of Proactive AI Agents" (Codellaborator) — arXiv 2502.18658 (2025)**
Link: https://arxiv.org/abs/2502.18658
Within-subjects study (N=18) of a proactive coding agent: of 398 agent-initiated interactions, **53.3% led to effective engagement, 12.1% caused workflow disruptions, 34.7% were ignored**. Interventions at **task boundaries** (e.g., after program execution) were the most effective heuristic; visible AI presence and threaded interaction reduced disruption and improved awareness.
Design implication: publishable benchmark ratios for proactive UX — aim for ≥50% engagement and ~≤10% disruption; interrupt at task boundaries, never mid-flow.

**2.8 "'Having Lunch Now': Understanding How Users Engage with a Proactive Agent for Daily Planning and Self-Reflection" — CHI 2026**
Link: https://dl.acm.org/doi/10.1145/3772318.3790957
14-day deployment (12 participants, 336 agent-initiated check-ins, 3,181 turns). Compliance with suggestions averaged **8.6%**; **32.4% of agent-initiated conversations ended with the user leaving the last message unanswered**; users reported annoyance at fixed-time evening check-ins when busy, at rigidity, and at the agent's overpromising. Users also began *volunteering* status updates — accountability is a valued proactive side-effect.
Design implication: twice-daily AI check-ins without adaptive timing produce measurable disengagement; unanswered-proactive-message rate is the churn canary.

**2.9 "Proactive, But Not Creepy: Legitimacy and Disclosure Boundaries in Generative IR Assistants" — CHI 2026**
Link: https://programs.sigchi.org/chi/2026/program/content/230156
Mixed methods (SEM, N=112; interviews, N=12) on AI-initiated assistance: acceptance runs through **legitimacy judgments** and conditional trust calibration; design implications are explicit — clear explanations **at initiation**, incremental disclosure with user control, and context-adaptive proactivity intensity.
Design implication: "why am I seeing this?" at the moment of initiation is the acceptance lever for memory-driven proactivity.

**2.10 "'Tell Me Why You're Asking': Exploring How to Increase Engagement in Preference Feedback for Intelligent Notification Systems" — CHI 2026**
Link: https://people.cs.nycu.edu.tw/~armuro/pubs/su-et-al-2026-chi.pdf
Findings on soliciting notification preferences: requests are honored when **justifiable** (user understands why the system asks and what their answer changes), when aligned with established notification-handling routines, and immediately after the user has read the notification; users want complex preferences moved into dedicated settings.
Design implication: put preference capture at natural touchpoints and always show the consequence of the answer.

**2.11 "NotiSummary" (UbiComp/ISWC 2023) + "From Overwhelmed to Overview…" (MobileHCI 2025)**
Links: https://programs.sigchi.org/ubicomp-iswc/2023/program/content/121802 ; https://people.cs.nycu.edu.tw/~armuro/pubs/chen-et-al-2025-mobilehci.pdf
LLM-generated notification digests deployed on Google Play for 3 months + 20 follow-up interviews. Users preferred summaries at **early morning and late night**; wanted priority tiers and graded information disclosure; but **sustained adoption was relatively low**, indicating a mismatch between generated summaries and expectations. The paper also synthesizes prior findings: batching notifications reduces perceived interruption, and opportune delivery timing increases engagement.
Design implication: digests are the right interaction shape, but content quality/expectation-fit decides whether they stick; timing preference is individual and learnable.

**2.12 "Pensieve: supporting everyday reminiscence" — Peesapati et al., CHI 2010**
Link: https://www.cs.cornell.edu/~danco/research/papers/peesapati-pensieve-chi2010.pdf
91 users over 5 months receiving occasional emailed "memory triggers" from their own social-media content. People **valued spontaneous reminders** to revisit their past; shorter, more general triggers drew more responses, and triggers containing users' own photos drew the most.
Design implication: resurfacing one's own past content via low-frequency, low-ceremony nudges is a validated, beloved pattern — the direct ancestor of a "memory digest."

**2.13 "Quologue: Dust Off Kindle Highlights…" — Kang, Odom, Chen & Neustaedter, CHI 2026**
Link: https://doi.org/10.1145/3772318.3790664
8-week field study (10 participants): an LLM app surfaced **one random e-book highlight per week** via keywords → reflection → "remix." Stepwise, low-volume surfacing generated "diverse reflective experiences" and even changed users' highlighting behavior.
Design implication: weekly cadence + minimal cues + user completion of the thought is a proven resurfacing recipe for personal archives.

**2.14 "IRCHIVER: An Information-Centric Personal Web Archive for Revisiting Past Online Sensemaking Tasks" — CHIIR 2025**
Link: https://jeffhuang.com/papers/Irchiver_CHIIR25.pdf
Passive full-page capture + OCR indexing; measured that users **re-found information more effectively, restored mental models more completely, and revisited past tasks more confidently** than with browser-native history.
Design implication: the measured value of a personal archive is *revisitation* — resurfacing and recap are the product surface where the archive proves its worth.

**2.15 Email triage & deferral baseline — Venolia et al. 2001; Sarrafzadeh et al., CHIIR 2019**
Links: https://www.interruptions.net/literature/Venolia-01-88.pdf ; https://doi.org/10.1145/3295750.3298960
The canonical email framework names **flow vs triage** as distinct activities; the CHIIR 2019 interview+survey study finds deferral is pervasive (77% of respondents had ≥1 deferred email that day; 44% deferred ≥5 daily) and that triage sessions cluster at arrival/re-entry moments (morning, post-meeting).
Design implication: digests should map onto existing triage rituals (morning / end-of-day), and "defer" must be a first-class digest action.

### What the literature endorses / warns against (Section 2)
**Endorses:** batching and scheduled digests at user-routine moments (2.11, 2.15); task-boundary timing and capped frequency (2.6, 2.7); adjustable proactivity levels with an internal "should I speak" gate (2.5); explanations at initiation + incremental disclosure (2.9, 2.10); acceptance/rejection telemetry as the learning signal (2.4, 2.6); low-frequency resurfacing of personal content (2.12, 2.13).
**Warns against:** streaming unrequested notifications (2.1, 2.2 — speed masks stress); fixed-clock check-ins (2.8 — 32% unanswered); high-frequency suggestion spam (2.6 — preference halves); purely informational, non-actionable pushes (2.6); assuming attention is free because tasks still got done (2.2).

---

## Section 3 — Privacy, erasure, unlearning, and attribution for memory systems

**3.1 "When Machine Unlearning Meets Retrieval-Augmented Generation (RAG): Keep Secret or Forget Knowledge?" — Wang, Zhu, Ye & Zhou, arXiv 2410.15267 (2024/2025)**
Link: https://arxiv.org/abs/2410.15267
Proposes lightweight **behavioral unlearning by modifying the external knowledge base** of a RAG pipeline — no weight access, no gradient ascent, works on closed-source models (ChatGPT, Gemini, PaLM 2) — and evaluates it against five criteria (effectiveness, universality, harmlessness, simplicity, robustness). Explicitly contrasts with weight-level unlearning's "high computational demands, limited applicability, or the risk of catastrophic forgetting," and extends to LLM-based agents.
Design implication: direct support for the architectural claim — **deletion in a retrieval store is cleaner, cheaper, and verifiable in a way weight-level unlearning is not.**

**3.2 "Learning to Erase Private Knowledge from Multi-Documents for Retrieval-Augmented Large Language Models" (Eraser4RAG) — Wang et al., arXiv 2504.09910 (2025)**
Link: https://arxiv.org/abs/2504.09910
Introduces the privacy-erasure task for RAG: user-defined private knowledge must be removed across documents while keeping public knowledge — crucially using a **global knowledge graph to defend against multi-document de-anonymization** (the fact you deleted can be reconstructed from neighbors). Outperforms GPT-4o-based rewriting on erase performance.
Design implication: single-record deletion is insufficient; deletion must cascade across derived/related artifacts or users remain re-identifiable.

**3.3 "Do LLMs Really Forget? Evaluating Unlearning with Knowledge Correlation and Confidence Awareness" — arXiv 2506.05735 (2025)**
Link: https://arxiv.org/abs/2506.05735
Shows current unlearning evaluation **overestimates** forgetting: facts presumed erased can be re-inferred through correlated knowledge (e.g., forgetting "Fuji is a volcano" fails while "Fuji has a crater" + "craters form volcanically" persist). Introduces knowledge-graph-based probing and an LLM-judge protocol.
Design implication: any "we deleted it" claim needs adversarial verification, not just absence-of-hit checks.

**3.4 "ReLearn: Unlearning via Learning for Large Language Models" — ACL 2025**
Link: https://aclanthology.org/2025.acl-long.297.pdf
Documents that reverse-optimization unlearning (gradient ascent / NPO) causes a "probability seesaw" that degrades fluency and coherence (repetitive, "Alzheimer's-like" outputs); proposes positive-learning replacement and metrics — Knowledge Forgetting Ratio (KFR), Knowledge Retention Ratio (KRR), Linguistic Score (LS).
Design implication: weight-side deletion damages the host; store-side deletion doesn't. For Orivory the model is fungible — the memory store is the durable, governable asset.

**3.5 "Unveiling Privacy Risks in LLM Agent Memory" (MEXTRA) — Wang et al., ACL 2025**
Link: https://aclanthology.org/2025.acl-long.1227/
First systematic black-box **memory-extraction attack** on LLM agents: crafted prompts plus automated prompt generation extract past user queries from the memory module; with 50 attacking prompts, agents leaked **>30% of stored private user queries** (edit-distance memory) and >10% (cosine-similarity memory). Concludes there is "an urgent need for effective memory safeguards."
Design implication: agent memory is a proven attack surface even under isolation-by-identifier; extraction probing should be part of Orivory's security testing.

**3.6 "Isolated but Exposed: Persistence-Based Memory Extraction Attack on LLM Agents" (SPORE) — arXiv 2607.23444 (2026); "ADAM" — arXiv 2604.09747; "MRMMIA: Membership Inference Attacks on Memory in Chat Agents" — arXiv 2605.27825**
Links: https://arxiv.org/html/2607.23444 ; https://arxiv.org/html/2604.09747v1 ; https://arxiv.org/html/2605.27825
The 2026 wave: SPORE shows **memory isolation alone is insufficient** — agents leak LTM contents through tool-invocation parameters, and injected payloads can persist and reactivate across sessions (up to 80% record extraction; 47% with only 20 triggers; extracted records linkable to identities via OAuth). MRMMIA shows membership inference (does "X" exist in this agent's memory?) works against Mem0- and MemGPT-style backends.
Design implication: for a self-hosted memory hub, tool-call output filtering, per-user memory partitioning, and anomaly detection on retrieval patterns are not optional.

**3.7 "A Survey on Long-Term Memory Security in LLM Agents" — arXiv 2604.16548 (2026)**
Link: https://arxiv.org/html/2604.16548v2
Frames agent memory across a lifecycle (Write, Store, Retrieve, Execute, Share & Propagate, **Forget & Rollback**) and argues LTM security "cannot be retrofitted at retrieval or execution time alone, but must be anchored in **storage-time provenance, versioning, and policy-aware retention**"; proposes Verifiable Memory Governance primitives (snapshots, write logs, diff-auditable histories, post-deletion verification).
Design implication: this is effectively the spec for erasure-as-a-feature: provenance + versioning + auditable rollback, designed in from storage time.

**3.8 "Right to be Forgotten in the Era of Large Language Models: Implications, Challenges, and Solutions" — Zhang et al., AI and Ethics (2024/2025)**
Link: https://doi.org/10.1007/s43681-024-00573-9
Maps GDPR Art. 17 onto LLM systems; warns that **guardrail/suppression approaches are not genuine removal** ("the data is not genuinely removed in accordance with the law, so systems [that] only implement guardrails… may still face compliance issues"), while retraining-from-scratch cannot meet "undue delay."
Design implication: compliance-grade erasure = actual purge of the store + indexes + derived artifacts + audit manifest; prompt-level "please forget" is not deletion.

**3.9 "What Should LLMs Forget? Quantifying Personal Data in LLMs for Right-to-Be-Forgotten Requests" (WikiMem) — arXiv 2507.11128 (2025)**
Link: https://arxiv.org/abs/2507.11128
Builds 5,000+ canaries over 243 human properties and a metric to rank memorized human–fact associations across 15 LLMs; memorization correlates with subject web presence and model scale. Reviews the legal landscape (EDPB: models trained on personal data can't be presumed anonymous).
Design implication: "forget-set construction" (finding everything about a person before deleting) is a recognized research problem — Orivory's per-user data model makes it tractable, which is a genuine self-hosted advantage over cloud LLMs.

**3.10 "Unlearning at Scale: Implementing the Right to be Forgotten in Large Language Models" — arXiv 2508.12220 (2025)**
Link: https://arxiv.org/abs/2508.12220
Treats RTBF as a reproducible systems problem: deterministic training replay filtered by a forget closure yields bit-identical parameters to retraining; complements with micro-checkpoints, adapter deletion, and **audit-gated** approximate paths.
Design implication: even the strongest weight-level work ends at auditability; store-level systems reach the same audit bar with vastly less machinery.

**3.11 "Measuring Attribution in Natural Language Generation Models" (AIS) — Rashkin et al., Computational Linguistics 49, 2023**
Link: https://aclanthology.org/2023.cl-4.2.pdf
The standard attribution framework: a statement is **Attributable to Identified Sources** if an evaluator would say "According to P, s" using only source P; defines a two-stage annotation pipeline (interpretable? → attributable?) validated across QA, summarization, and table-to-text with released guidelines/data.
Design implication: AIS is the human-eval gold standard for "the answer cites real sources."

**3.12 "Enabling Large Language Models to Generate Text with Citations" (ALCE) — Gao, Yen, Yu & Chen, EMNLP 2023**
Link: https://aclanthology.org/2023.emnlp-main.398/
The standard automatic benchmark: end-to-end retrieval + cited generation evaluated on **citation recall and citation precision** via NLI (explicitly AIS-aligned), plus fluency (MAUVE) and correctness. Finding that keeps the bar honest: even the best systems lacked complete citation support ~50% of the time on ELI5.
Design implication: citation recall/precision are the metrics Orivory should CI-track for all memory-grounded answers — with the caveat that ~50% support-failure among SOTA systems means this needs real investment, not a demo.

### What the literature endorses / warns against (Section 3)
**Endorses:** store-level deletion as the tractable erasure path (3.1, 3.10); provenance/versioning/rollback designed at storage time (3.7); deletion with cascade + adversarial verification (3.2, 3.3); AIS-style attribution plus ALCE-style automatic citation recall/precision as the measurement standard (3.11, 3.12).
**Warns against:** assuming weight-level unlearning is solved (3.3, 3.4); assuming memory isolation is protection (3.6); prompt-level "forgetting" as compliance (3.8); shipping cited answers without measuring support (3.12).

---

## Implications for Orivory

1. **Make capture the 10-second path.** The strongest replicated finding in PIM is that capture speed and lack of imposed structure decide adoption (1.2, 1.3). Default capture = free text/auto-ingest with zero required fields; every structure is added later, by AI or by the user.
2. **Automate the organizing tax, explicitly.** Auto-tagging, auto-linking, and note-upkeep should run in the background as reviewable suggestions (1.7 quotes the exact pain; 1.10–1.13 validate the pattern). Targets: cheap local encoders for routing (1.11), LLM only where needed.
3. **Suggestions are accept/reject/edit, never silent writes.** Every AI organization action is a proposal with a one-tap accept (1.11, 1.10, 1.12); log acceptance rates as the core quality metric and retrain/rerank on rejections (1.4-style reward learning, 2.4).
4. **Keep raw input visible next to AI output.** Toggling between the user's original note and the AI-expanded version built trust in user studies (1.10); provenance links from every generated artifact to its source made experts faster and more confident (1.13).
5. **Default proactive surface = scheduled digest, not pushes.** Batch at user-routine moments (morning / evening preferences observed in 2.11; triage rituals in 2.15), one resurfaced item per period for reflection (2.12, 2.13), and never interrupt mid-flow — task-boundary timing only (2.7).
6. **Ship a proactivity dial with an internal gate.** Three levels (2.5) from "digest only" to "agent may initiate"; per-source and per-type toggles (2.10); explain why each proactive message fired, at initiation (2.9).
7. **Instrument churn like the studies do.** Track: proactive acceptance rate (2.6: 69/6 accepts/rejects), engagement vs disruption vs ignored ratios (2.7: 53/12/35%), unanswered-proactive-message rate (2.8: 32.4% = alarm), and digest open/action rate. Set guardrails (e.g., disruption <10%) and throttle automatically.
8. **Erase as a verified pipeline, not a DELETE.** On request: purge source record → purge embeddings/index → cascade derived artifacts (summaries, links, digests) → probe for correlated re-identification (3.2, 3.3) → write an audit manifest. Store-level deletion is architecturally cleaner than weight-level unlearning (3.1) — lean on that, and expose verifiable deletion as a self-hosted selling point (3.7).
9. **Harden the hub against memory attacks.** Assume extraction attempts (3.5: >30% leakage; 3.6: isolation insufficient): filter tool-call payloads, partition memory per user/agent, cap retrieval fan-out, log and alert on anomalous recall patterns; include memory-extraction probes in the security test suite.
10. **Adopt the standard metrics.** For answers: ALCE citation recall + precision with an NLI judge, AIS-style human spot-checks (3.11, 3.12). For erasure: KFR/KRR-style forget/retain ratios adapted to the store (3.4) plus post-deletion extraction probes (3.3). For proactivity: the acceptance/disruption/unanswered ratios above.
