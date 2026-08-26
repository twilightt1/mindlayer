# Orivory Positioning & Messaging Guide v1.0

> **Status:** Active — Internal & Partner Use  
> **Last Updated:** June 2025  
> **Owner:** Marketing & Product  

---

## Table of Contents

1. [Brand Positioning](#1-brand-positioning)
2. [Messaging Framework](#2-messaging-framework)
3. [Voice & Tone](#3-voice--tone)
4. [Content Templates](#4-content-templates)
5. [Messaging by Stage](#5-messaging-by-stage)
6. [Talking Points](#6-talking-points)
7. [Visual Identity Guidelines](#7-visual-identity-guidelines)

---

## 1. Brand Positioning

### 1.1 Brand Pillars

**Trust through transparency**
Every answer Orivory produces shows the exact source — paragraph, page, document. No black boxes. Researchers cite with confidence because they know where every fact originates.

**Research-grade accuracy**
Built on Corrective-RAG: self-critique + web fallback. When the answer isn't in your documents, Orivory tells you and points to where it went looking. Uncertainty is displayed, not hidden.

**Your knowledge, amplified**
Orivory indexes what you already know — notes, papers, emails, annotations — and surfaces connections you forgot you made. The insight was always there. Now you can find it.

---

### 1.2 Positioning Statement

**One-liner**

> The AI research assistant that answers questions from *your* documents, shows you *exactly* where it found the answer, and discovers connections you forgot you made.

**Three-point differentiation**

| Dimension | Orivory | Typical AI Tools |
|---|---|---|
| **Source** | Always cites your documents | May hallucinate; source unknown |
| **Uncertainty** | Confidence scores visible | Hides when it doesn't know |
| **Connections** | Multi-hop reasoning across your knowledge | Single-hop Q&A only |

**Target audience definition**

> Knowledge workers, researchers, analysts, consultants, and PhD students who accumulate personal knowledge faster than they can search it — and are tired of knowing something exists "somewhere in my files" but having no way to find it.

---

### 1.3 Competitive Differentiation Matrix

#### vs. Mem.ai

| | **Mem.ai** | **Orivory** |
|---|---|---|
| **Core philosophy** | Capture-first; auto-organizes via AI | Retrieval-first; answers questions from what you have |
| **Source transparency** | Surfaces connections; doesn't always show provenance | Every answer shows exact document + paragraph |
| **Temporal queries** | Limited | "What did I conclude in Q1?" — temporal memory built in |
| **Uncertainty display** | No explicit confidence scoring | Visible confidence calibration per answer |
| **Best for** | Passive capture; "I might need this someday" | Active retrieval; "I know I read something about X" |

**Messaging:** "Mem helps you capture. Orivory helps you *find* what you already captured."

---

#### vs. Notion AI

| | **Notion AI** | **Orivory** |
|---|---|---|
| **Core philosophy** | Enterprise workspace + AI assist | Personal knowledge RAG engine |
| **Scope** | Team documents; collaborative | Personal knowledge; private |
| **Citations** | Rewrite/summarize; minimal source linking | Exact paragraph-level citations for every claim |
| **Multi-hop** | Single-page context | Cross-document reasoning chains |
| **Setup** | Requires structured workspace | Zero-setup; index and ask |

**Messaging:** "Notion AI writes in your workspace. Orivory searches *across* your workspace."

---

#### vs. Obsidian Copilot

| | **Obsidian Copilot** | **Orivory** |
|---|---|---|
| **Core philosophy** | Local-first; privacy-focused plugin | RAG-native answer engine |
| **Data location** | Local vault only | Indexes personal documents wherever they live |
| **Reasoning depth** | Single-hop; plugin-limited | Multi-hop reasoning with citation chains |
| **Confidence** | No uncertainty display | Calibrated confidence scores |
| **Web fallback** | No | Yes — Corrective-RAG auto-escalates |

**Messaging:** "Obsidian Copilot queries your vault. Orivory reasons *across* your vault and the web when needed."

---

#### vs. General AI (ChatGPT, Claude, etc.)

| | **General AI** | **Orivory** |
|---|---|---|
| **Knowledge source** | Training data; general knowledge | *Your* documents; personal knowledge |
| **Hallucination risk** | High on specialized/niche topics | Near-zero on indexed content |
| **Source** | Cannot provide; training data | Exact paragraph + document for every answer |
| **Privacy** | Data may be used for training | Private; your data stays yours |
| **Temporal context** | No awareness of "what I thought last quarter" | Temporal memory; date-aware queries |

**Messaging:** "ChatGPT knows everything. Orivory knows *what you know*."

---

## 2. Messaging Framework

### 2.1 Core Messages

**Primary message (one sentence)**

> Orivory turns your personal knowledge into a searchable, reasoning, answerable brain — with receipts for every answer.

**Supporting message 1 — Source transparency**

> Every answer Orivory gives comes with a citation. Not "the model said so" — the exact paragraph from your document. Copy it. Cite it. Trust it.

**Supporting message 2 — Confidence calibration**

> Orivory shows its confidence score on every answer. When it's uncertain, you see it. No confident wrong answers hiding behind a polished response.

**Supporting message 3 — Connection discovery**

> Orivory connects what you know. Ask "How does the market analysis from March relate to the customer interviews in May?" and get a reasoned answer — not a keyword search.

---

### 2.2 Audience-Specific Messages

#### Researchers

> "You spent three years accumulating papers, notes, and datasets. Orivory turns that stack into a searchable, answerable knowledge base — with citations that hold up to peer review."

**Pain points addressed:** Information overload, citation management, knowledge scattered across tools, difficulty recalling where a finding lives.

---

#### Consultants

> "Your competitive intelligence lives in 400 client documents. Orivory indexes all of it and answers questions like 'Which clients mentioned regulatory risk in Q2?' with exact sources."

**Pain points addressed:** Client knowledge silos, inability to quickly recall prior findings, risk of "I think I read that somewhere."

---

#### PhD Students

> "Your advisor asks a question about your literature review. Orivory answers from your annotated PDFs and notes — with citations."

**Pain points addressed:** Literature review chaos, lost annotations, difficulty demonstrating knowledge provenance during discussions.

---

#### Enterprise Teams

> "Your team's institutional knowledge — reports, meeting notes, research — stays accessible even when the person who wrote it isn't around. Orivory indexes it. Answers it. Cites it."

**Pain points addressed:** Knowledge loss on attrition, tribal knowledge bottlenecks, difficulty onboarding to project history.

---

### 2.3 Feature-Specific Messages

#### Q&A with Citations

**Short:** Ask in natural language. Get answers with exact paragraph citations.

**Extended:** Type a question. Orivory searches your indexed documents and returns an answer — with the specific paragraph, page, and document highlighted. Every claim backed by a receipt.

**Example UI copy:** *"According to your document 'Q1 Market Analysis.pdf' on page 3: 'Customer churn increased 12% following the pricing change.' [High confidence: 94%] [View source →]"*

---

#### Confidence Scores

**Short:** Know when Orivory is sure — and when it's guessing.

**Extended:** Each answer displays a confidence score. High confidence means the answer is well-grounded in your documents. Lower confidence triggers a "I searched your docs and found this, but I'm not certain — here's what I found on the web just in case."

**Example UI copy:** *"High confidence (91%): This answer is strongly supported by your indexed documents. [Show reasoning]"*

---

#### Multi-hop Reasoning

**Short:** Ask compound questions. Get chain-of-thought answers.

**Extended:** "How does X relate to Y?" isn't a single search — it's a reasoning chain. Orivory traces the connection, shows each step, and cites sources at every hop.

**Example:** *"Question: How does the regulatory change in 2024 affect our product roadmap? — Answer walks through: ① the regulation text, ② our compliance notes, ③ product spec changes, with citations at each step."*

---

#### Temporal Memory

**Short:** "What did I conclude in Q1?" — Orivory knows when you wrote what.

**Extended:** Temporal memory means Orivory understands *when* things happened in your knowledge base. Ask time-bound questions and get answers scoped to specific periods.

**Example:** *"Told the board in January we expected Q2 headwinds. [Source: Board Meeting Notes, January 15]"*

---

#### Zero-setup

**Short:** Connect your documents. Start asking questions.

**Extended:** No folder restructuring. No manual tagging. No workspace redesign. Orivory indexes your documents as they are. Ask questions in plain English.

---

## 3. Voice & Tone

### 3.1 Brand Voice

**Confident but not arrogant**

- Say what Orivory does well. Don't overstate ("revolutionize") or hedge ("might help").
- Example — Good: "Orivory cites every answer to your own documents."  
  Example — Bad: "Orivory will totally transform the way you do research forever."

**Transparent about limitations**

- Acknowledge uncertainty openly. "Orivory didn't find this in your documents, so it searched the web" is a feature, not a failure.
- Never mask a knowledge gap with vague language.

**Research-oriented**

- Write for someone who cares about evidence, accuracy, and precision.
- Use the vocabulary of researchers and analysts — citation, provenance, confidence, evidence, retrieval.
- Avoid buzzwords, hype language, and startup superlatives.

**Clarity over cleverness**

- If a sentence can be misunderstood, rewrite it.
- Use concrete examples over abstract descriptions.
- Every claim should be verifiable or explicitly framed as an interpretation.

---

### 3.2 Tone Guidelines

#### By Situation

| Situation | Tone | Example |
|---|---|---|
| **Onboarding / first question** | Warm, clear, confident | "Here's what I found in your documents. Each claim links to its source — tap to check." |
| **High-confidence answer** | Direct, assured | "Customer churn increased 12% in Q2. [Source: Board Report, p.4]" |
| **Low-confidence / web fallback** | Honest, helpful | "I didn't find this in your documents, so I searched the web. Here's what I found:" |
| **Error state** | Calm, transparent, actionable | "Orivory couldn't access your document store right now. This usually resolves in a few minutes. [Retry →]" |
| **Empty state (no results)** | Constructive | "Orivory didn't find anything matching that query. Try rephrasing, or check if the relevant documents are indexed." |
| **Retention / usage nudge** | Informative | "You haven't asked a question in a while. Here's a prompt to get started: 'What did I conclude about...'" |

#### By Audience

| Audience | Adjustment |
|---|---|
| **PhD Researcher** | Lean into precision, citation culture, academic standards. Show the methodology behind multi-hop reasoning. |
| **Consultant** | Emphasize speed, client-ready citations, competitive intelligence. Focus on time saved. |
| **Enterprise team** | Stress security, institutional knowledge retention, onboarding value. Address IT/privacy concerns proactively. |
| **Casual / solo researcher** | Keep it simple. Avoid jargon. Show the "aha moment" of finding something they forgot they knew. |

---

### 3.3 Word Bank

#### Use These Words

- cite, citation, source, provenance, evidence, document, index, retrieval, answer, confidence, uncertain, find, search
- research, knowledge, documents, papers, notes, annotate
- connects, relates, reasoning, chain, trace
- transparent, honest, exact, precise
- "your documents," "what you know," "your knowledge"

#### Avoid These Words

| Avoid | Reason | Use Instead |
|---|---|---|
| "Revolutionize" | Hype; undermines credibility | "Change how you access," "transform your workflow" |
| "Magic" / "magically" | Imprecise; erodes trust | "Automatically," "instantly" |
| "Knows everything" | Overpromise; invites failure | "Answers questions from your documents" |
| "AI magic" | Vague; erodes transparency pillar | "RAG-native answer engine," "Corrective-RAG" |
| "Simply" (as in "simply do X") | Dismisses genuine complexity | Just describe the step |
| "Leverage" | Corporate buzzword | "Use," "access," "apply" |
| "Synergy" | Empty | Don't use this word ever |
| "Game-changing" | Superlative; no evidence | Specific outcome: "cuts research time by X%" |

---

## 4. Content Templates

### 4.1 Homepage Hero

**Headline (H1):**
> Your research. Your answers. With receipts.

**Subheadline:**
> Orivory is the RAG-native answer engine that searches your documents, reasons across them, and shows you exactly where it found every answer — including when it went to the web to find more.

**Primary CTA:** [Ask your knowledge base →]  
**Secondary CTA:** [See it in action]  
**Social proof line:** *Used by researchers at [X universities], [Y consulting firms], and [Z research teams]*

---

### 4.2 Feature Descriptions

#### Feature: Q&A with Citations

**Short (≤20 words):**
> Ask questions. Get answers. Every answer shows the exact paragraph from your document.

**Medium (≤50 words):**
> Orivory answers your questions by searching across all your indexed documents — and shows you the exact paragraph that supports each claim. No hallucination risk. No mystery sources. Just evidence-backed answers.

**Long (landing page):**
> Orivory's Q&A engine searches your entire personal knowledge base — papers, notes, PDFs, annotations, emails — and returns answers grounded in your own documents. Every claim is backed by an exact paragraph citation. Tap to expand the source. Copy the citation. Trust the answer.

---

#### Feature: Corrective-RAG with Web Fallback

**Short:**
> When your documents don't have the answer, Orivory searches the web and tells you it did.

**Medium:**
> Orivory's Corrective-RAG first checks your documents. If the answer isn't there, it transparently escalates to a web search — and shows you exactly where it went and what it found. No silent failures. No confident hallucinations. Just honest answers.

---

#### Feature: Multi-hop Reasoning

**Short:**
> Complex questions get chain-of-thought answers — with sources at every step.

**Medium:**
> "How does X relate to Y?" requires reasoning, not a single keyword search. Orivory traces connections across your documents, shows each step in the reasoning chain, and cites sources at every hop.

---

#### Feature: Temporal Memory

**Short:**
> "What did I conclude in Q1?" Orivory knows when you wrote what.

**Medium:**
> Your knowledge has a timeline. Orivory's temporal memory indexes not just *what* you wrote, but *when*. Ask time-bound questions and get answers scoped to specific periods — without manual date filters or folder archaeology.

---

#### Feature: Confidence Calibration

**Short:**
> Every answer comes with a confidence score. When Orivory doesn't know, you see it.

**Medium:**
> Orivory displays a calibrated confidence score on every answer — so you know whether the answer is well-grounded in your documents or needs further investigation. High confidence: answer is strongly supported. Low confidence: transparent escalation or disclaimer.

---

### 4.3 Email Templates

#### Welcome Email (Day 1)

**Subject:** Welcome to Orivory — your knowledge base is ready

**Body:**

> Hi [Name],
>
> Orivory is set up and ready. Here's what to do next:
>
> **1. Index your documents**
> Drag and drop papers, PDFs, notes, and reports into Orivory. It indexes everything and makes it searchable.
>
> **2. Ask your first question**
> Try something like:
> - "What did I conclude about [topic]?"
> - "What does my research say about [question]?"
> - "Show me everything I wrote about [subject] in Q1"
>
> **3. Notice the citations**
> Every answer Orivory gives includes the exact paragraph from your document. If the confidence score is high, you can cite it directly.
>
> Questions? Reply to this email or check the [docs].
>
> — The Orivory Team

---

#### Re-engagement Email (Day 7, no activity)

**Subject:** 3 questions Orivory can answer from your research

**Body:**

> Hi [Name],
>
> You joined Orivory [X days] ago but haven't asked a question yet. Here's what you might be wondering:
>
> 1. **"Did I already research this?"** — Ask Orivory. It searches your full knowledge base.
> 2. **"What did I conclude in [quarter/month]?"** — Orivory's temporal memory knows.
> 3. **"How does A relate to B?"** — Multi-hop reasoning traces the connection with citations.
>
> → [Go to Orivory and ask a question]
>
> — The Orivory Team

---

#### Feature Announcement Email

**Subject:** New: Temporal Memory — ask "What did I conclude in Q1?"

**Body:**

> Hi [Name],
>
> You asked for time-aware search. Orivory's Temporal Memory is now live.
>
> **What it does:**
> Orivory now tracks *when* content was written, not just *what* was written. Ask "What did I conclude about market dynamics in Q1?" and get answers scoped to that period — no manual date filtering needed.
>
> **How it works:**
> Temporal Memory indexes document metadata, annotation dates, and note timestamps. When you ask a time-bound question, Orivory scopes retrieval to the relevant period and shows you exactly which documents it drew from.
>
> **Example:**
> "What did I say about customer churn in Q1?"
> → Answer: "In your Board Meeting Notes from January 15, you noted: '[exact quote]'. Confidence: 89%."
>
> → [Try Temporal Memory now]
>
> — The Orivory Team

---

### 4.4 Social Media

#### Twitter/X

**Post 1 (awareness):**
> You spent 3 years accumulating research.
> Orivory makes it searchable.
> With citations.
> No hallucination. No mystery sources. Just answers from your own documents.
> → [link]

**Post 2 (feature):**
> "What did I conclude about that in Q1?"
> Orivory knows when you wrote what.
> Temporal memory is live. Try it: [link]

**Post 3 (competitive):**
> ChatGPT knows everything.
> Orivory knows what *you* know.
> With receipts.
> [brief comparison graphic]

**Post 4 (social proof / use case):**
> A PhD student told us:
> "I spent 20 minutes trying to find where I cited that paper. Orivory found it in 3 seconds and showed me the exact paragraph."
> That is the product.

---

#### LinkedIn

**Post (longer-form):**

> I spent three years building a research knowledge base.
> PDFs. Notes. Annotated papers. Meeting notes. Slack threads.
> I *knew* I had the answer to my advisor's question somewhere.
> I couldn't find it.
>
> That's the problem Orivory solves.
>
> Not "another AI that writes for you" or "AI that summarizes your meetings."
> Orivory is a RAG-native answer engine that:
> ✅ Searches your personal documents
> ✅ Answers questions in natural language
> ✅ Shows you the exact paragraph it found
> ✅ Displays a confidence score on every answer
> ✅ Escalates to the web when your documents don't have the answer
>
> The insight was always there. Now you can find it.
>
> [link to demo]

---

### 4.5 Error Messages

| Error State | Message |
|---|---|
| **Document index failed** | "Orivory couldn't index '[filename]'. This file may be corrupted or in an unsupported format. [Supported formats →]" |
| **No results found** | "Orivory didn't find anything matching your question in your documents. Try rephrasing, or check if the relevant documents are indexed." |
| **Web fallback triggered** | "Orivory didn't find a strong answer in your documents, so it searched the web. Here's what it found: [answer]." |
| **Low confidence answer** | "Orivory found something related, but confidence is low (47%). [Show what it found] [Refine your question →]" |
| **Service unavailable** | "Orivory is temporarily unavailable. Your indexed documents are safe — this usually resolves in a few minutes. [Retry →]" |
| **Session expired** | "Your session expired. Sign in again to continue. [Sign in →]" |
| **Rate limit** | "You've made many queries in a short time. Orivory will be ready to answer again shortly. [Learn about limits →]" |

---

## 5. Messaging by Stage

### 5.1 Awareness

**Objective:** Get the right person to say "yes, I have this problem."

**Core message:**
> Too much personal knowledge, scattered across tools. Can't find what you know you have.

**Channels:** Content marketing, SEO, social (LinkedIn, X), research communities, podcast appearances.

**Key content:**
- Blog post: "Why Researchers Can't Find What They Know" (pain-first; no product mention until 60% through)
- Comparison pages: "Orivory vs. [Obsidian / Notion AI / Mem / ChatGPT]" — honest, feature-matrix style
- SEO: Target queries like "how to search my own documents with AI," "AI research assistant with citations," "find information in my notes with AI"
- Short-form video: Screen recording of a complex question answered in 8 seconds with citation shown

**What not to do at this stage:** Lead with features. Lead with pain.

---

### 5.2 Consideration

**Objective:** Help the prospect understand Orivory is the right fit — specifically for researchers who need source transparency.

**Core message:**
> Orivory isn't another AI assistant. It's a RAG engine that answers questions from your documents, shows its work, and tells you when it doesn't know.

**Channels:** Product walkthrough, free trial, comparison pages, case studies, email sequences.

**Key content:**
- Interactive demo (live questions against a sample research corpus)
- Case study: "[Researcher Name], [Title]" — used Orivory to answer "[specific question]" in "[time saved]"
- FAQ page: "Does Orivory train on my data?" → "No. Your documents stay private."
- Email sequence: Pain → Product → Proof → CTA (3-email nurture)

**What not to do at this stage:** Over-claim on accuracy. Every statement about accuracy must acknowledge the confidence calibration feature.

---

### 5.3 Conversion

**Objective:** Convert trial to paid. Reduce friction in the decision.

**Core message:**
> Zero-setup. Start asking questions in 5 minutes.

**Tactics:**
- Trial experience: First 3 questions should be pre-loaded suggestions ("Try: 'What did I conclude about...'")
- Pricing page: Frame as time saved, not cost — "A researcher saves [X hours/week] searching their own documents. Orivory costs less than one hour of consultant time."
- Onboarding email sequence: Day 1 → Index your docs. Day 3 → Try a complex question. Day 7 → "Here's what others in your field are asking."
- Social proof placement: Show a real citation from a real demo document — not a mockup

**What not to do at this stage:** Hidden limits. Be transparent about document limits, query limits, and what happens at each pricing tier.

---

### 5.4 Retention

**Objective:** Drive habitual use. Turn new users into power users.

**Core message:**
> Orivory gets better the more you ask.

**Tactics:**
- In-app prompts: "You haven't asked a temporal question yet. Try: 'What did I write about [topic] in [quarter]?'"
- Periodic digest: "This week, Orivory answered [X] questions. Top query area: [topic]. [See all →]"
- Feature education: "New: Multi-hop Reasoning — ask connection questions now available"
- Feedback loop: "Was this answer helpful? [Yes / No]" → "What were you expecting?" — feeds continual learning
- Annual review nudge: "Your Orivory knowledge base contains [X documents]. Ask: 'What were my key findings this year?'"

---

## 6. Talking Points

### 6.1 Sales Talking Points

**Opening (discovery):**
> "Tell me about how you currently search through your research or personal knowledge."

**Bridge to Orivory:**
> "Most researchers we talk to say the same thing: 'I know I read it somewhere, I just can't find it.' That's the exact problem Orivory was built for."

**Feature highlights (lead with pain, not feature):**

| Pain | Orivory Feature | One-liner |
|---|---|---|
| "I can't find that citation I wrote" | Q&A + citations | "Orivory shows you the exact paragraph." |
| "I don't trust AI answers" | Confidence calibration | "Every answer has a confidence score. When Orivory doesn't know, you see it." |
| "ChatGPT doesn't know my documents" | Personal knowledge RAG | "Orivory answers from *your* documents, not training data." |
| "My knowledge is scattered" | Unified index | "Index papers, PDFs, notes — Orivory searches across all of it." |
| "I need to show my sources" | Source transparency | "Every answer is a citation-ready paragraph from your document." |

---

### 6.2 Support Talking Points

**First contact (user can't find a document):**
> "Let's check if the document was indexed. Can you share the filename or describe the document? I can verify its status in your index."

**Low confidence answer:**
> "The confidence score for this answer is [X%] — which means Orivory found relevant content but it's not a strong match. You might want to try rephrasing the question, or check if the relevant document is indexed."

**Web fallback explanation:**
> "Orivory first searches your personal documents. If it doesn't find a strong answer, it transparently escalates to the web and shows you exactly where it looked. You'll see the confidence score change and a note that web search was used."

**Privacy question:**
> "Your documents stay private. Orivory indexes them locally or in your private cloud — it never uses your personal documents to train its models. The RAG engine retrieves from your index, not from training data."

---

### 6.3 Competitive Objection Handling

#### "We already use Notion AI / Mem / Obsidian"

> "That's great — Orivory doesn't replace your note-taking tool. It indexes *output* from those tools and makes it searchable and answerable. If you've already got a vault full of knowledge in Obsidian, Orivory can index it and let you ask questions across it with citations. No need to change your workflow."

#### "ChatGPT already does this with custom GPTs"

> "Custom GPTs can reference documents, but they don't show you *which paragraph* the answer came from — and they have no confidence calibration. When ChatGPT doesn't find something in your documents, it silently falls back to its training data and sounds equally confident. Orivory shows a confidence score and explicitly tells you when it escalated to the web."

#### "This sounds complicated to set up"

> "That's the most common concern — and it's wrong. Orivory indexes documents automatically as you add them. No folder restructuring, no manual tagging, no taxonomy to maintain. You index your documents, you ask questions. That's the entire setup."

#### "How is this different from a vector database?"

> "A vector database stores embeddings. Orivory builds on top of that with Corrective-RAG — self-critique, confidence calibration, and web fallback. If Orivory can't answer from your documents, it tells you and searches the web. A vector database alone doesn't do any of that."

#### "We have compliance / data privacy concerns"

> "Orivory is RAG-native, not training-dependent. Your documents are used for retrieval, not training. We support [self-hosting / private cloud / on-premise] options for enterprise compliance requirements. Happy to walk through the security architecture in detail."

#### "It seems too good to be true"

> "The best way to know is to try it. [X-minute free trial, no credit card required]. Index three of your documents, ask five questions, and judge it on the citations — not the marketing copy."

---

## 7. Visual Identity Guidelines

### 7.1 Logo Usage

**Primary logo:**
Orivory wordmark — horizontal lockup on light backgrounds; white wordmark on dark backgrounds.

**Minimum clear space:** 1× the height of the wordmark on all sides.

**Do not:**
- Stretch or compress the logo
- Add drop shadows or effects
- Use the logo on busy photographic backgrounds without a clear space zone
- Recreate the logo with different typefaces

**Icon-only mark:** Use only in contexts where the full wordmark won't fit — app icon, favicon, social profile picture.

---

### 7.2 Color Palette

| Color | Hex | Usage | Avoid |
|---|---|---|---|
| **Deep Navy** | `#0D1B2A` | Primary text, headings, dark mode backgrounds | — |
| **Electric Blue** | `#2563EB` | Primary CTAs, links, active states | Using for decoration only |
| **Cyan Accent** | `#06B6D4` | Confidence indicators, secondary highlights | Overuse; reserve for data visualization |
| **Slate Gray** | `#64748B` | Body text on light backgrounds, metadata | Primary headings |
| **Mint Green** | `#10B981` | Success states, high-confidence indicators | Decoration |
| **Amber** | `#F59E0B` | Medium confidence indicators, warnings | Error states |
| **Coral Red** | `#EF4444` | Low confidence indicators, errors | Non-critical use |
| **Pure White** | `#FFFFFF` | Backgrounds, text on dark | — |
| **Off-White** | `#F8FAFC` | Card backgrounds, subtle sections | — |

**Confidence indicator gradient:**
- High (85–100%): Mint Green `#10B981`
- Medium (50–84%): Amber `#F59E0B`
- Low (0–49%): Coral Red `#EF4444`

---

### 7.3 Typography

**Primary typeface:** Inter

- H1: Inter Bold, 40px / 48px line-height
- H2: Inter Semibold, 32px / 40px line-height
- H3: Inter Semibold, 24px / 32px line-height
- Body: Inter Regular, 16px / 24px line-height
- Caption / metadata: Inter Regular, 13px / 20px line-height
- Code / citations: JetBrains Mono, 14px / 22px line-height

**Secondary typeface (headings only):** Playfair Display (for editorial contrast on hero sections)

**Accessibility:** Minimum body text contrast ratio: 4.5:1 against background. All text must pass WCAG AA.

---

### 7.4 Imagery Style

**Research authenticity over stock polish.**
- Use real screenshots of the Orivory interface wherever possible
- When using photography: Researchers working at desks, papers spread out, annotated documents — not posed corporate headshots
- Avoid: Flying paper, magnifying glasses, light bulbs, or generic "AI" imagery (neural networks, robot faces, glowing brains)
- Do: Show the citation card UI. Show the confidence indicator. Show the question → answer → source flow

**Data visualization:**
- Confidence scores: Horizontal bar, color-coded (green/amber/red)
- Citation blocks: Monospace text, left border in Electric Blue, document title + page above
- Reasoning chains: Connected nodes with source links between them

**Illustrations (if needed):**
- Minimal line art style
- Colors from palette only
- Topic: documents, search paths, connection nodes — never human figures with AI

---

## Appendix: Tagline Options

| Tagline | Use Case | Notes |
|---|---|---|
| "The AI research assistant that shows its work." | Landing page hero | Clear, confidence-building |
| "Your knowledge, answered. With receipts." | Social, email | Casual, memorable |
| "Find what you know." | App onboarding, empty state | Simple, pain-direct |
| "From scattered documents to confident answers." | Conversion page | Problem → solution |
| "The answer engine for researchers who cite." | Academic / PhD targeting | Niche-specific |

**Primary tagline (recommended):** "The AI research assistant that shows its work."

---

*End of Orivory Positioning & Messaging Guide v1.0*
