# Orivory PRD v1.0

**RAG-native answer engine for researchers**

---

> *"The AI research assistant that answers questions from YOUR documents, shows you exactly where it found the answer, and discovers connections you forgot you made."*

---

## 1. Executive Summary

Orivory is a personal knowledge retrieval and reasoning engine built for knowledge workers, researchers, and analysts who are drowning in their own documents. Unlike general-purpose AI, Orivory answers questions exclusively from the user's uploaded corpus—PDFs, notes, web clips, emails—then shows exactly where it found each answer.

**The core bet:** Researchers don't need another AI that hallucinates confidently. They need one that says "I found this in your March notes, but I'm uncertain because X"—and still surfaces the answer. Trust through transparency is the product.

**The single metric that gates all growth investment:** Weekly Active Query Rate ≥ 70% among users who have uploaded 5 or more documents. Below 70% means the product has not earned a habit; growth spend is paused until retention is fixed.

**5-year TAM:** $14.8B market growing at 14.8% CAGR. No competitor owns "RAG-native researcher" positioning. Privacy-first architecture is the wedge: 70% of enterprise buyers cite data security as their top AI adoption obstacle.

**Why now:** RAG infrastructure has commoditized. The moat is not retrieval—it is confidence calibration, corrective-RAG fallback to web search when the corpus is silent, and the "unexpected discovery" moment that competitors fail to deliver at scale.

---

## 2. Problem Statement

### 2.1 Target User Pain Points

**The Drowning Researcher** (primary persona, see §4.1)

*"I have 8,000 papers in Zotero, 3 years of meeting notes in Notion, and a folder of industry reports I downloaded and never read. I *know* I read something about this last year. Where is it?"*

Core pain: Scattered personal knowledge. No single tool holds everything, and no existing tool connects across them. The user has the information; they cannot retrieve it.

**The Reluctant Archivist** (secondary persona, see §4.2)

*"I should be organizing my notes better. I don't have time to tag and structure everything. I just want to ask a question and get a real answer from my stuff—not from the internet."*

Core pain: Capture friction is too high. Every knowledge management system asks the user to do the organizing work *before* the tool is useful. Users abandon during setup.

**The Overwhelmed Consultant** (tertiary persona, see §4.3)

*"My clients ask me questions that span projects from 18 months ago. I have to search three tools, open six files, and reconstruct the answer from fragments. I sound like I'm not on top of my own work."*

Core pain: Temporal knowledge is lost. "What did I conclude about X in Q1?" breaks most tools because they treat all documents as equally fresh.

### 2.2 Current Alternatives and Their Gaps

| Alternative | What it does | The gap for researchers |
|---|---|---|
| **General AI (ChatGPT, Claude)** | Answers from training data | No source attribution; hallucinations; no private document access |
| **Notion AI** | Q&A within Notion workspace | Siloed to Notion; weak cross-document reasoning; no temporal memory |
| **Mem.ai** | Capture-first knowledge management | Good at capturing, weak at retrieval; users feel they do the work |
| **Elasticsearch + LLM** | Custom RAG pipeline | Requires engineering setup; no UX; not consumer-ready |
| **Perplexity** | Web search + AI synthesis | Answers from the internet, not from your documents |
| **AskYourPDF / ChatPDF** | Single-document Q&A | One file at a time; no cross-document synthesis; no memory |

**The positioning gap no one owns:** A tool that is researcher-first (not capture-first, not enterprise-first), treats source attribution as non-negotiable, and makes the "unexpected discovery" moment the default experience.

### 2.3 Opportunity

Setup abandonment is the #1 churn driver. Current solutions require users to import, tag, organize, and label before asking a single question. The opportunity is to invert this: upload a folder, ask immediately, and let the system teach itself from usage.

One hallucination = permanent trust loss. Accuracy is existential. Every wrong answer costs more than a missed answer. The product must signal uncertainty honestly—and still provide useful answers.

The aha moment is *unexpected discovery*: showing users something in their own documents they had forgotten or never connected. Only 50–60% of competitor users reach this moment. The goal is to make it the default, first-query experience.

---

## 3. Product Vision & Positioning

### 3.1 Vision Statement

**Orivory becomes the researcher's second memory.** You ask; it searches. You question; it cites. You explore; it discovers. Every answer is traceable to a source in your own knowledge base.

### 3.2 Positioning Matrix

| | **Orivory** | **Mem.ai** | **Notion AI** | **General AI** |
|---|---|---|---|---|
| **Answers from your documents** | ✓✓✓ Primary | ✓ Secondary | ✓ Within workspace | ✗ |
| **Source attribution** | ✓✓✓ Non-negotiable | ✗ | Limited | ✗ |
| **Multi-hop reasoning** | ✓✓✓ Core feature | ✗ | ✗ | ✗ |
| **Temporal memory** | ✓✓✓ Core feature | ✗ | ✗ | ✗ |
| **Corrective-RAG (web fallback)** | ✓✓✓ | ✗ | ✗ | ✓ |
| **Confidence signaling** | ✓✓✓ Visible | ✗ | ✗ | ✗ |
| **Zero-setup onboarding** | ✓✓✓ | ✓ | ✓ | ✓✓✓ |
| **Researcher positioning** | ✓✓✓ | Capture-first | Enterprise | General |

### 3.3 Competitive Differentiation

**The 5 SOTA Competitive Moats:**

1. **Corrective-RAG**: Self-critique pipeline that detects when the corpus cannot answer and falls back to web search with explicit framing ("Your documents don't address this directly, but the web says..."). Users never face a dead end, and the source boundary is always honest.

2. **Temporal Memory**: "What did I conclude about X in Q1?" is answered with explicit temporal scoping. The system tracks when documents were created/modified and weights recency without losing historical context. Time-series reasoning over personal knowledge is novel.

3. **Multi-hop Reasoning**: "How does paper A connect to my June notes?" requires the system to retrieve A, retrieve June notes, find the connection, and synthesize. This is not retrieval—it is reasoning over a personal knowledge graph. Competitors cannot do this across documents.

4. **Continual Learning**: User feedback on answers (thumbs up/down, correction flags) is stored and fed back into retrieval reranking. The system improves for *that user* over time. This is not fine-tuning—it is a lightweight feedback loop that changes embedding weights and ranking signals.

5. **Confidence Calibration**: Every answer is accompanied by a visible confidence indicator (high/medium/low/uncertain). The thresholds are calibrated against held-out evaluation sets. The system explicitly states when it is uncertain—and users trust it more for being honest.

---

## 4. User Personas

### 4.1 Persona 1: The Drowning Researcher

**Who she is:** Dr. Amara Chen, postdoctoral researcher in computational biology. Has 8 years of papers, lab notes in Markdown, thesis chapters, and a Zotero library of 3,000 references.

**Her goal:** Find the one relevant paper, experiment result, or note that contains the answer she needs—without manually searching through folders.

**Her quote:** *"I spend 45 minutes looking for something I already read. By the time I find it, I've lost my train of thought on the actual problem."*

**Her workflow:** Reads papers in the morning, takes notes in Obsidian, imports Zotero highlights via Zapier, has a messy `~/Downloads` full of PDFs. Wants to ask Orivory: *"What did I read about CRISPR off-target effects?"* and get an answer with citations.

**Her friction:** Hates tagging. Will not use any tool that asks her to organize before querying.

**Success signal:** She asks 3+ queries in her first session without uploading a single document manually (auto-import from Zotero/Obsidian).

---

### 4.2 Persona 2: The Reluctant Archivist

**Who he is:** Marcus Webb, management consultant at a boutique firm. Works across 6 clients simultaneously. Has meeting notes in Notion, client decks in Google Drive, and industry reports saved to a shared folder he hasn't opened in 6 months.

**His goal:** Sound like he has perfect recall. Answer client questions with confidence, backed by his own previous work.

**His quote:** *"I should be using my notes better. But the overhead of organizing everything is why I never do."*

**His workflow:** Attends a client meeting, exports the transcript, uploads it to Orivory alongside the relevant deck. Asks: *"What did we agree were the three biggest risks in the last three sessions?"*

**His friction:** He will not manually tag or categorize. He wants to dump and query.

**Success signal:** He uploads 10+ documents in the first week and asks 5+ queries without ever touching a settings menu.

---

### 4.3 Persona 3: The Overwhelmed Consultant

**Who she is:** Priya Sharma, senior analyst at a healthcare consultancy. Has regulatory documents, clinical trial summaries, and 3 years of market research reports. Her clients ask questions that span all of it.

**Her goal:** Cross-reference across time and source types. Answer: *"What has our analysis said about Alzheimer's drug approval timelines since 2021, and how has that changed?"*

**Her quote:** *"I've written three reports on this topic over two years. I have the answer somewhere—I just can't stitch it together fast enough to be useful in a client call."*

**Her workflow:** Uploads quarterly reports as they arrive. Asks synthesis questions that require the system to compare positions across time.

**Her friction:** She is skeptical of AI accuracy. One hallucination in a client-facing context destroys her trust permanently.

**Success signal:** She uses confidence indicators to decide whether to present an answer in a client meeting—meaning she trusts the calibration enough to use it as a decision tool.

---

## 5. Core Product Features

### 5.1 P0 — Q&A with Source Attribution

**What it is:** The user types a natural-language question. The system searches their uploaded documents and returns an answer with inline citations pointing to exact source passages.

**UI Description:**

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Ask Orivory...                                 [⏎ Send] │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  You asked: "What did my notes say about transformer scaling   │
│  laws?"                                                         │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Your notes mention scaling laws in three contexts:             │
│                                                                  │
│  1. In "Scaling AGI Safely" (Jan 2024), you wrote:              │
│     "Kaplan et al. show power-law scaling, but the data cuts    │
│     off at 1B params. The Chinchilla paper argues for a         │
│     different optimum."                                          │
│                                                                  │
│  2. In "ML Reading Log", an excerpt from Hoffmann et al.:       │
│     "Training compute-optimal models requires balancing model     │
│     size and dataset size roughly equally."                      │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  Confidence: ████████░░  82%  High                             │
│  Sources: 2 documents · 4 passages                              │
│                                                                  │
│  [↓ Expand all sources]  [Copy answer]  [Was this helpful? 👍👎]│
└─────────────────────────────────────────────────────────────────┘
```

**Clicking a source opens a side panel:**

```
┌──────────────────────────────┐
│  Source: "ML Reading Log"   │
│  ─────────────────────────  │
│  Added: Feb 14, 2024         │
│  Type: Web clip              │
│  ─────────────────────────  │
│  "...Training compute-       │
│   optimal models requires    │
│   balancing model size and   │
│   dataset size roughly       │
│   equally."                  │
│                              │
│  [Open full document →]      │
└──────────────────────────────┘
```

**Engineering requirements:**
- Retrieval: Hybrid BM25 + dense vector search (embedding model: `e5-base-v2` or equivalent)
- Citation grounding: Every answer span is mapped to a source node with a confidence score
- Citation format: `[Source: filename, line X–Y]` with hover tooltip showing full passage
- Reranking: Cross-encoder reranking after initial retrieval
- Latency target: First token < 2s, full answer < 8s for corpus ≤ 500 documents

**User quote for acceptance criteria:** *"I asked 'what was our revenue model in the Q1 proposal' and it cited the exact slide deck with the paragraph I remembered. That's the moment I trusted it."*

---

### 5.2 P0 — Confidence Signaling

**What it is:** Every answer carries a calibrated confidence score with an explanation of *why* the system is confident or uncertain.

**UI Description:**

```
┌────────────────────────────────────────────────────┐
│  Confidence: ██████░░░░  58%  Medium              │
│  ──────────────────────────────────────────────   │
│  "This answer is medium-confidence because:        │
│   • We found relevant passages in 2 of 12 docs    │
│   • The key claim (↑ 23%) appears in only 1 source│
│   • No passage directly addresses your timeframe   │
│     (Q3 2024)                                      │
│   [Learn how confidence is calculated →]          │
└────────────────────────────────────────────────────┘
```

**Three states:**

| State | Visual | Behavior |
|---|---|---|
| **High** (≥ 80%) | Solid green bar | Answer shown prominently; sources visible |
| **Medium** (50–79%) | Partial yellow bar | Answer shown with yellow caution border; explanation visible |
| **Low / Uncertain** (< 50%) | Red bar + warning icon | "I'm not sure your documents contain a clear answer. I found..." with web fallback or explicit "No relevant source found" |

**Engineering requirements:**
- Confidence score: Calibrated probability from a binary classifier (has_answer vs. no_answer) plus uncertainty from answer span overlap
- Explanation generation: Template-based explanation citing retrieval statistics (doc coverage %, passage recall)
- Calibrated thresholds validated on held-out eval set of 500 Q&A pairs
- Thresholds are adjustable in settings (strict/balanced/relaxed)

**User quote for acceptance criteria:** *"When it says low confidence and explains why, I know to go check myself. When it guesses with no signal, that's when I stop using it."*

---

### 5.3 P0 — Zero-Setup Onboarding

**What it is:** The user can ask their first question within 60 seconds of signing up—without uploading, organizing, or configuring anything. They upload documents gradually; the system works from the start.

**The Setup Cliff:** Setup complexity is the #1 churn driver. Every additional step before first query loses 15–20% of users. Zero-setup means: create account → paste a URL, drop a file, or ask a question → get an answer.

**UI Flow:**

```
Step 1 — Welcome Screen (5 seconds)
┌─────────────────────────────────────────┐
│  Welcome to Orivory.                   │
│  Your research memory, finally organized.│
│                                         │
│  Start by asking your first question.   │
│  (You can add documents anytime.)        │
│                                         │
│  [Start asking questions →]            │
└─────────────────────────────────────────┘

Step 2 — Empty State (before first document)
┌─────────────────────────────────────────┐
│  ┌─────────────────────────────────┐    │
│  │  Ask anything...          [→]  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  You haven't added documents yet.       │
│  Orivory works better with each one.  │
│                                         │
│  [Upload PDFs / docs]  [Paste text]     │
│  [Connect Notion]     [Connect Obsidian]│
│                                         │
│  ↓ Drag files here to upload            │
└─────────────────────────────────────────┘

Step 3 — First Answer (within 30 seconds of upload)
Answer shown with citation to the uploaded document.
System prompts: "Want to explore more documents?"
```

**Import connectors (Phase 1):**
- File upload: PDF, DOCX, TXT, Markdown (drag-and-drop)
- Paste text directly
- URL import (web clip saved to Orivory)
- Notion export (JSON)
- Obsidian vault sync (via plugin)

**Engineering requirements:**
- Document processing pipeline: PDF → text (pdfminer), DOCX → text (python-docx), Markdown → text (commonmark)
- Chunking: Recursive character splitting at 512 tokens with 64-token overlap
- Embedding: `e5-base-v2` with per-user vector namespace (no cross-contamination)
- Indexing: Async background indexing with progress indicator; queryable within 30 seconds of upload for documents ≤ 50 pages

**Success criteria:** ≥ 60% of new users complete their first query within 5 minutes of account creation, without manually uploading a document (using a sample corpus or the pasted-text flow).

---

### 5.4 P1 — Multi-hop Reasoning

**What it is:** The system answers questions that require chaining across multiple documents. Not "find me the answer in one document" but "here's how Document A connects to Document B."

**UI Description:**

```
You asked: "How does the customer feedback from our pilot
relate to the technical limitations I noted in October?"

Reasoning trace:
  Step 1: Found 3 passages in "Pilot Feedback Q3.pdf"
    → 12 customer complaints about response latency
  Step 2: Found 2 passages in "Engineering Notes Oct 2024.md"
    → "Latency caused by vector index rebuild at 10K docs"
  Step 3: Connecting...

  Answer: Your October notes identified the vector index
  rebuild as a technical bottleneck. The pilot feedback you
  collected in Q3 shows 12 customers specifically complained
  about response time degradation at scale. These appear
  to be the same issue: customers hit the bottleneck you
  were already documenting.

  [See full reasoning trace →]
```

**Engineering requirements:**
- Graph-based retrieval: Build a document-level and passage-level graph; multi-hop queries traverse the graph with a lightweight reasoning model (not full agentic loops)
- Query decomposition: Decompose multi-hop queries into sub-queries using a small LLM (≤ 7B parameters) with a prompt template
- Answer synthesis: Interleave sub-query answers using a synthesis prompt with explicit source grounding
- Max hops: 3 hops (4 documents) for MVP; configurable in settings
- Fallback: If graph traversal fails, answer with independent document findings and flag as "partial"

**User quote for acceptance criteria:** *"I asked 'does the customer feedback from the pilot match what engineering found in October?' and it connected two completely different documents I'd never grouped together. That was the moment I became a user."*

---

### 5.5 P1 — Temporal Memory

**What it is:** The system understands *when* information was recorded and can answer questions scoped to time periods. "What did I conclude about X in Q1?" is answered by time-bounded retrieval.

**UI Description:**

```
You asked: "What did I conclude about market sizing in Q1?"

Timeline filter: [Q1 2024 ▾]  ← Dropdown: Last 90 days / Q1 / Q2 / This year / All time / Custom range

Answer: In Q1 2024, your conclusion about market sizing appeared
in two documents:

• "Q1 Strategy.docx" (Feb 2024): "TAM estimate: $4.2B.
  SAM: $890M at current adoption curve."

• "Investor Prep.md" (Mar 2024): "Revised TAM to $5.1B after
  Gartner revised their forecast upward."

Note: Your Q2 notes revised this to $5.8B. View Q2 conclusions? [→]
```

**Engineering requirements:**
- Temporal metadata: Every document and chunk is indexed with created_at, modified_at, and (optionally) user-annotated date
- Time-aware retrieval: Filter and rerank results by temporal proximity to query's implied timeframe
- "Recent vs. stable" signal: Flag when a conclusion has been revised in newer documents (changed signal)
- Timeline UI: Interactive timeline showing when documents were added and when claims were made

**User quote for acceptance criteria:** *"I asked 'what did I think about this company in Q1?' and it showed me documents from exactly that period. That temporal filter is the feature I didn't know I needed."*

---

### 5.6 P1 — Corrective-RAG

**What it is:** When the corpus does not contain a relevant answer, the system does not hallucinate. Instead, it performs a web search with explicit framing: the corpus answer is N/A; here is what the web says; here is the source.

**UI Description:**

```
You asked: "What is the current FDA approval timeline for
         CAR-T cell therapies?"

Confidence: ████████░░  85%  (Web-enhanced)

Your documents do not contain specific FDA CAR-T approval
timeline information. I searched the web and found:

• FDA.gov (Oct 2024): "Standard CAR-T approval pathway:
  10–12 months for priority review, with additional time
  for BLA submission." — [Source]

• ASH Clinical News (Nov 2024): "Recent FDA guidance
  updates recommend..."

This information is from the web, not your documents.
[Why did I search the web? →]
```

**Engineering requirements:**
- No-answer detection: Binary classifier (answer exists in corpus vs. not); triggered when top-K retrieval confidence < threshold
- Web search integration: SerpAPI or Tavily API for web fallback
- Source separation: Explicit "from your documents" vs. "from the web" labeling throughout
- User control: Toggle to disable web fallback (strict private mode)
- Hallucination guard: LLM answer generation is constrained to only cite retrieved passages; citations outside retrieved set are flagged as errors in eval

**User quote for acceptance criteria:** *"The best thing it ever did was say 'I don't have that in your documents' and then Google it for me anyway. Better than making something up."*

---

### 5.7 P2 — Continual Learning

**What it is:** User feedback (thumbs up/down, correction flags, source reordering) is stored and used to improve retrieval rankings for that user over time.

**UI Description:**

```
After each answer:
┌────────────────────────────────────────────────┐
│  Was this helpful?  [👍] [👎]                  │
│  [Report error or misattribution →]            │
└────────────────────────────────────────────────┘

Report error modal:
┌────────────────────────────────────────────────┐
│  What was wrong?                               │
│  ○ Answer is factually incorrect               │
│  ○ Right answer, wrong source                  │
│  ○ Missing important source                    │
│  ○ Source cited incorrectly                    │
│                                                 │
│  Suggest a better source: [dropdown/search]   │
│  Additional context: [textarea]               │
│                                                 │
│  [Submit feedback]        [Cancel]             │
└────────────────────────────────────────────────┘
```

**Engineering requirements:**
- Feedback storage: Per-user, per-query, per-passage feedback stored in feedback table
- Retrieval adaptation: Feedback is used to reweight passage similarity scores (Boost known-relevant passages, suppress known-irrelevant ones)
- Implementation: No fine-tuning. Use a learned weight vector applied at reranking time. Re-rank model takes retrieval score + feedback signal as features
- Learning latency: Feedback reflected in next query (no retraining pipeline required for MVP)
- User dashboard: "How Orivory has learned from you" showing correction count, topic areas improved

**Success signal:** Users who submit ≥ 3 feedback items show ≥ 20% improvement in answer satisfaction scores within 2 weeks.

---

### 5.8 P2 — Team Knowledge Bases

**What it is:** Shared knowledge bases for small teams. A researcher and their PhD advisor share a corpus. A consultancy team shares project-relevant documents.

**UI Description:**

```
Sidebar:
  My Knowledge Base  ← Personal
  Lab Team            ← Shared (3 members)
  Client: Acme Corp   ← Shared (5 members)

Team KB view:
  ┌─────────────────────────────────────────┐
  │  Lab Team Knowledge Base                │
  │  Members: Dr. Chen, Marcus, Priya       │
  │  Documents: 142  ·  Last updated: 2h ago│
  │                                        │
  │  [Upload to Team]  [Invite Member]     │
  │                                        │
  │  Recent activity:                      │
  │  • Marcus uploaded "Q4 Results.pdf"    │
  │  • Priya asked "Which experiments..."  │
  │  • Dr. Chen annotated p.34 of "..."   │
  └─────────────────────────────────────────┘
```

**Engineering requirements:**
- Permission model: Owner, Editor, Viewer roles per knowledge base
- Document-level access: Not all documents in a KB are visible to all members (configurable)
- Query attribution: Answers show which team member's documents contributed
- Usage quotas: Per-team storage and query limits (TBD by pricing)
- Isolation: User's personal KB is always separate; cross-KB queries are not supported in MVP

---

## 6. User Flows

### 6.1 Onboarding Flow

**Goal:** User completes first successful query within 5 minutes, without reading documentation.

```
[Signup] → [Welcome + "Ask your first question"] →
  → [Empty state: "Add your first document?"] →
    → [Quick upload: drag PDF, paste text, or connect app] →
      → [Indexing spinner (0–30s)] →
        → [First answer with citation] →
          → [Celebration micro-moment: "Found in 2 sources!"] →
            → [Prompt: "Want to add more?"]
```

**Friction removal at each step:**
- No email verification gate before first query (verify email on second session)
- No document requirement before first query (use sample/demo corpus for first query if empty)
- No onboarding checklist or wizard
- Indexing happens in background; user can query immediately and receives results as documents are indexed

**Critical path metrics:**
- Time-to-first-query: Target ≤ 120 seconds from account creation
- Drop-off points tracked: Signup → First upload → First query → Second query
- Acceptance threshold: ≥ 70% of users who reach the upload step complete their first query

### 6.2 First Query Flow

**Goal:** The first query should produce a high-confidence answer that demonstrates the core value proposition—source attribution and corpus accuracy—in under 8 seconds.

```
[User types question] → [Debounce 300ms] →
  [Retrieval: hybrid search over user corpus] → [Reranking] →
    [Answer generation with inline citations] →
      [Confidence score + explanation] →
        [Answer displayed] → [Source panel on hover/click]
```

**Graceful degradation:**
- No documents: Show empty-state with "Add documents to get started" prompt
- Low confidence (<50%): Show answer with red confidence bar + "I found something but I'm not certain" framing
- Slow retrieval (>5s): Show skeleton loader with "Searching your documents..." progress
- Web fallback triggered: Show answer with explicit "from the web" badge

### 6.3 Report Error Flow

**Goal:** When a user reports an error, the system acknowledges, records the feedback, and shows immediate evidence that it listened.

```
[User clicks "Report error"] →
  [Modal: error type selection] →
    [User describes issue + optionally suggests correction] →
      [Feedback stored] →
        [Confirmation: "Thanks—I won't cite that passage that way again."] →
          [Immediate: rerank affected passages in-session]
```

**Recovery path:** If the user reports a hallucination (answer not grounded in any source), the system immediately re-runs retrieval with stricter citation requirements and shows the user what it finds.

**Trust recovery:** After a reported error, the system shows a visible improvement on the next query (adjusted retrieval weights or a "based on your feedback" badge). This demonstrates continual learning in real time.

---

## 7. Success Metrics

### 7.1 Primary Metric

**Weekly Active Query Rate (WAQR)**

$$\text{WAQR} = \frac{\text{Users who asked ≥ 1 query in the last 7 days}}{\text{Users who uploaded ≥ 5 documents}} \times 100$$

**Target:** WAQR ≥ 70%

**Why this metric gates all growth:**
- Uploading 5+ documents signals minimum viable corpus. Below this threshold, the user hasn't experienced the full product.
- Asking ≥ 1 query per week signals habit formation. Below this threshold, the product is not earning a place in the user's workflow.
- 70% is the threshold where the product has achieved product-market fit for the retention loop. Below 70%, no amount of growth investment will close the churn gap.

**Measurement cadence:** Weekly, rolling 4-week average.

**What to do if WAQR drops below 70%:**
1. Pause paid acquisition (no new users until fixed)
2. Root-cause analysis: Which cohort dropped? New users or existing?
3. Common causes: Indexing failures, accuracy regressions, onboarding friction
4. Fix the retention problem before scaling

---

### 7.2 Secondary Metrics

| Metric | Definition | Target | Cadence |
|---|---|---|---|
| **Time-to-first-query** | Seconds from account creation to first successful query | ≤ 120s | Weekly |
| **Query-to-answer latency (P95)** | Time from query submission to answer displayed | ≤ 8s | Daily |
| **Answer satisfaction score** | Thumbs-up rate across all queries | ≥ 75% | Weekly |
| **Source citation accuracy** | % of answers where human judges citations are correct | ≥ 92% | Bi-weekly (sampled) |
| **Confidence calibration error** | Difference between stated confidence and observed accuracy | ≤ 10% | Bi-weekly (sampled) |
| **Hallucination rate** | % of answers with unsupported claims | ≤ 3% | Bi-weekly (sampled) |
| **Multi-hop query rate** | % of queries that are multi-hop (decomposed) | ≥ 15% | Monthly |
| **Web fallback rate** | % of queries where corpus had no answer (web search triggered) | 10–30% | Monthly |

---

### 7.3 Leading Indicators

These metrics predict WAQR and give early warning before the primary metric moves.

| Indicator | Signal | Action if below threshold |
|---|---|---|
| **Upload completion rate** | % of users who start uploading who complete ≥ 5 documents | Improve upload UX; add connector integrations |
| **First-query satisfaction** | Thumbs-up rate on first query | Improve onboarding answer quality; consider sample corpus |
| **Session depth** | Avg queries per session | Improve answer quality; add related questions |
| **Day-7 retention** | % of users who return within 7 days of signup | Investigate onboarding drop-off |
| **Confidence acknowledgment rate** | % of users who expand the confidence explanation | Proxy for trust calibration; below 20% = users don't notice confidence signals |

---

## 8. Out of Scope (MVP)

The following are deliberately excluded from the MVP to preserve focus and avoid the Setup Cliff.

**Excluded from MVP:**

1. **Team knowledge bases** — Personal KB only in v1. Personal KB is the foundation; team sharing adds permission complexity, storage quotas, and billing complexity that are fatal at MVP scale.

2. **Continual learning feedback loop** — Handled with thumbs up/down; the learned reranking pipeline is P2.

3. **Multi-hop reasoning** — P1. Deferred after basic Q&A achieves WAQR ≥ 65%.

4. **Temporal memory** — P1. Basic time-filter on results is out; temporal reasoning over conclusions is P1.

5. **Web clip browser extension** — MVP uses URL import; extension is P2.

6. **Mobile app** — Web app only in v1. Mobile is P3.

7. **API access** — No public API in MVP. Internal API for connector integrations only.

8. **Zotero/Obsidian native sync** — File upload and URL import in MVP; native connectors are P1.

9. **Enterprise SSO** — Consumer-grade auth in MVP. SAML/OIDC is P2.

10. **Document editing** — View and annotate only. No collaborative editing.

---

## 9. Risks & Mitigations

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **Hallucination damages trust** | Critical | High | Corrective-RAG with explicit "no answer in corpus" fallback; citation verification pipeline; 3% hallucination rate ceiling enforced in eval |
| **Setup cliff loses users at onboarding** | Critical | High | Zero-setup first query; async background indexing; sample corpus for first query; no email verification gate |
| **Indexing latency breaks first impression** | High | Medium | Target 30s indexing for ≤50-page documents; skeleton loader during indexing; query-while-indexing enabled |
| **Vector search quality insufficient for niche vocab** | High | Medium | Hybrid BM25 + dense retrieval; domain-adapted embedding fine-tuning (post-MVP); user feedback as correction signal |
| **Competitor launches "RAG-native researcher"** | Medium | Medium | First-mover advantage in confidence calibration and Corrective-RAG positioning; build community and dataset moat |
| **Privacy concerns block enterprise adoption** | Medium | High | Privacy-by-design: no data used for training without explicit consent; encryption at rest; SOC 2 Type II audit in Q3 |
| **Confidence calibration drift over time** | Medium | Medium | Weekly calibration eval against held-out set; threshold adjustment without retraining |
| **Users upload low-quality corpus** (garbage in, garbage out) | Medium | High | Document quality indicators; "Your corpus has low coverage for this topic" signal; document onboarding tips |

---

## 10. Appendix

### 10.1 Glossary

| Term | Definition |
|---|---|
| **RAG** | Retrieval-Augmented Generation. A pattern where an LLM generates answers grounded in retrieved documents rather than training data alone. |
| **Corrective-RAG** | A RAG variant where the system self-evaluates whether the retrieved context answers the query and falls back to alternative retrieval (e.g., web search) when it does not. |
| **Confidence Calibration** | The property that a system's stated confidence matches the observed accuracy. A calibrated 80% confidence means the answer is correct 80% of the time. |
| **Multi-hop Reasoning** | Answering a query that requires connecting information from multiple documents in sequence (A → B → answer). |
| **Temporal Memory** | The system's ability to distinguish when information was recorded and to scope answers to specific time periods. |
| **BM25** | A classical probabilistic information retrieval algorithm (Okapi BM25). Used alongside dense vector search for hybrid retrieval. |
| **Chunking** | Splitting a document into smaller passages (chunks) for embedding and retrieval. |
| **Embedding** | A dense vector representation of text. Used for semantic similarity search. |
| **Continual Learning** | The system's ability to improve from user feedback over time without full retraining. |

### 10.2 Technical Architecture Overview

```
User Input (Query)
       ↓
  Query Understanding (intent classification, temporal extraction)
       ↓
  ┌─────────────────────────────────────────┐
  │  Retrieval Engine                       │
  │  ├── BM25 sparse retrieval              │
  │  ├── Dense vector retrieval (e5-base)  │
  │  ├── Hybrid reranking (cross-encoder)   │
  │  └── Confidence scorer (binary + span)  │
  └─────────────────────────────────────────┘
       ↓
  ┌─────────────────────────────────────────┐
  │  Corrective-RAG Gate                    │
  │  ├── If confidence ≥ threshold: proceed │
  │  └── If confidence < threshold:         │
  │       web search fallback                │
  └─────────────────────────────────────────┘
       ↓
  ┌─────────────────────────────────────────┐
  │  Answer Generation                       │
  │  ├── Grounded answer with citations     │
  │  ├── Confidence bar + explanation       │
  │  └── Multi-hop trace (if applicable)    │
  └─────────────────────────────────────────┘
       ↓
  User Feedback Loop (thumbs up/down, corrections)
       ↓
  Learned Reranker (feedback → updated weights)
```

### 10.3 Evaluation Framework

**Internal eval dataset:**
- 500 human-annotated Q&A pairs covering 5 persona scenarios
- Ground-truth sources and correct citations annotated by domain experts
- Adversarial examples: queries designed to trigger hallucination

**Eval metrics:**
- Citation accuracy: % of cited passages that actually support the answer claim
- Hallucination rate: % of answers containing claims not grounded in any retrieved passage
- Confidence calibration: Brier score on binary correctness at each confidence threshold
- Answer quality: LLM-as-judge on coherence, relevance, and groundedness (1–5 scale)

**Eval cadence:**
- Pre-launch: Full eval on all 500 pairs
- Weekly: Automated regression suite (100 pairs, < 30 min)
- On-demand: After any retrieval model change or LLM swap

### 10.4 Open Questions for Engineering

1. **Chunk size trade-offs:** 512 tokens with overlap gives better recall but increases retrieval noise. Is there a corpus-type-specific chunking strategy that improves signal?

2. **Embedding model selection:** `e5-base-v2` is the current choice. Should we fine-tune on research-domain text (arXiv, PubMed) or keep general?

3. **Confidence threshold calibration:** What is the actual observed accuracy at our stated thresholds? Calibration needs to be validated against production data, not just held-out eval.

4. **Multi-tenant isolation:** For team KBs (P2), what is the right vector namespace isolation? Per-user? Per-KB? The cost/performance tradeoff is significant.

5. **On-device vs. cloud embedding:** For privacy-sensitive enterprise users (P2), would on-device embedding change the product's privacy positioning?

---

*PRD v1.0 — Orivory. Last updated: [Date]. Owner: [Product Lead]. Engineering contacts: [Backend Lead], [ML Lead].*
