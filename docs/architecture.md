# MindLayer Technical Architecture v2.0

**Document Version:** 2.0  
**Last Updated:** 2026-01-19  
**Status:** Implementation Ready  
**Target Audience:** Engineering, Product, Research, DevOps

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Current Architecture Analysis](#3-current-architecture-analysis)
4. [SOTA Implementation Architecture](#4-sota-implementation-architecture)
   - [4.1 Corrective-RAG Pipeline](#41-corrective-rag-pipeline)
   - [4.2 Temporal Memory System](#42-temporal-memory-system)
   - [4.3 Multi-hop Reasoning](#43-multi-hop-reasoning)
   - [4.4 Continual Learning Pipeline](#44-continual-learning-pipeline)
   - [4.5 Confidence Calibration](#45-confidence-calibration)
5. [Data Architecture](#5-data-architecture)
6. [Infrastructure Requirements](#6-infrastructure-requirements)
7. [Monitoring & Observability](#7-monitoring--observability)
8. [Implementation Phases](#8-implementation-phases)

---

## 1. Executive Summary

MindLayer is a RAG-native answer engine for researchers, enabling intelligent retrieval-augmented generation over personal knowledge bases. This document defines the technical architecture for v2.0, which introduces five state-of-the-art techniques to significantly improve answer accuracy, temporal reasoning, multi-hop question answering, continuous learning, and confidence calibration.

### 1.1 Business Context

Researchers need to query their accumulated knowledge — papers, notes, documents — with natural questions. Traditional search fails because it doesn't understand semantic relationships, temporal context, or multi-step reasoning chains. MindLayer addresses this with an intelligent RAG pipeline that:

- Retrieves relevant documents using hybrid search (BM25 + dense vectors)
- Corrects retrieval failures by falling back to web search
- Reasons across multiple documents for complex questions
- Learns from user feedback to improve over time
- Provides calibrated confidence scores so users know when to trust answers

### 1.2 Current System Baseline

The v1.0 system operates with:

- **11-node LangGraph workflow** for answer generation
- **Hybrid retrieval**: BM25 + Vector search with Reciprocal Rank Fusion (RRF)
- **Jina-based reranking** for top-k document selection
- **Parent-child chunking** for granular retrieval with readable context
- **Agent trace recording** for observability
- **187 CI-safe tests** with full-repo ruff compliance

### 1.3 SOTA Techniques to Implement

| # | Technique | Primary Benefit | Research Source |
|---|-----------|----------------|-----------------|
| 1 | **Corrective-RAG (CRAG)** | 36.6% accuracy improvement on PubHealth | Yan et al., arXiv 2401.15884 |
| 2 | **Temporal Memory (TimeR4)** | Time-filtered retrieval with recency weighting | TimeR4 + EM-LLM research |
| 3 | **Multi-hop Reasoning (EfficientRAG)** | 10x efficiency improvement | EMNLP 2024 |
| 4 | **Continual Learning (Pistis-RAG)** | Closed-loop retriever improvement | Pistis-RAG framework |
| 5 | **Confidence Calibration** | Calibrated uncertainty estimation | Platt scaling / Isotonic regression |

### 1.4 Expected Impact Summary

| Metric | Current | Post-Implementation | Improvement |
|--------|---------|-------------------|-------------|
| Answer Accuracy (PubHealth benchmark) | ~65% | ~90% | +36.6% |
| Multi-hop Recall | ~70% | ~95% | +25% |
| Retrieval Efficiency | baseline | 10x faster | 10x |
| Confidence Calibration Error | ~25% | <5% | 4x |
| User Feedback Loop | none | weekly | new capability |

---

## 2. System Overview

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    CLIENTS                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Web App   │  │   Mobile    │  │   CLI       │  │   API       │           │
│  │  (SSE/WS)  │  │  (REST)    │  │  (REST)     │  │  Integration│           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
└─────────┼────────────────┼────────────────┼────────────────┼───────────────────────┘
          │                │                │                │
          └────────────────┴────────┬───────┴────────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │         FastAPI Gateway       │
                     │  ┌─────────────────────────┐ │
                     │  │ JWT Auth Middleware     │ │
                     │  │ Rate Limiter (Redis)    │ │
                     │  │ CORS Handler            │ │
                     │  │ SSE Streaming Handler   │ │
                     │  └─────────────────────────┘ │
                     └──────────────┬───────────────┘
                                    │
           ┌────────────────────────┼────────────────────────────────────────────┐
           │                        │                                              │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐             │
│  LangGraph Engine  │  │   Celery Workers  │  │   Admin API       │             │
│  (Recall Workflow) │  │   (Ingestion)    │  │   (Diagnostics)   │             │
└─────────┬─────────┘  └─────────┬─────────┘  └───────────────────┘             │
          │                     │                                                    │
    ┌─────┴─────────────────────┴─────┐                                         
    │                                   │                                         
┌───▼───┐  ┌──────┐  ┌───────┐  ┌────▼────┐  ┌──────────┐           
│Router │  │Memory│  │KG     │  │Retrieval│  │Eval/    │           
│(LLM)  │  │Hist. │  │Context│  │(Hybrid) │  │Calibr.  │  [NEW]   
└───┬───┘  └──┬───┘  └───┬───┘  └───┬───┘  └────┬─────┘           
    │         │           │          │             │                 
    └─────────┴───────────┴──────────┴─────────────┘                 
                      │                                                
      ┌───────────────┴──────────────────────────────────────────┐  
      │                    RETRIEVAL PIPELINE                        │  
      │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │  
      │  │  BM25   │  │ Vector  │  │  RRF    │  │ Reranker    │  │  
      │  │ (Redis) │  │(ChromaDB│  │ Fusion  │  │ (Jina API)  │  │  
      │  └─────────┘  └─────────┘  └─────────┘  └─────────────┘  │  
      └──────────────────────────────────────────────────────────────┘  
                                                                      

┌────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE LAYER                                  │
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│  │   PostgreSQL    │  │     Redis       │  │    ChromaDB     │           │
│  │                 │  │                 │  │                 │           │
│  │ • Users        │  │ • Rate Limits   │  │ • Vectors       │           │
│  │ • Conversations│  │ • BM25 Cache   │  │ • Col: per-conv│           │
│  │ • Messages     │  │ • Refresh Tokens│ │ • HNSW Index   │           │
│  │ • Memories     │  │ • SSE Task IDs  │  │                 │           │
│  │ • Entities    │  │ • Query Cache   │  └─────────────────┘           │
│  │ • Relations    │  │                 │                                  │
│  │ • Documents    │  └─────────────────┘                                  │
│  │ • Chunks       │                                                     │
│  │ • Feedback     │  ┌─────────────────┐  ┌─────────────────┐           │
│  │ • Eval Sets    │  │     MinIO       │  │   Celery Beat   │           │
│  └─────────────────┘  │                 │  │   (Scheduler)   │           │
│                         │ • Original Files│  │                 │           │
│                         │ • Parsed Text  │  │ • Retraining Jobs│ [NEW]    │
│                         │ • Media Assets  │  │ • Decay Tasks   │           │
│                         └─────────────────┘  └─────────────────┘           │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **FastAPI Gateway** | Request routing, auth, rate limiting, SSE streaming | FastAPI |
| **LangGraph Engine** | Orchestrates recall workflow as directed graph with state management | LangGraph StateGraph |
| **Router Agent** | Classifies query intent (simple/temporal/multi-hop) | LLM (OpenRouter) |
| **Memory Agent** | Loads conversation history for context | PostgreSQL |
| **Personal Context Agent** | Retrieves user memories related to query | ChromaDB + Redis |
| **Graph Context Agent** | Extracts entities/relations from knowledge graph | PostgreSQL KG |
| **Retrieval Agent** | Executes hybrid search (BM25 + Vector + RRF) | BM25 + ChromaDB |
| **CRAG Grader (NEW)** | Scores retrieved doc relevance, triggers web fallback | LLM |
| **Web Fallback (NEW)** | External search when local retrieval fails | Tavily/SERP API |
| **Reranker** | Re-ranks retrieved chunks using cross-encoder | Jina Reranker API |
| **Answer Agent** | Generates grounded, cited responses | LLM (OpenRouter) |
| **Confidence Calibrator (NEW)** | Statistical calibration of confidence scores | Python |
| **Celery Workers** | Async ingestion, embeddings, scheduled tasks | Celery + Redis |
| **MinIO** | Object storage for original files | MinIO S3-compatible |

### 2.3 Current LangGraph Workflow (11 Nodes)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      CURRENT LANGGRAPH WORKFLOW (v1.0)                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────────┐│
│    │  Router  │────▶│  Memory  │────▶│P.Context │────▶│  KG Context      ││
│    └──────────┘     └──────────┘     └──────────┘     └──────────────────┘│
│         │                                                        │         │
│         ▼                                                        ▼         │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────────┐│
│    │Retrieval │────▶│ParentExp.│────▶│ Reranking│────▶│  Grade Docs      ││
│    └──────────┘     └──────────┘     └──────────┘     └──────────────────┘│
│                                                                        │    │
│                                                                        ▼    │
│                                                           ┌──────────────────┐│
│                                                           │  Answer Gen      ││
│                                                           └──────────────────┘│
│                                                                        │    │
│                                                                        ▼    │
│                                                           ┌──────────────────┐│
│                                                           │ Grade Generation ││
│                                                           └──────────────────┘│
│                                                                              │
│  RETRY EDGES:                                                              │
│  - Grade Docs (irrelevant) ──────────────────────▶ Retrieval               │
│  - Grade Generation (hallucination) ─────────────▶ Answer Gen             │
│  - Grade Docs (irrelevant) ──────────────────────▶ Retrieval (max 3)       │
│  - Grade Generation (hallucination) ─────────────▶ Answer Gen (max 3)      │
│  - Retrieval (failed) ───────────────────────────▶ Retrieval (max 3)       │
│  - Answer Gen (failed) ─────────────────────────▶ Answer Gen (max 3)      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Target LangGraph Workflow (15 Nodes with SOTA)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      TARGET LANGGRAPH WORKFLOW (v2.0)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────────┐│
│    │  Router  │────▶│  Memory  │────▶│P.Context │────▶│  KG Context      ││
│    │ (detect  │     │          │     │ (temporal│     │                  ││
│    │  type)   │     │          │     │  filter) │     │                  ││
│    └──────────┘     └──────────┘     └──────────┘     └──────────────────┘│
│         │                                                        │         │
│         ▼                                                        ▼         │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────────┐│
│    │Retrieval │────▶│ParentExp.│────▶│ Reranking│────▶│  CRAG Grader     ││
│    │(temporal │     │          │     │          │     │  (NEW)           ││
│    │  boost)  │     │          │     │          │     └────────┬─────────┘│
│    └──────────┘     └──────────┘     └──────────┘              │         │
│                                                                │         │
│                     ┌───────────────────────────────────────────┤         │
│                     │                                           │         │
│                     ▼                                           ▼         │
│           ┌──────────────────┐                    ┌──────────────────┐│
│           │ Web Fallback      │◀──────────────────│ Grade Docs       ││
│           │ (NEW - if low    │                    │ (score < 0.5)    ││
│           │  confidence)     │                    └──────────────────┘│
│           └────────┬─────────┘                                   │         │
│                    │                                             ▼         │
│                    │                                   ┌──────────────────┐│
│                    └──────────────────────────────────▶│  Multi-hop       ││
│                                                        │  Reasoning      ││
│                                                        │  (NEW)          ││
│                                                        └────────┬─────────┘│
│                                                                 │         │
│                                                                 ▼         │
│                                                        ┌──────────────────┐│
│                                                        │  Answer Gen      ││
│                                                        │  + Confidence    ││
│                                                        │  (NEW)           ││
│                                                        └────────┬─────────┘│
│                                                                 │         │
│                                                                 ▼         │
│                                                        ┌──────────────────┐│
│                                                        │ Grade Generation ││
│                                                        └──────────────────┘│
│                                                                              │
│  NEW RETRY EDGES:                                                            │
│  - CRAG Grader (low confidence) ─────────────────────▶ Web Fallback         │
│  - CRAG Grader (ambiguous) ──────────────────────────▶ Query Transform       │
│  - Multi-hop (not converged) ────────────────────────▶ Retrieval (max 3 hops)│
│  - Answer Gen (low confidence) ──────────────────────▶ Calibrate Confidence   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.5 Data Flow (SOTA-Enhanced)

```
Query Input
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. ROUTER                                                           │
│    - Classify: simple / temporal / multi-hop / factual              │
│    - Output: query_type, routing_decision                          │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. CONTEXT GATHERING (parallel)                                      │
│    ├── Memory: conversation_history (last N turns)                   │
│    ├── Personal Context: related_memories (vector search)           │
│    ├── KG Context: entities + relations (entity extraction)         │
│    └── Temporal Context (NEW): time-filtered memories               │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. RETRIEVAL PIPELINE                                               │
│    ├── BM25: keyword search (Redis)                                │
│    ├── Vector: semantic search (ChromaDB, HNSW)                   │
│    ├── Temporal Filter (NEW): time-bounded retrieval                 │
│    └── RRF Fusion: merge rankings (k=60)                           │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. PARENT EXPANSION                                                  │
│    - Expand child chunks to parent documents                         │
│    - Preserve citation granularity at chunk level                     │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. CORRECTIVE-RAG (NEW - SOTA)                                       │
│    ┌──────────────────────────────────────────────────────────────┐   │
│    │ 5a. CRAG GRADER                                              │   │
│    │     LLM scores each doc: RELEVANT / PARTIAL / IRRELEVANT    │   │
│    │     Threshold: score < 0.5 → IRRELEVANT                      │   │
│    └──────────────────────────────────────────────────────────────┘   │
│    │                                                               │   │
│    ├── If >50% docs IRRELEVANT:                                    │   │
│    │   ┌──────────────────────────────────────────────────────┐   │   │
│    │   │ 5b. WEB FALLBACK                                     │   │   │
│    │   │      - Tavily API: live web search                    │   │   │
│    │   │      - Merge web results with existing context       │   │   │
│    │   │      - Re-score with CRAG grader                     │   │   │
│    │   └──────────────────────────────────────────────────────┘   │   │
│    │                                                               │   │
│    └── If docs PASSED: continue                                    │   │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 6. RERANKING                                                         │
│    - Jina Reranker API: cross-encoder scoring                        │
│    - Top-K selection (configurable, default 20)                      │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 7. GRADE DOCUMENTS                                                    │
│    - LLM evaluates: SUPPORTED / CONTRADICTS / NOT ADDRESSED          │
│    - Filters docs that don't support the answer                        │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 8. MULTI-HOP REASONING (NEW - SOTA)                                  │
│    ┌──────────────────────────────────────────────────────────────┐   │
│    │ For multi-hop queries: EfficientRAG pattern                 │   │
│    │  - Generate next-hop query from current context             │   │
│    │  - Recursive retrieval (max 3 hops)                         │   │
│    │  - Branch-solve-merge aggregation                           │   │
│    └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 9. ANSWER GENERATION                                                  │
│    - LLM generates answer with citations                             │
│    - Inline citations: [doc_1], [doc_2]                             │
│    - Confidence score per claim (NEW - SOTA)                          │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 10. CONFIDENCE CALIBRATION (NEW - SOTA)                              │
│     ┌──────────────────────────────────────────────────────────────┐   │
│     │ 10a. Per-claim confidence scoring                           │   │
│     │       - Statistical calibration against eval set             │   │
│     │       - Temperature-scaled softmax over retrieval scores     │   │
│     │       - Source diversity bonus                              │   │
│     │       - Temporal decay factor                                │   │
│     │                                                               │   │
│     │ 10b. Aggregate answer confidence                            │   │
│     │       - Weighted mean of claim confidences                  │   │
│     │       - Evidence count factor                               │   │
│     │       - Reranker score contribution                         │   │
│     └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 11. GRADE GENERATION                                                  │
│     - LLM evaluates answer quality, hallucination detection           │
└────────────────────────────────────────────────────────────────────────┘
     │
     ▼
Answer Output (SSE) + Feedback Collection Hook
```

---

## 3. Current Architecture Analysis

### 3.1 Strengths

| Area | Assessment | Evidence |
|------|------------|----------|
| **Production-Ready Foundation** | 187 CI-safe tests passing, full-repo ruff clean | Test suite coverage |
| **Orchestration** | LangGraph StateGraph provides clean, inspectable workflow with 6 retry edges | `app/graph.py` |
| **Hybrid Retrieval** | BM25 + Vector + RRF fusion is proven for recall | `app/retrieval/rrf.py` |
| **Vector Infrastructure** | ChromaDB with HNSW + cosine similarity is production-viable | `app/retrieval/vector_store.py` |
| **Async Processing** | Celery + Redis broker enables scalable background job processing | `app/tasks/` |
| **API Design** | SSE streaming for real-time responses; clean REST endpoints | `app/api/` |
| **Reranking** | Jina Reranker integration adds significant precision | `app/retrieval/reranker.py` |
| **Memory Architecture** | Conversation history + knowledge graph context covers most retrieval needs | `app/agents/` |
| **Chunk Hierarchy** | Parent expansion preserves document structure | Parent-child chunking |
| **Auth System** | JWT + OAuth with hashed refresh tokens, O(1) revocation | `app/auth/` |

### 3.2 Weaknesses

| Area | Issue | Impact | User Impact |
|------|-------|--------|-------------|
| **No Fallback Path** | When retrieval fails, answer quality degrades silently | High | Wrong answers for gaps in knowledge |
| **Flat Memory** | No temporal ordering or time-aware retrieval | Medium | Can't answer "what did I conclude last month?" |
| **Single-Hop Only** | Cannot handle multi-hop reasoning queries | High | Wrong answers for "what is X's relationship to Y?" |
| **Static Retriever** | No feedback loop to improve retrieval over time | Medium | Same retrieval failures repeat |
| **Opaque Confidence** | No calibrated confidence scores | High | Users don't know when to trust answers |
| **No Document Freshness** | No mechanism to prefer recent or authoritative sources | Medium | Stale information prioritized |
| **Chunking Strategy** | Fixed chunk size, no semantic-aware chunking | Low-Medium | Suboptimal retrieval granularity |
| **Rate Limiting** | Coarse-grained rate limits, no per-query-type limits | Low | No granular resource management |

### 3.3 Technical Debt

| Issue | Location | Impact | Effort | Priority |
|-------|----------|--------|--------|----------|
| BM25 rebuild in API process | `app/retrieval/bm25_retriever.py` | Latency spike on cold cache | Low | P2 |
| Missing conversation-scoped vector collections | `app/retrieval/` | Cross-conversation bleed risk | Medium | P1 |
| No retry queue for failed ingestions | `app/tasks/` | Lost documents | Medium | P2 |
| Hardcoded `k=60` for RRF | `app/retrieval/hybrid_retriever.py` | Non-optimal fusion | Low | P3 |
| No temporal indexes on timestamps | `app/models/memory.py` | Slow time-range queries | Low | P3 |
| Monolithic StateGraph | `app/graph.py` | Hard to test nodes independently | Medium | P1 |
| Hardcoded thresholds | Various | Not tunable without code changes | Low | P3 |
| No circuit breakers | Downstream services | Cascade failures | Medium | P2 |
| Missing distributed tracing | LangGraph nodes | Hard to debug production issues | Medium | P2 |

### 3.4 Scalability Limits

| Bottleneck | Current Limit | Scaling Strategy | Priority |
|-----------|--------------|-----------------|----------|
| ChromaDB single-node | ~10M vectors | Sharding or pgvector migration | P1 |
| Postgres connection pool | 10 + 20 overflow | PgBouncer, read replicas | P2 |
| Redis BM25 index | Memory-bound | Tiered storage, index pruning | P2 |
| SSE connection limit | ~1000/worker | Horizontal scaling with sticky sessions | P2 |
| LLM token limits | 128k context | Streaming, truncation strategies | P3 |
| Celery worker pool | Fixed pool size | Auto-scaling based on queue depth | P2 |

---

## 4. SOTA Implementation Architecture

### 4.1 Corrective-RAG Pipeline

**Research Background**: "Corrective Retrieval Augmented Generation" - Yan et al., arXiv 2401.15884

**Key Findings**:
- A lightweight classifier evaluates retrieval quality
- Three outcomes: RELEVANT (>0.7), PARTIAL (0.4-0.7), IRRELEVANT (<0.4)
- For IRRELEVANT cases, web search fallback dramatically improves accuracy
- **36.6% accuracy improvement** on PubHealth benchmark

#### 4.1.1 CRAG Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CORRECTIVE-RAG (CRAG) PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  Node: grade_retrieval                                                │  │
│  │  ───────────────────────────────────────────────────────────────────│  │
│  │  Input:  retrieved_documents[], query                                 │  │
│  │  Output: graded_docs[], needs_web_fallback: bool                       │  │
│  │                                                                       │  │
│  │  LLM Prompt:                                                         │  │
│  │  """                                                                 │  │
│  │  Grade the relevance of each document on 0-1 scale:                   │  │
│  │  - RELEVANT (≥0.7): Directly answers the query                         │  │
│  │  - PARTIAL (0.4-0.69): Contains useful context                         │  │
│  │  - IRRELEVANT (<0.4): Does not address the query                      │  │
│  │                                                                       │  │
│  │  Return: [                                                         │  │
│  │    {"doc_id": "...", "score": 0.85, "class": "RELEVANT",           │  │
│  │      "reasoning": "..."}                                             │  │
│  │  ]                                                                  │  │
│  │                                                                       │  │
│  │  Also return needs_web_fallback if <50% docs RELEVANT/PARTIAL.         │  │
│  │  """                                                                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                 │                                          │
│                                 ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    ROUTING DECISION                                   │  │
│  │                                                                       │  │
│  │   >50% RELEVANT/PARTIAL          │      <50% RELEVANT/PARTIAL        │  │
│  │   ┌─────────────────────┐        │      ┌─────────────────────┐      │  │
│  │   │ Continue to Rerank  │        │      │ Trigger Web Fallback │      │  │
│  │   └─────────────────────┘        │      └─────────────────────┘      │  │
│  │                                                                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEB FALLBACK (when triggered)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. QUERY EXPANSION                                                        │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Generate optimized search query:                                     │  │
│     │ - Incorporate key terms from query + context                       │  │
│     │ - Use precise terminology (not vague)                              │  │
│     │ - Max 20 words                                                     │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  2. WEB SEARCH (Tavily API)                                                │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ POST /search                                                        │  │
│     │ {                                                                  │  │
│     │   "query": "expanded query",                                       │  │
│     │   "search_depth": "advanced",                                     │  │
│     │   "max_results": 10,                                              │  │
│     │   "include_raw_content": true                                      │  │
│     │ }                                                                  │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  3. RESULT PARSING                                                         │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Parse and score web results:                                       │  │
│     │ - Extract title, content, URL, published_date                       │  │
│     │ - Apply domain filtering (block paywalled/spam)                    │  │
│     │ - Deduplicate by content hash                                      │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  4. MERGE + RE-SCORE                                                       │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Combine existing docs + web docs:                                   │  │
│     │ - Weight existing × 1.2, web × 0.8                               │  │
│     │ - Re-run CRAG grader on merged set                                 │  │
│     │ - Pass top-K to reranking                                         │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.1.2 Retrieval Grader Design

```python
# app/agents/crag_agent.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import json


class RetrievalGrade(str, Enum):
    """Classification levels for retrieved document relevance."""
    RELEVANT = "relevant"       # >= 0.7 - Directly answers query
    PARTIAL = "partial"        # 0.4-0.69 - Contains useful context
    IRRELEVANT = "irrelevant"   # < 0.4 - Does not address query


@dataclass
class GradedDocument:
    """A single document with CRAG grading."""
    doc_id: str
    score: float              # 0.0 - 1.0
    grade: RetrievalGrade
    reasoning: str
    source: str               # "local" or "web"
    key_information: Optional[str] = None  # Extracted relevant portion


@dataclass
class GradingResult:
    """Result from CRAG grading pipeline."""
    graded_documents: list[GradedDocument]
    needs_web_fallback: bool
    fallback_reason: Optional[str] = None
    consensus_score: float = 0.0  # Agreement among grader on relevance


# Threshold configuration
RELEVANT_SCORE_MIN = 0.7
PARTIAL_SCORE_MIN = 0.4
FALLBACK_THRESHOLD = 0.5  # % of docs that must be >= PARTIAL


GRADE_DOCS_PROMPT = """You are a retrieval quality assessor for a research assistant.
Evaluate whether the retrieved document chunk helps answer the user's question.

Classification Definitions:
- "relevant": Document contains information DIRECTLY relevant to answering the question.
              Even if incomplete, the relevant portions can be used.
- "partial": Document MAY contain relevant information but:
              1. It's mixed with irrelevant content
              2. The relevant part requires extraction
              3. Confidence is low
- "irrelevant": Document CONTRADICTS the question's premise OR is about a 
                completely different topic. Should NOT be used.

Question: {query}

Document Chunk:
{chunk_content}

Respond with JSON:
{{
    "score": 0.0-1.0,
    "classification": "relevant" | "partial" | "irrelevant",
    "reasoning": "brief explanation (1-2 sentences)",
    "key_information": "extracted relevant portion if partial/irrelevant" | null
}}
"""


async def grade_retrieval(
    documents: list[dict],
    query: str,
    threshold: float = FALLBACK_THRESHOLD,
) -> GradingResult:
    """
    Grade retrieved documents and determine if web fallback is needed.
    
    This is the core CRAG function that evaluates each document's relevance
    to the query and decides whether to trigger a web search fallback.
    
    Args:
        documents: List of document dicts with 'id' and 'content' keys
        query: The user's search query
        threshold: Minimum ratio of PARTIAL+ documents required (default 0.5)
    
    Returns:
        GradingResult with graded documents and fallback decision
    
    Algorithm:
        1. Create document summaries (first 500 chars)
        2. Call LLM with grading prompt for each doc (parallelized)
        3. Aggregate scores and determine fallback need
        4. Return GradingResult
    """
    if not documents:
        return GradingResult(
            graded_documents=[],
            needs_web_fallback=False,
            consensus_score=0.0
        )
    
    # Prepare document summaries for grading
    doc_summaries = [
        {
            "id": doc.get("id", f"doc_{i}"),
            "content": doc.get("content", "")[:500],
            "source": doc.get("metadata", {}).get("source", "local")
        }
        for i, doc in enumerate(documents)
    ]
    
    # Grade each document (parallelized LLM calls)
    graded_docs = []
    grading_tasks = [
        grade_single_document(doc["id"], doc["content"], query)
        for doc in doc_summaries
    ]
    
    results = await asyncio.gather(*grading_tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Log error, default to IRRELEVANT
            graded_docs.append(GradedDocument(
                doc_id=doc_summaries[i]["id"],
                score=0.0,
                grade=RetrievalGrade.IRRELEVANT,
                reasoning=f"Grading failed: {str(result)}",
                source=doc_summaries[i]["source"]
            ))
        else:
            graded_docs.append(result)
    
    # Calculate fallback need
    usable_count = sum(
        1 for d in graded_docs
        if d.grade in (RetrievalGrade.RELEVANT, RetrievalGrade.PARTIAL)
    )
    usable_ratio = usable_count / len(graded_docs)
    
    # Calculate consensus (variance in scores)
    scores = [d.score for d in graded_docs]
    consensus = 1.0 - (std(scores) / (max(scores) - min(scores) + 1e-8))
    
    # Determine fallback reason
    fallback_reason = None
    if usable_ratio < threshold:
        irrelevant_docs = [d for d in graded_docs if d.grade == RetrievalGrade.IRRELEVANT]
        fallback_reason = f"{len(irrelevant_docs)}/{len(graded_docs)} docs irrelevant"
    
    return GradingResult(
        graded_documents=graded_docs,
        needs_web_fallback=usable_ratio < threshold,
        fallback_reason=fallback_reason,
        consensus_score=consensus
    )


async def grade_single_document(
    doc_id: str,
    content: str,
    query: str,
) -> GradedDocument:
    """Grade a single document using LLM."""
    prompt = GRADE_DOCS_PROMPT.format(query=query, chunk_content=content)
    
    response = await llm_client.chat.completions.create(
        model=settings.GRADING_MODEL,  # Smaller model for efficiency
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    
    result = json.loads(response.choices[0].message.content)
    score = float(result["score"])
    
    # Classify based on score
    if score >= RELEVANT_SCORE_MIN:
        grade = RetrievalGrade.RELEVANT
    elif score >= PARTIAL_SCORE_MIN:
        grade = RetrievalGrade.PARTIAL
    else:
        grade = RetrievalGrade.IRRELEVANT
    
    return GradedDocument(
        doc_id=doc_id,
        score=score,
        grade=grade,
        reasoning=result.get("reasoning", ""),
        source="local",
        key_information=result.get("key_information")
    )
```

#### 4.1.3 Web Fallback Integration

```python
# app/agents/web_search_agent.py

from dataclasses import dataclass
from typing import Protocol
import httpx


class WebSearchProvider(Protocol):
    """Pluggable web search interface."""
    async def search(
        self, 
        query: str, 
        num_results: int = 10
    ) -> list[dict]: ...


@dataclass
class WebSearchResult:
    """Structured web search result."""
    url: str
    title: str
    content: str
    score: float
    published_date: str | None = None
    domain: str | None = None


@dataclass  
class WebFallbackResult:
    """Result from web fallback pipeline."""
    web_documents: list[WebSearchResult]
    merged_documents: list[dict]
    search_query_used: str
    domains_included: list[str]
    domains_excluded: list[str]


class TavilyWebSearch:
    """Tavily API implementation - primary web search provider."""
    
    BASE_URL = "https://api.tavily.com/search"
    
    # Blocked domains configuration
    BLOCKED_DOMAINS = {
        "example-paywalled.com",
        "spam-site.org",
        "known-scraper.io",
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def search(
        self, 
        query: str, 
        num_results: int = 10
    ) -> list[WebSearchResult]:
        """Execute web search via Tavily API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": num_results,
                    "include_answer": False,
                    "include_raw_content": True,
                    "include_images": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                WebSearchResult(
                    url=result["url"],
                    title=result["title"],
                    content=result["content"],
                    score=result.get("score", 0.5),
                    published_date=result.get("published_date"),
                    domain=self._extract_domain(result["url"]),
                )
                for result in data.get("results", [])
            ]


class DuckDuckGoSearch:
    """DuckDuckGo fallback provider - no API key required."""
    
    BASE_URL = "https://api.duckduckgo.com/"
    
    async def search(
        self, 
        query: str, 
        num_results: int = 10
    ) -> list[WebSearchResult]:
        """Execute web search via DuckDuckGo Instant Answer API."""
        from urllib.parse import quote
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.BASE_URL}{quote(query)}",
                params={
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1",
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for topic in data.get("RelatedTopics", [])[:num_results]:
                if "Text" in topic and "FirstURL" in topic:
                    results.append(WebSearchResult(
                        url=topic["FirstURL"],
                        title=data.get("Heading", query),
                        content=topic["Text"],
                        score=0.5,  # No relevance score from DDG
                        published_date=None,
                        domain=self._extract_domain(topic["FirstURL"]),
                    ))
            
            return results


QUERY_EXPANSION_PROMPT = """Given this research query and the existing context, generate an optimized web search query.

Query: {query}

Existing context summary:
{existing_context}

Generate a search query that:
- Incorporates key terms from both query and context
- Uses precise terminology (not vague)
- Is suitable for web search (not too broad or narrow)
- Maximum 20 words

Return only the search query, nothing else."""


class WebFallbackExecutor:
    """Orchestrates web fallback with query expansion and deduplication."""
    
    def __init__(
        self,
        primary_provider: WebSearchProvider,
        fallback_provider: WebSearchProvider | None = None,
    ):
        self.primary = primary_provider
        self.fallback = fallback_provider
    
    async def execute(
        self,
        query: str,
        existing_context: str = "",
        existing_doc_ids: set[str] | None = None,
        max_results: int = 10,
    ) -> WebFallbackResult:
        """
        Execute web fallback search with query expansion.
        
        Steps:
        1. Expand query using existing context
        2. Execute web search
        3. Filter blocked domains
        4. Format results
        """
        # Step 1: Query expansion
        expanded_query = await self._expand_query(query, existing_context)
        
        # Step 2: Execute search (with fallback provider)
        web_results = []
        try:
            web_results = await self.primary.search(expanded_query, max_results)
        except Exception as primary_error:
            if self.fallback:
                web_results = await self.fallback.search(expanded_query, max_results)
            else:
                raise WebSearchError(f"Primary search failed: {primary_error}")
        
        # Step 3: Filter blocked domains
        domains_excluded = []
        filtered_results = []
        for result in web_results:
            if any(blocked in result.domain for blocked in TavilyWebSearch.BLOCKED_DOMAINS):
                domains_excluded.append(result.domain)
            else:
                filtered_results.append(result)
        
        # Step 4: Format results
        web_documents = [
            {
                "id": f"web_{i}",
                "content": r.content,
                "metadata": {
                    "source": "web",
                    "url": r.url,
                    "title": r.title,
                    "score": r.score,
                    "published_date": r.published_date,
                    "domain": r.domain,
                },
            }
            for i, r in enumerate(filtered_results)
        ]
        
        return WebFallbackResult(
            web_documents=filtered_results,
            merged_documents=web_documents,
            search_query_used=expanded_query,
            domains_included=list(set(r.domain for r in filtered_results)),
            domains_excluded=domains_excluded,
        )
    
    async def _expand_query(
        self, 
        query: str, 
        context: str
    ) -> str:
        """Generate expanded search query using LLM."""
        prompt = QUERY_EXPANSION_PROMPT.format(
            query=query,
            existing_context=context[:1000]
        )
        
        response = await llm_client.chat.completions.create(
            model="openrouter/meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.0,
        )
        
        return response.choices[0].message.content.strip()
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        return urlparse(url).netloc
```

#### 4.1.4 CRAG Configuration

```python
# app/config.py - CRAG Settings

from pydantic_settings import BaseSettings


class CRAGSettings(BaseSettings):
    """Corrective-RAG configuration."""
    
    # Enable/disable CRAG
    crag_enabled: bool = True
    
    # Thresholds
    relevance_threshold: float = 0.7    # RELEVANT cutoff
    partial_threshold: float = 0.4       # PARTIAL cutoff  
    fallback_threshold: float = 0.5     # % docs needed to avoid fallback
    
    # Web fallback
    use_web_fallback: bool = True
    web_search_provider: str = "tavily"  # "tavily" | "duckduckgo"
    max_web_results: int = 10
    
    # Model selection
    grading_model: str = "openrouter/meta-llama/llama-3-8b-instruct"
    grading_temperature: float = 0.1
    
    # Caching
    cache_web_results: bool = True
    web_cache_ttl_seconds: int = 3600  # 1 hour
    
    class Config:
        env_prefix = "CRAG_"


class Settings(BaseSettings):
    # ... existing settings ...
    crag: CRAGSettings = CRAGSettings()
```

#### 4.1.5 CRAG LangGraph Integration

```python
# app/agents/graph.py - CRAG Nodes

from langgraph.graph import StateGraph, END
from typing import Literal


def add_crag_nodes(graph: StateGraph) -> StateGraph:
    """Add CRAG nodes to the existing LangGraph workflow."""
    
    # Add nodes
    graph.add_node("grade_retrieval", grade_retrieval_node)
    graph.add_node("web_fallback", web_fallback_node)
    graph.add_node("merge_results", merge_results_node)
    
    # CRAG routing logic
    def crag_router(state: AgentState) -> Literal["rerank", "web_fallback"]:
        """
        Route after CRAG grading:
        - If >50% docs relevant: continue to reranking
        - If <50% docs relevant: trigger web fallback
        """
        grades = state.get("doc_grades", [])
        if not grades:
            return "rerank"
        
        usable = sum(
            1 for g in grades 
            if g.grade in ("relevant", "partial")
        )
        ratio = usable / len(grades)
        
        if ratio >= settings.crag.fallback_threshold:
            return "rerank"
        else:
            state["web_fallback_triggered"] = True
            return "web_fallback"
    
    # Update edges: grade_docs -> CRAG routing
    graph.add_conditional_edges(
        "grade_docs",
        crag_router,
        {
            "rerank": "rerank",
            "web_fallback": "web_fallback",
        }
    )
    
    # Web fallback path
    graph.add_edge("web_fallback", "merge_results")
    graph.add_edge("merge_results", "rerank")
    
    return graph


async def grade_retrieval_node(state: AgentState) -> AgentState:
    """CRAG grading node."""
    query = state["query"]
    retrieved_docs = state.get("retrieved_docs", [])
    
    # Grade documents
    result = await grade_retrieval(
        documents=retrieved_docs,
        query=query,
        threshold=settings.crag.fallback_threshold,
    )
    
    # Update state
    state["doc_grades"] = [
        {
            "doc_id": g.doc_id,
            "score": g.score,
            "grade": g.grade,
            "reasoning": g.reasoning,
            "source": g.source,
        }
        for g in result.graded_documents
    ]
    state["crag_consensus"] = result.consensus_score
    
    return state


async def web_fallback_node(state: AgentState) -> AgentState:
    """Web fallback node - search external sources."""
    query = state["query"]
    existing_context = state.get("merged_context", "")
    
    # Execute web fallback
    result = await web_fallback_executor.execute(
        query=query,
        existing_context=existing_context,
    )
    
    # Add web documents to state
    state["web_documents"] = result.merged_documents
    state["web_search_query"] = result.search_query_used
    state["web_domains"] = result.domains_included
    
    return state


async def merge_results_node(state: AgentState) -> AgentState:
    """Merge local and web documents with re-scoring."""
    local_docs = state.get("retrieved_docs", [])
    web_docs = state.get("web_documents", [])
    
    # Combine and deduplicate
    all_docs = {doc["id"]: doc for doc in local_docs}
    for doc in web_docs:
        if doc["id"] not in all_docs:
            all_docs[doc["id"]] = doc
    
    # Re-score combined set
    combined_docs = list(all_docs.values())
    result = await grade_retrieval(
        documents=combined_docs,
        query=state["query"],
    )
    
    # Apply weighting: local × 1.2, web × 0.8
    for graded in result.graded_documents:
        if graded.source == "local":
            graded.score = min(1.0, graded.score * 1.2)
        else:
            graded.score *= 0.8
    
    state["merged_documents"] = combined_docs
    state["doc_grades"] = [
        {
            "doc_id": g.doc_id,
            "score": g.score,
            "grade": g.grade,
            "source": g.source,
        }
        for g in result.graded_documents
    ]
    
    return state
```

---

### 4.2 Temporal Memory System

**Research Background**: Time-aware retrieval using timestamp embeddings and temporal filters (TimeR4 + EM-LLM research).

**Key Capabilities**:
- Encode temporal information into embeddings
- Filter documents by time ranges
- Apply recency weighting
- Answer temporal questions ("what did I conclude last month?")

#### 4.2.1 Temporal Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TEMPORAL MEMORY SYSTEM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEMPORAL EMBEDDING PIPELINE:                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │ Semantic Embed  │     │ Temporal Encode │     │ Combine Vectors│          │
│  │ (Jina/Voyage)  │────▶│  (Sinusoidal)   │────▶│  (Weighted Sum) │          │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘          │
│         │                       │                        │                   │
│         ▼                       ▼                        ▼                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Combined Memory Embedding (semantic + temporal)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  TEMPORAL QUERY DECOMPOSITION:                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  User Query: "What did I conclude about transformers last quarter?"          │
│                    │                                                        │
│                    ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LLM-based Temporal Parser                                          │   │
│  │  - has_temporal: true                                               │   │
│  │  - time_range: (2024-10-01, 2024-12-31)                           │   │
│  │  - recency_weight: 0.5                                              │   │
│  │  - granularity: "quarter"                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  TIME-AWARE RETRIEVAL:                                                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Combined Score = α × Semantic + (1-α) × Temporal                  │   │
│  │                                                                      │   │
│  │  Where α = f(temporal_specificity):                                │   │
│  │    - Explicit time range (e.g., "in March 2024"): α = 0.3          │   │
│  │    - Relative time (e.g., "recently"): α = 0.7                    │   │
│  │    - No temporal intent: α = 1.0 (semantic only)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.2.2 Timestamp Embedding Strategy

```python
# app/memory/temporal_embeddings.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import numpy as np


@dataclass
class TemporalEmbedding:
    """Dual embedding combining semantic and temporal vectors."""
    semantic_vector: np.ndarray      # Standard semantic embedding
    temporal_vector: np.ndarray        # Time-specific encoding
    timestamp: datetime                # Document capture time
    decay_weight: float               # Recency-based weight
    metadata: dict                    # Additional temporal features


class TemporalEncoder:
    """
    Encodes temporal information using sinusoidal positional encoding.
    
    Similar to transformer attention positional encoding, but adapted for
    1D temporal sequences with support for:
    - Absolute position (days since epoch)
    - Cyclical patterns (day of week, month, year)
    - Relative recency
    """
    
    # Time granularity buckets for cyclical encoding
    TIME_BUCKETS = [
        (timedelta(hours=1), "hour"),
        (timedelta(days=1), "day"),
        (timedelta(weeks=1), "week"),
        (timedelta(days=30), "month"),
        (timedelta(days=365), "year"),
    ]
    
    VECTOR_DIM = 64  # Temporal vector dimension
    
    # Reference epoch for absolute encoding
    EPOCH = datetime(2020, 1, 1)
    
    def __init__(self, reference_date: datetime | None = None):
        self.reference_date = reference_date or datetime.utcnow()
        self.frequencies = [
            2 * np.pi / bucket.total_seconds()
            for bucket, _ in self.TIME_BUCKETS
            for _ in range(2)  # sin and cos for each frequency
        ]
    
    def encode(self, timestamp: datetime) -> np.ndarray:
        """
        Encode a timestamp into a fixed-dimensional vector.
        
        Uses sinusoidal encoding with multiple frequencies to capture
        different time scales.
        """
        # Absolute time offset from reference
        time_diff = max(0, (timestamp - self.reference_date).total_seconds())
        
        vector = np.zeros(self.VECTOR_DIM)
        for i in range(self.VECTOR_DIM):
            freq_idx = i % len(self.frequencies)
            # Decay amplitude with frequency (higher freq = lower amplitude)
            amplitude = 1.0 / (1 + i // len(self.frequencies))
            vector[i] = amplitude * np.sin(
                self.frequencies[freq_idx] * time_diff / (i + 1)
            )
        
        return vector
    
    def encode_relative(
        self,
        doc_timestamp: datetime,
        query_timestamp: datetime,
    ) -> np.ndarray:
        """
        Encode relative time difference for queries like 
        "documents from the last month".
        """
        # Relative offset from query time
        time_diff = (query_timestamp - doc_timestamp).total_seconds()
        
        # Compress large differences (logarithmic)
        compressed_diff = np.sign(time_diff) * np.log1p(abs(time_diff))
        
        vector = np.zeros(self.VECTOR_DIM)
        for i in range(self.VECTOR_DIM):
            freq_idx = i % len(self.frequencies)
            vector[i] = np.cos(
                self.frequencies[freq_idx] * compressed_diff / (i + 1)
            )
        
        return vector
    
    def encode_cyclical(
        self,
        timestamp: datetime,
    ) -> np.ndarray:
        """
        Encode cyclical patterns in time (day of week, month, etc.).
        """
        features = []
        
        # Day of week (0-6)
        dow = timestamp.weekday()
        features.extend(self._periodic(dow, 7))
        
        # Day of year (0-365)
        doy = timestamp.timetuple().tm_yday
        features.extend(self._periodic(doy, 365))
        
        # Month (1-12)
        month = timestamp.month
        features.extend(self._periodic(month, 12))
        
        # Hour of day (0-23)
        hour = timestamp.hour
        features.extend(self._periodic(hour, 24))
        
        return np.array(features)
    
    @staticmethod
    def _periodic(value: float, period: float) -> list[float]:
        """Generate sin/cos pair for cyclical encoding."""
        normalized = 2 * np.pi * value / period
        return [np.sin(normalized), np.cos(normalized)]


class TemporalEmbedder:
    """
    Combines semantic and temporal embeddings for time-aware retrieval.
    
    Two embedding modes:
    1. Sequential: semantic then temporal (used for indexing)
    2. Relative: encode doc-query time difference (used for retrieval)
    """
    
    def __init__(
        self,
        base_embedder: Embedder,
        temporal_encoder: TemporalEncoder | None = None,
        temporal_weight: float = 0.3,
    ):
        self.base_embedder = base_embedder
        self.temporal_encoder = temporal_encoder or TemporalEncoder()
        self.temporal_weight = temporal_weight
    
    async def embed_with_time(
        self,
        content: str,
        timestamp: datetime,
    ) -> TemporalEmbedding:
        """
        Generate combined semantic + temporal embedding.
        
        Args:
            content: Text content to embed
            timestamp: Document capture timestamp
        
        Returns:
            TemporalEmbedding with combined vectors
        """
        # Semantic embedding
        semantic = await self.base_embedder.embed(content)
        
        # Temporal encoding
        temporal = self.temporal_encoder.encode(timestamp)
        
        # Compute recency weight (exponential decay)
        days_old = (datetime.utcnow() - timestamp).days
        decay_weight = 0.5 ** (days_old / 90)  # 90-day half-life
        
        return TemporalEmbedding(
            semantic_vector=semantic,
            temporal_vector=temporal,
            timestamp=timestamp,
            decay_weight=decay_weight,
            metadata={
                "days_old": days_old,
                "recency_score": decay_weight,
            }
        )
    
    def combine_vectors(
        self,
        semantic: np.ndarray,
        temporal: np.ndarray,
        recency_weight: float,
        temporal_alpha: float = 0.3,
    ) -> np.ndarray:
        """
        Combine semantic and temporal vectors with recency weighting.
        
        Score = (1 - α) × semantic + α × temporal × recency_weight
        
        Where α varies based on temporal query specificity:
        - Explicit range: α = 0.4 (temporal matters more)
        - Relative time: α = 0.2 (semantic matters more)
        - No temporal: α = 0.0 (semantic only)
        """
        combined = (
            (1 - temporal_alpha) * semantic +
            temporal_alpha * temporal * recency_weight
        )
        return combined / np.linalg.norm(combined)  # Normalize


# Backfill utility for existing memories
async def backfill_temporal_embeddings(
    db: AsyncSession,
    batch_size: int = 100,
):
    """Backfill temporal embeddings for existing memories."""
    embedder = TemporalEmbedder(base_embedder=DefaultEmbedder())
    
    while True:
        # Fetch batch of memories without temporal vectors
        result = await db.execute(
            select(Memory)
            .where(Memory.temporal_vector_id.is_(None))
            .limit(batch_size)
        )
        memories = result.scalars().all()
        
        if not memories:
            break
        
        for memory in memories:
            # Generate temporal embedding
            embedding = await embedder.embed_with_time(
                content=memory.content,
                timestamp=memory.captured_at,
            )
            
            # Store temporal vector (compressed)
            temporal_vec = TemporalVector(
                memory_id=memory.id,
                vector_id="temporal",
                vector=np.clip(embedding.temporal_vector, -10, 10).astype(np.float16).tobytes(),
                decay_weight=embedding.decay_weight,
            )
            db.add(temporal_vec)
            
            # Update memory reference
            memory.temporal_vector_id = temporal_vec.id
        
        await db.commit()
```

#### 4.2.3 Time-Aware Retrieval

```python
# app/retrieval/temporal_retriever.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import numpy as np


class TemporalFilter(str, Enum):
    """Temporal retrieval modes."""
    ALL = "all"              # No temporal filtering
    RECENT = "recent"        # Within N days
    BEFORE = "before"        # Before specific date
    AFTER = "after"          # After specific date
    BETWEEN = "between"      # Within date range
    RELATIVE = "relative"   # Relative to query time


@dataclass
class TemporalQuery:
    """Query with temporal constraints."""
    text: str
    mode: TemporalFilter = TemporalFilter.ALL
    days: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    query_time: Optional[datetime] = None
    decay_half_life_days: float = 90.0
    temporal_alpha: float = 0.3  # Weight of temporal vs semantic


@dataclass
class TemporalRetrievalResult:
    """Result with temporal scoring."""
    documents: list[dict]
    temporal_scores: list[float]
    semantic_scores: list[float]
    combined_scores: list[float]
    time_weights: list[float]
    metadata: dict


class TemporalRetriever:
    """
    Time-aware retrieval combining semantic similarity with temporal relevance.
    
    Score calculation:
        combined = α × semantic + (1-α) × temporal × recency_weight
    
    Where α is determined by query's temporal specificity.
    """
    
    def __init__(
        self,
        vector_store: ChromaDBClient,
        temporal_encoder: TemporalEncoder,
        embedder: TemporalEmbedder,
    ):
        self.vector_store = vector_store
        self.temporal_encoder = temporal_encoder
        self.embedder = embedder
    
    async def retrieve(
        self,
        query: TemporalQuery,
        query_embedding: np.ndarray,
        top_k: int = 50,
    ) -> TemporalRetrievalResult:
        """
        Execute time-aware retrieval.
        
        Steps:
        1. Get semantic search results (oversample for filtering)
        2. Compute temporal scores for each result
        3. Combine semantic + temporal
        4. Return ranked results
        """
        # Step 1: Semantic search (oversample)
        raw_results = await self.vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k * 2,
            include=["documents", "metadatas", "distances"],
        )
        
        # Step 2: Compute scores
        documents = []
        temporal_scores = []
        semantic_scores = []
        time_weights = []
        
        query_time = query.query_time or datetime.utcnow()
        
        for i, doc in enumerate(raw_results["documents"]):
            metadata = raw_results["metadatas"][i]
            doc_time = self._parse_timestamp(metadata.get("timestamp"))
            
            # Apply temporal filter
            if not self._passes_filter(doc_time, query):
                continue
            
            # Compute temporal score
            temporal_score = self._compute_temporal_score(
                doc_time, query_time, query
            )
            
            # Compute recency weight (exponential decay)
            time_weight = self._compute_recency_weight(
                doc_time, query_time, query.decay_half_life_days
            )
            
            # Semantic score (invert distance)
            semantic_score = 1 - raw_results["distances"][i]
            
            documents.append({
                "id": raw_results["ids"][i],
                "content": doc,
                "metadata": metadata,
                "semantic_distance": raw_results["distances"][i],
            })
            temporal_scores.append(temporal_score)
            semantic_scores.append(semantic_score)
            time_weights.append(time_weight)
        
        # Step 3: Combine scores
        combined_scores = [
            self._combine_score(
                sem, temp, weight, query.temporal_alpha
            )
            for sem, temp, weight in zip(semantic_scores, temporal_scores, time_weights)
        ]
        
        # Step 4: Rank and return top-k
        ranked_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        return TemporalRetrievalResult(
            documents=[documents[i] for i in ranked_indices],
            temporal_scores=[temporal_scores[i] for i in ranked_indices],
            semantic_scores=[semantic_scores[i] for i in ranked_indices],
            combined_scores=[combined_scores[i] for i in ranked_indices],
            time_weights=[time_weights[i] for i in ranked_indices],
            metadata={
                "temporal_mode": query.mode,
                "total_candidates": len(raw_results["documents"]),
                "post_filter_count": len(documents),
                "query_time_range": (
                    query.start_date.isoformat() if query.start_date else None,
                    query.end_date.isoformat() if query.end_date else None,
                ),
            }
        )
    
    def _combine_score(
        self,
        semantic: float,
        temporal: float,
        recency_weight: float,
        alpha: float,
    ) -> float:
        """
        Combine semantic and temporal scores.
        
        combined = (1-α) × semantic + α × temporal × recency_weight
        """
        temporal_component = temporal * recency_weight
        return (1 - alpha) * semantic + alpha * temporal_component
    
    def _compute_temporal_score(
        self,
        doc_time: datetime,
        query_time: datetime,
        query: TemporalQuery,
    ) -> float:
        """
        Compute temporal relevance score.
        
        Different scoring strategies based on query mode.
        """
        if query.mode == TemporalFilter.ALL:
            return 1.0
        
        elif query.mode == TemporalFilter.RECENT:
            age = (query_time - doc_time).days
            threshold = query.days or 30
            return max(0.0, 1.0 - (age / threshold))
        
        elif query.mode == TemporalFilter.BEFORE:
            return 1.0 if doc_time < (query.end_date or datetime.max) else 0.0
        
        elif query.mode == TemporalFilter.AFTER:
            return 1.0 if doc_time > (query.start_date or datetime.min) else 0.0
        
        elif query.mode == TemporalFilter.BETWEEN:
            start = query.start_date or datetime.min
            end = query.end_date or datetime.max
            if start <= doc_time <= end:
                # Bonus for being near range center
                range_center = start + (end - start) / 2
                distance = abs((doc_time - range_center).days)
                max_distance = (end - start).days / 2
                return 1.0 - (distance / max_distance if max_distance > 0 else 0)
            return 0.0
        
        elif query.mode == TemporalFilter.RELATIVE:
            # Use temporal encoder for similarity
            doc_vec = self.temporal_encoder.encode_relative(doc_time, query_time)
            query_vec = self.temporal_encoder.encode_relative(doc_time, query_time)
            return float(np.dot(doc_vec, query_vec))
        
        return 0.5  # Default neutral
    
    def _compute_recency_weight(
        self,
        doc_time: datetime,
        query_time: datetime,
        half_life_days: float,
    ) -> float:
        """
        Compute recency weight using exponential decay.
        
        weight = 0.5^(days_old / half_life)
        """
        days_old = (query_time - doc_time).days
        return 0.5 ** (days_old / half_life_days)
    
    def _passes_filter(
        self,
        doc_time: datetime | None,
        query: TemporalQuery,
    ) -> bool:
        """Check if document passes temporal filter."""
        if query.mode == TemporalFilter.ALL:
            return True
        if doc_time is None:
            return query.mode == TemporalFilter.ALL
        return True  # Further filtering done in score computation
    
    @staticmethod
    def _parse_timestamp(value: str | datetime | None) -> datetime | None:
        """Parse timestamp from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
```

#### 4.2.4 Temporal Query Decomposition

```python
# app/agents/temporal_query_agent.py

"""
Temporal query patterns and their decomposition:

Natural Language → Temporal Query Parameters

Patterns:
  - "last week" / "recently" → mode: RECENT, days: 7
  - "in March 2024" → mode: BETWEEN, start: 2024-03-01, end: 2024-03-31
  - "about a month ago" → mode: RECENT, days: 30-45
  - "before 2023" → mode: BEFORE, end: 2023-01-01
  - "during my time at X" → extract date range from KG entity
  - "Q3 2024" → mode: BETWEEN, start: 2024-07-01, end: 2024-09-30
"""


TEMPORAL_DECOMPOSE_PROMPT = """Extract temporal intent from this research query.

Query: {query}

Analyze the query for:
1. Explicit date ranges mentioned (e.g., "in March 2024")
2. Relative time references (e.g., "last week", "recently", "a month ago")
3. Implicit time constraints from context
4. Temporal keywords that suggest recency importance

Respond with JSON:
{{
    "has_temporal_intent": true/false,
    "temporal_keywords_found": ["list of time-related words"],
    "mode": "all" | "recent" | "before" | "after" | "between" | "relative",
    "days": number (for "recent" mode),
    "start_date": "YYYY-MM-DD" | null,
    "end_date": "YYYY-MM-DD" | null,
    "confidence": 0.0-1.0,
    "interpretation": "natural language interpretation",
    "needs_kg_lookup": true/false,
    "kg_entity_hint": "person/project name" | null
}}

Examples:
- "What did I read last week about transformers?"
  → {{"mode": "recent", "days": 7, "confidence": 0.95}}

- "Research on attention from before 2023"
  → {{"mode": "before", "end_date": "2023-01-01", "confidence": 0.9}}

- "Papers published in Q3 2024 about RLHF"
  → {{"mode": "between", "start_date": "2024-07-01", "end_date": "2024-09-30", "confidence": 0.95}}

- "My conclusions about the project"
  → {{"has_temporal_intent": false, "mode": "all", "confidence": 0.5}}
"""


# Regex patterns for fast-path extraction
TEMPORAL_PATTERNS = [
    # Relative patterns
    (r"\blast week\b", TemporalFilter.RECENT, {"days": 7}),
    (r"\blast month\b", TemporalFilter.RECENT, {"days": 30}),
    (r"\bthis week\b", TemporalFilter.RECENT, {"days": 7}),
    (r"\bthis month\b", TemporalFilter.RECENT, {"days": 30}),
    (r"\brecently\b", TemporalFilter.RECENT, {"days": 14}),
    (r"\bpast \d+ days?\b", None, None),  # Extract number
    (r"\blast \d+ days?\b", None, None),  # Extract number
    (r"\byesterday\b", TemporalFilter.RECENT, {"days": 1}),
    (r"\btoday\b", TemporalFilter.RECENT, {"days": 0}),
    
    # Quarter patterns
    (r"\bq([1-4])\s+(\d{4})\b", TemporalFilter.BETWEEN, None),  # Q1 2024
    
    # Month patterns
    (r"\bin\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b", 
     TemporalFilter.BETWEEN, None),
    
    # Year patterns
    (r"\bin\s+(\d{4})\b", TemporalFilter.BETWEEN, None),
    
    # Range patterns
    (r"\bbefore\s+(\d{4})\b", TemporalFilter.BEFORE, None),
    (r"\bafter\s+(\d{4})\b", TemporalFilter.AFTER, None),
    (r"\bbetween\s+(\d{4})\s+and\s+(\d{4})\b", TemporalFilter.BETWEEN, None),
]

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}


class TemporalQueryDecomposer:
    """
    Decomposes natural language queries into temporal parameters.
    
    Uses two-stage approach:
    1. Fast regex patterns for common queries
    2. LLM for complex/ambiguous queries
    """
    
    def __init__(
        self,
        llm_client: AsyncLLMClient,
        kg_client: KnowledgeGraphClient | None = None,
    ):
        self.llm = llm_client
        self.kg = kg_client
    
    async def decompose(self, query: str) -> TemporalQuery:
        """
        Decompose query into temporal parameters.
        
        Attempts fast regex extraction first, falls back to LLM
        for complex queries.
        """
        # Try fast pattern matching first
        fast_result = self._try_fast_extract(query)
        if fast_result and fast_result.confidence > 0.8:
            return fast_result
        
        # Fall back to LLM decomposition
        return await self._llm_decompose(query)
    
    def _try_fast_extract(self, query: str) -> TemporalQuery | None:
        """Fast pattern-based temporal extraction."""
        query_lower = query.lower()
        
        for pattern, default_mode, default_params in TEMPORAL_PATTERNS:
            match = re.search(pattern, query_lower)
            if not match:
                continue
            
            # Parse relative patterns
            if "week" in match.group(0):
                return TemporalQuery(
                    text=self._remove_temporal_words(query),
                    mode=TemporalFilter.RECENT,
                    days=7,
                    decay_half_life_days=90.0,
                    temporal_alpha=0.3,
                )
            
            if "month" in match.group(0) and "last" in match.group(0):
                return TemporalQuery(
                    text=self._remove_temporal_words(query),
                    mode=TemporalFilter.RECENT,
                    days=30,
                    decay_half_life_days=90.0,
                    temporal_alpha=0.3,
                )
            
            if "recently" in match.group(0):
                return TemporalQuery(
                    text=self._remove_temporal_words(query),
                    mode=TemporalFilter.RECENT,
                    days=14,
                    decay_half_life_days=90.0,
                    temporal_alpha=0.2,
                )
            
            # Parse quarter patterns
            if match := re.search(r"q([1-4])\s+(\d{4})", query_lower):
                q = int(match.group(1))
                year = int(match.group(2))
                quarter_start = datetime(year, (q - 1) * 3 + 1, 1)
                if q < 4:
                    quarter_end = datetime(year, q * 3 + 1, 1) - timedelta(days=1)
                else:
                    quarter_end = datetime(year + 1, 1, 1) - timedelta(days=1)
                
                return TemporalQuery(
                    text=self._remove_temporal_words(query),
                    mode=TemporalFilter.BETWEEN,
                    start_date=quarter_start,
                    end_date=quarter_end,
                    decay_half_life_days=90.0,
                    temporal_alpha=0.4,  # Higher weight for explicit ranges
                )
            
            # Parse month patterns
            if match := re.search(
                r"in\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
                query_lower
            ):
                month = MONTH_MAP[match.group(1)]
                year = int(match.group(2))
                start = datetime(year, month, 1)
                if month < 12:
                    end = datetime(year, month + 1, 1) - timedelta(days=1)
                else:
                    end = datetime(year + 1, 1, 1) - timedelta(days=1)
                
                return TemporalQuery(
                    text=self._remove_temporal_words(query),
                    mode=TemporalFilter.BETWEEN,
                    start_date=start,
                    end_date=end,
                    decay_half_life_days=90.0,
                    temporal_alpha=0.4,
                )
            
            # Parse year patterns
            if match := re.search(r"\b(20\d{2})\b", query_lower):
                year = int(match.group(1))
                return TemporalQuery(
                    text=self._remove_temporal_words(query),
                    mode=TemporalFilter.BETWEEN,
                    start_date=datetime(year, 1, 1),
                    end_date=datetime(year, 12, 31),
                    decay_half_life_days=90.0,
                    temporal_alpha=0.3,
                )
        
        # No temporal pattern found
        return None
    
    async def _llm_decompose(self, query: str) -> TemporalQuery:
        """Use LLM for complex temporal decomposition."""
        prompt = TEMPORAL_DECOMPOSE_PROMPT.format(query=query)
        
        response = await self.llm.chat.completions.create(
            model="openrouter/meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Parse result
        mode = TemporalFilter(result.get("mode", "all"))
        
        # Extract dates
        start_date = None
        end_date = None
        days = None
        
        if result.get("start_date"):
            try:
                start_date = datetime.fromisoformat(result["start_date"])
            except ValueError:
                pass
        
        if result.get("end_date"):
            try:
                end_date = datetime.fromisoformat(result["end_date"])
            except ValueError:
                pass
        
        if result.get("days"):
            days = int(result["days"])
        
        # Determine temporal alpha based on mode
        alpha = self._alpha_for_mode(mode, result.get("confidence", 0.5))
        
        return TemporalQuery(
            text=query,  # Keep original text for semantic search
            mode=mode,
            days=days,
            start_date=start_date,
            end_date=end_date,
            query_time=datetime.utcnow(),
            decay_half_life_days=90.0,
            temporal_alpha=alpha,
        )
    
    def _alpha_for_mode(self, mode: TemporalFilter, confidence: float) -> float:
        """Determine temporal weight based on query mode."""
        alphas = {
            TemporalFilter.ALL: 0.0,       # Pure semantic
            TemporalFilter.RECENT: 0.2,   # Slight temporal boost
            TemporalFilter.BEFORE: 0.3,
            TemporalFilter.AFTER: 0.3,
            TemporalFilter.BETWEEN: 0.4,  # Explicit range = temporal matters
            TemporalFilter.RELATIVE: 0.3,
        }
        return alphas.get(mode, 0.3) * confidence
    
    @staticmethod
    def _remove_temporal_words(query: str) -> str:
        """Remove temporal keywords from query for semantic search."""
        words_to_remove = [
            r"\blast\s+(week|month|year|quarter)\b",
            r"\bthis\s+(week|month|year|quarter)\b",
            r"\brecently\b",
            r"\byesterday\b",
            r"\btoday\b",
            r"\bQ[1-4]\s+\d{4}\b",
            r"\bin\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b",
            r"\bfrom\s+\d{4}\b",
            r"\bto\s+\d{4}\b",
            r"\bbefore\s+\d{4}\b",
            r"\bafter\s+\d{4}\b",
        ]
        
        result = query.lower()
        for pattern in words_to_remove:
            result = re.sub(pattern, "", result)
        
        return " ".join(result.split())  # Normalize whitespace
```

#### 4.2.5 Storage Schema Changes

**PostgreSQL: Temporal Memory Tables**

```sql
-- Migration: add_temporal_memory_support.sql

-- Add temporal columns to memories table
ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS temporal_vector_id UUID REFERENCES temporal_vectors(id),
    ADD COLUMN IF NOT EXISTS time_weight FLOAT NOT NULL DEFAULT 1.0,
    ADD COLUMN IF NOT EXISTS event_date TIMESTAMPTZ,  -- Explicit event time vs capture time
    ADD COLUMN IF NOT EXISTS access_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ;

-- Add temporal indexes
CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_timestamp ON memories(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_event_date ON memories(user_id, event_date DESC) 
    WHERE event_date IS NOT NULL;

-- Temporal vectors table
CREATE TABLE IF NOT EXISTS temporal_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    vector_id VARCHAR(64) NOT NULL,  -- 'temporal' or 'temporal_relative'
    vector BYTEA NOT NULL,           -- Compressed float16 array
    encoded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decay_weight FLOAT NOT NULL DEFAULT 1.0,
    metadata JSONB NOT NULL DEFAULT '{}',
    UNIQUE(memory_id, vector_id)
);

CREATE INDEX IF NOT EXISTS idx_temporal_vectors_memory ON temporal_vectors(memory_id);
CREATE INDEX IF NOT EXISTS idx_temporal_vectors_encoded ON temporal_vectors(encoded_at);

-- Feedback table for continual learning
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feedback_type VARCHAR(20) NOT NULL,  -- 'thumbs_up', 'thumbs_down', 'correction', 'citation_click'
    rating INTEGER,                       -- 1-5 scale
    time_spent_seconds INTEGER,
    source_clicks INTEGER,
    retrieval_confidence FLOAT,
    answer_quality FLOAT,
    correction_text TEXT,
    extra_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_message FOREIGN KEY (message_id) REFERENCES messages(id),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_message ON user_feedback(user_id, message_id);
CREATE INDEX IF NOT EXISTS idx_feedback_quality ON user_feedback(retrieval_confidence, answer_quality);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON user_feedback(created_at DESC);

-- Evaluation sets table
CREATE TABLE IF NOT EXISTS evaluation_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    feedback_ids UUID[] NOT NULL DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(64) NOT NULL,  -- 'system', 'human_reviewer'
    last_evaluated_at TIMESTAMPTZ,
    metrics JSONB
);

CREATE INDEX IF NOT EXISTS idx_eval_sets_name ON evaluation_sets(name);
CREATE INDEX IF NOT EXISTS idx_eval_sets_created ON evaluation_sets(created_at DESC);
```

**ChromaDB: Temporal Collection Schema**

```python
# app/retrieval/chroma_schema.py

TEMPORAL_COLLECTION_SCHEMA = {
    "name": "memories_temporal",
    "metadata": {
        "description": "Temporal embeddings for time-aware retrieval",
        "version": "1.0",
        "created_at": datetime.utcnow().isoformat(),
    },
    "get_or_create": True,
    "configuration": {
        "hnsw": {
            "space": "cosine",
            "ef_construction": 128,
            "ef": 100,
            "M": 16,
        },
        "quantization": {
            "enabled": True,
            "type": "float16",
        },
    },
}

# Metadata fields for temporal filtering
TEMPORAL_METADATA_FIELDS = {
    "memory_id": "uuid",
    "user_id": "uuid",
    "timestamp": "datetime",        # ISO format string
    "event_date": "datetime",        # Optional explicit event time
    "decay_weight": "float32",       # Pre-computed recency weight
    "access_count": "int32",         # Popularity signal
    "doc_type": "string",            # 'document', 'note', 'email', etc.
    "source": "string",               # 'upload', 'gmail', 'notion', etc.
}

# Composite index for temporal queries
TEMPORAL_INDEX_CONFIG = """
CREATE COLLECTION memories_temporal WITH:
  dimension = 64,           -- Temporal vector dimension
  metric = cosine,         -- Angular distance
  hnsw:space = cosine,     -- HNSW configuration
  hnsw:ef_construction = 128,
  hnsw:ef = 100,
  hnsw:M = 16
"""
```

---

### 4.3 Multi-hop Reasoning

**Research Background**: "EfficientRAG: Efficient Retriever for Multi-Hop QA" - EMNLP 2024

**Key Findings**:
- Multi-hop questions require sequential retrieval and reasoning
- Naive approaches retrieve 200+ chunks but with low efficiency
- Token-level labeler identifies useful tokens in retrieved chunks
- Filter module generates next-hop queries from labeled tokens
- **10x efficiency improvement** (200 chunks → 20 chunks equivalent)

#### 4.3.1 EfficientRAG Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-HOP REASONING (EfficientRAG)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  QUERY: "What is the relationship between transformer architecture          │
│          and the attention mechanism?"                                      │
│                    │                                                        │
│                    ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HOP 1: Initial Retrieval                                            │   │
│  │  Query: "transformer architecture"                                   │   │
│  │  Retrieved: [doc1, doc2, doc3]                                       │   │
│  │  Key entities: ["self-attention", "encoder-decoder", "positional    │   │
│  │                encoding"]                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                    │                                                        │
│                    ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HOP 2: Next-hop Retrieval                                           │   │
│  │  Query: "self-attention mechanism in transformers"                   │   │
│  │  Retrieved: [doc4, doc5, doc6]                                       │   │
│  │  Key entities: ["scaled dot-product", "multi-head", "Q,K,V"]        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                    │                                                        │
│                    ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HOP 3: Final Synthesis                                              │   │
│  │  All evidence combined                                               │   │
│  │  Answer: "Transformers use attention to..."                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  EFFICIENCY COMPARISON:                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Naive RAG:     200 chunks retrieved, 5 LLM calls                         │
│  EfficientRAG:  20 chunks retrieved (token-labeled), 3 LLM calls          │
│                                                                             │
│  Token Labeling extracts only relevant passages before next-hop query       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 EfficientRAG Implementation

```python
# app/agents/multihop_agent.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import asyncio


class HopStatus(str, Enum):
    """Status of a reasoning hop."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    MERGED = "merged"


@dataclass
class Hop:
    """A single retrieval + reasoning hop."""
    hop_id: int
    query: str
    context: str                        # Accumulated context
    retrieved_docs: list[dict] = field(default_factory=list)
    labeled_tokens: list[dict] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    answer_fragment: str = ""
    status: HopStatus = HopStatus.PENDING
    retrieval_score: float = 0.0
    
    @property
    def is_complete(self) -> bool:
        return self.status == HopStatus.COMPLETED


@dataclass
class MultiHopResult:
    """Result from multi-hop reasoning."""
    answer: str
    supporting_evidence: list[dict]
    hop_count: int
    hop_metadata: list[dict]
    confidence: float
    total_docs_retrieved: int
    efficient_mode: bool = True


@dataclass
class TokenSpan:
    """A labeled token span from a document."""
    token: str
    start: int
    end: int
    reason: str
    usefulness_score: float


LABEL_TOKENS_PROMPT = """Given a question and a retrieved document, identify which 
tokens (words or phrases) in the document are MOST USEFUL for finding information 
to answer the question.

Mark tokens that:
1. Are entities (names, dates, concepts)
2. Connect to other potential information sources
3. Suggest related topics for follow-up
4. Contain specific identifiers or references

Ignore tokens that:
- Are purely grammatical
- Don't contribute to information discovery

Question: {question}

Document: {document}

Return JSON:
{{
    "useful_tokens": [
        {{"token": "word", "start": 0, "end": 4, "reason": "why useful", "score": 0.8}},
        ...
    ],
    "next_hop_hints": [
        "suggested follow-up search term 1",
        "suggested follow-up search term 2"
    ],
    "key_finding": "one sentence summarizing the key finding",
    "confidence": 0.0-1.0
}}
"""


GENERATE_NEXT_QUERY_PROMPT = """Based on the original question and what we've found so far, 
generate the next search query to find the remaining information needed.

Original Question: {original_question}

What we've found so far:
{accumulated_findings}

Key entities/terms discovered:
{key_entities}

What information is still missing to fully answer the question?

Generate 1-2 specific search queries (max 15 words each) that would find this information.

Return JSON:
{{
    "next_queries": ["query 1", "query 2"],
    "reasoning": "why these queries are needed",
    "can_answer": true/false  -- True if we have enough info to answer
}}
"""


MERGE_EVIDENCE_PROMPT = """Synthesize findings from multiple research hops into a coherent answer.

Original Question: {question}

Evidence from Hop {n}:
{hop_findings}

Requirements:
1. Organize by theme/finding, not by source
2. Resolve any contradictions between sources
3. Maintain factual accuracy with citations
4. Answer the original question directly

Provide:
1. The synthesized answer
2. Supporting evidence citations
3. Confidence score (0-1)
4. Any remaining uncertainties
"""


class EfficientRAG:
    """
    EfficientRAG implementation for multi-hop reasoning.
    
    Key optimizations:
    1. Token-level labeling (not full document)
    2. Focused next-hop queries
    3. Early termination when answer is complete
    4. Evidence deduplication across hops
    """
    
    MAX_HOPS = 3
    MIN_CONFIDENCE_TO_CONTINUE = 0.7
    TOP_K_PER_HOP = 10
    TOKEN_LABEL_BATCH = 5  # Label top 5 docs per hop
    
    def __init__(
        self,
        retriever: TemporalRetriever,
        llm_client: AsyncLLMClient,
    ):
        self.retriever = retriever
        self.llm = llm_client
    
    async def execute(
        self,
        query: str,
        user_id: str,
        conversation_context: str = "",
        max_hops: int | None = None,
    ) -> MultiHopResult:
        """
        Execute multi-hop reasoning on a query.
        
        Args:
            query: User's question
            user_id: User for retrieval scoping
            conversation_context: Previous conversation for context
            max_hops: Override default max hops
        
        Returns:
            MultiHopResult with answer, evidence, and metadata
        """
        max_hops = max_hops or self.MAX_HOPS
        hops: list[Hop] = []
        accumulated_findings: list[str] = []
        key_entities: set[str] = set()
        
        current_query = query
        accumulated_context = conversation_context
        
        # Multi-hop loop
        for hop_num in range(max_hops):
            hop = Hop(
                hop_id=hop_num,
                query=current_query,
                context=accumulated_context,
            )
            hops.append(hop)
            
            # Execute hop
            await self._execute_hop(hop, user_id)
            
            # Extract findings and entities
            accumulated_findings.extend(hop.key_findings)
            for label in hop.labeled_tokens:
                if label.get("usefulness_score", 0) > 0.5:
                    key_entities.add(label.get("token", ""))
            
            # Update accumulated context
            accumulated_context = self._build_context(hops)
            
            # Check if we can answer or should continue
            if hop_num > 0:
                can_answer = await self._check_can_answer(
                    query, accumulated_findings
                )
                if can_answer:
                    break
                
                # Check confidence
                if hop.retrieval_score > self.MIN_CONFIDENCE_TO_CONTINUE:
                    continue
            
            # Generate next query if not last hop
            if hop_num < max_hops - 1:
                next_query_result = await self._generate_next_query(
                    original=query,
                    accumulated=accumulated_findings,
                    entities=list(key_entities),
                )
                
                if next_query_result.get("can_answer"):
                    break
                
                current_query = next_query_result["next_queries"][0]
        
        # Merge evidence and generate final answer
        final_result = await self._merge_and_answer(query, hops)
        
        return MultiHopResult(
            answer=final_result["answer"],
            supporting_evidence=final_result["evidence"],
            hop_count=len(hops),
            hop_metadata=[self._hop_metadata(h) for h in hops],
            confidence=final_result.get("confidence", 0.5),
            total_docs_retrieved=sum(len(h.retrieved_docs) for h in hops),
            efficient_mode=True,
        )
    
    async def _execute_hop(self, hop: Hop, user_id: str) -> None:
        """Execute a single retrieval + reasoning hop."""
        hop.status = HopStatus.IN_PROGRESS
        
        try:
            # Step 1: Retrieve documents
            temporal_query = TemporalQuery(
                text=hop.query,
                mode=TemporalFilter.ALL,
            )
            query_embedding = await self._embed(hop.query)
            
            results = await self.retriever.retrieve(
                query=temporal_query,
                query_embedding=query_embedding,
                top_k=self.TOP_K_PER_HOP,
            )
            
            hop.retrieved_docs = results.documents
            hop.retrieval_score = max(results.semantic_scores) if results.semantic_scores else 0.0
            
            # Step 2: Token-level labeling (top documents only)
            labeled_tokens = []
            key_findings = []
            
            for doc in hop.retrieved_docs[:self.TOKEN_LABEL_BATCH]:
                label_result = await self._label_tokens(hop.query, doc["content"])
                labeled_tokens.extend(label_result["useful_tokens"])
                if label_result.get("key_finding"):
                    key_findings.append(label_result["key_finding"])
            
            hop.labeled_tokens = labeled_tokens
            hop.key_findings = key_findings
            hop.status = HopStatus.COMPLETED
            
        except Exception as e:
            hop.status = HopStatus.FAILED
            raise
    
    async def _label_tokens(
        self, 
        question: str, 
        document: str
    ) -> dict:
        """Label useful tokens in a document for next-hop retrieval."""
        prompt = LABEL_TOKENS_PROMPT.format(
            question=question,
            document=document[:2000]  # Limit for cost
        )
        
        response = await self.llm.chat.completions.create(
            model="openrouter/meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _generate_next_query(
        self,
        original: str,
        accumulated: list[str],
        entities: list[str],
    ) -> dict:
        """Generate next-hop query based on accumulated findings."""
        prompt = GENERATE_NEXT_QUERY_PROMPT.format(
            original_question=original,
            accumulated_findings="\n".join(f"- {f}" for f in accumulated),
            key_entities=", ".join(entities[:20]),
        )
        
        response = await self.llm.chat.completions.create(
            model="openrouter/meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _check_can_answer(
        self, 
        query: str, 
        findings: list[str]
    ) -> bool:
        """Check if accumulated findings can answer the query."""
        check_prompt = f"""Based on these findings, can we fully answer the question?

Question: {query}

Findings:
{chr(10).join(f"- {f}" for f in findings)}

Answer: YES if findings directly address the question, NO if more info needed."""
        
        response = await self.llm.chat.completions.create(
            model="openrouter/meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": check_prompt}],
            max_tokens=10,
        )
        
        return "yes" in response.choices[0].message.content.lower()
    
    async def _merge_and_answer(
        self, 
        query: str, 
        hops: list[Hop]
    ) -> dict:
        """Merge evidence from all hops into final answer."""
        # Build findings summary per hop
        hop_findings = []
        all_docs = []
        
        for hop in hops:
            if hop.key_findings:
                summary = f"Hop {hop.hop_id + 1}: " + " ".join(hop.key_findings)
                hop_findings.append(summary)
            all_docs.extend(hop.retrieved_docs)
        
        # Generate answer
        prompt = MERGE_EVIDENCE_PROMPT.format(
            question=query,
            n=len(hops),
            hop_findings="\n\n".join(hop_findings) if hop_findings else "No specific findings.",
        )
        
        response = await self.llm.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Deduplicate evidence
        seen_ids = set()
        unique_evidence = []
        for doc in all_docs:
            if doc["id"] not in seen_ids:
                seen_ids.add(doc["id"])
                unique_evidence.append(doc)
        
        return {
            "answer": result.get("answer", ""),
            "evidence": unique_evidence[:20],  # Top 20 citations
            "confidence": result.get("confidence", 0.5),
        }
    
    def _build_context(self, hops: list[Hop]) -> str:
        """Build accumulated context from completed hops."""
        lines = []
        for hop in hops:
            if hop.key_findings:
                lines.append(f"[Hop {hop.hop_id + 1}] " + " ".join(hop.key_findings))
        return "\n".join(lines) if lines else ""
    
    def _hop_metadata(self, hop: Hop) -> dict:
        """Extract metadata from a hop."""
        return {
            "hop_id": hop.hop_id,
            "query": hop.query,
            "doc_count": len(hop.retrieved_docs),
            "token_count": len(hop.labeled_tokens),
            "finding_count": len(hop.key_findings),
            "retrieval_score": hop.retrieval_score,
            "status": hop.status.value,
        }
    
    async def _embed(self, text: str) -> np.ndarray:
        """Generate embedding for query."""
        # Placeholder - use actual embedder
        return await self.retriever.embedder.base_embedder.embed(text)
```

#### 4.3.3 Branch-Solve-Merge Pattern

```python
# app/agents/branch_solve_merge.py

"""
For questions with parallel sub-questions:

"Compare X and Y's approaches to Z"

Branch-Solve-Merge Pattern:
1. Branch: Decompose into parallel sub-questions
2. Solve: Retrieve for each sub-question independently
3. Merge: Synthesize into unified answer with comparison
"""

@dataclass
class BranchResult:
    """Result from a single parallel branch."""
    branch_id: str
    sub_question: str
    retrieved_context: list[str]
    answer_fragment: str
    confidence: float
    doc_count: int


@dataclass
class CompareResult:
    """Result from comparison query."""
    answer: str
    comparison_structure: dict  # {aspect: {x: ..., y: ...}}
    supporting_evidence: list[dict]
    confidence: float


async def parallel_branch_retrieve(
    sub_questions: list[str],
    retriever: TemporalRetriever,
    max_concurrent: int = 3,
) -> list[BranchResult]:
    """
    Execute multiple retrieval branches in parallel.
    
    For queries like "Compare X and Y", we retrieve for X and Y
    in parallel, then merge the results.
    """
    
    async def retrieve_branch(
        branch_id: str, 
        query: str
    ) -> BranchResult:
        """Retrieve for a single branch."""
        results = await retriever.retrieve(
            query=query,
            top_k=10,
        )
        
        context = [r["content"] for r in results.documents]
        
        return BranchResult(
            branch_id=branch_id,
            sub_question=query,
            retrieved_context=context,
            answer_fragment="",  # Filled by answer agent
            confidence=max(results.semantic_scores) if results.semantic_scores else 0.5,
            doc_count=len(results.documents),
        )
    
    # Semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_retrieve(branch_id: str, query: str):
        async with semaphore:
            return await retrieve_branch(branch_id, query)
    
    tasks = [
        bounded_retrieve(f"branch_{i}", q)
        for i, q in enumerate(sub_questions)
    ]
    
    return await asyncio.gather(*tasks)


COMPARE_MERGE_PROMPT = """You are comparing two entities (X and Y) on multiple aspects.

Original Question: {question}

Findings for X:
{x_findings}

Findings for Y:
{y_findings}

Generate a structured comparison that:
1. Addresses each key aspect mentioned in the question
2. Shows how X and Y differ on each aspect
3. Provides specific evidence from the sources
4. Identifies any similarities

Return JSON:
{{
    "answer": "natural language comparison",
    "comparison": {{
        "aspect_1": {{"x": "...", "y": "...", "comparison": "..."}},
        ...
    }},
    "confidence": 0.0-1.0
}}
"""


class BranchSolveMerge:
    """
    Handles parallel sub-question retrieval and comparison synthesis.
    """
    
    def __init__(self, efficient_rag: EfficientRAG):
        self.rag = efficient_rag
    
    async def execute_comparison(
        self,
        query: str,
        entities: list[str],  # [entity_x, entity_y]
        user_id: str,
    ) -> CompareResult:
        """
        Execute comparison query using branch-solve-merge.
        
        Example: "Compare transformer and RNN architectures"
        → Branch 1: "transformer architecture"
        → Branch 2: "RNN architecture"
        → Merge: Structured comparison
        """
        # Decompose into sub-questions
        sub_questions = [
            f"{entities[0]}",
            f"{entities[1]}",
        ]
        
        # Parallel retrieval
        branches = await parallel_branch_retrieve(
            sub_questions=sub_questions,
            retriever=self.rag.retriever,
        )
        
        # Generate answer fragments per branch
        for branch in branches:
            branch.answer_fragment = await self._generate_fragment(
                branch.sub_question,
                branch.retrieved_context,
            )
        
        # Merge into comparison
        comparison = await self._merge_comparison(
            query=query,
            x_findings=branches[0].retrieved_context,
            y_findings=branches[1].retrieved_context,
        )
        
        return CompareResult(
            answer=comparison["answer"],
            comparison_structure=comparison["comparison"],
            supporting_evidence=[
                *[{"id": b.branch_id, "content": c} 
                  for b in branches for c in b.retrieved_context[:5]]
            ],
            confidence=comparison.get("confidence", 0.5),
        )
    
    async def _generate_fragment(
        self, 
        query: str, 
        context: list[str]
    ) -> str:
        """Generate answer fragment for a sub-question."""
        prompt = f"""Based on these sources, answer the question:

Question: {query}

Sources:
{chr(10).join(f"- {c[:300]}" for c in context[:5])}

Provide a brief answer (2-3 sentences)."""
        
        response = await self.rag.llm.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        
        return response.choices[0].message.content
    
    async def _merge_comparison(
        self,
        query: str,
        x_findings: list[str],
        y_findings: list[str],
    ) -> dict:
        """Merge parallel branch results into comparison."""
        prompt = COMPARE_MERGE_PROMPT.format(
            question=query,
            x_findings="\n".join(f"- {c[:200]}" for c in x_findings[:5]),
            y_findings="\n".join(f"- {c[:200]}" for c in y_findings[:5]),
        )
        
        response = await self.rag.llm.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        return json.loads(response.choices[0].message.content)
```

---

### 4.4 Continual Learning Pipeline

**Research Background**: Pistis-RAG framework for closed-loop retriever improvement

**Key Capabilities**:
- Collect feedback: thumbs up/down, corrections, citation clicks
- Label feedback: hallucination, incomplete, irrelevant, correct
- Weekly curation of evaluation sets
- Active learning: prioritize uncertain predictions
- Retrain reranker on failure cases

#### 4.4.1 Continual Learning Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTINUAL LEARNING PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      FEEDBACK COLLECTION                              │   │
│  │                                                                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │   │
│  │  │ 👍 / 👎   │  │ Correction │  │Citation    │  │  Time on   │       │   │
│  │  │ Feedback  │  │   Text     │  │  Click     │  │   Answer   │       │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │   │
│  │       │                │              │               │              │   │
│  │       └────────────────┴──────────────┴───────────────┘              │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Feedback Store (PostgreSQL)                                   │   │   │
│  │  │  - user_id, message_id, feedback_type, rating, ...             │   │   │
│  │  │  - retrieval_confidence, answer_quality (from CRAG)           │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      EVAL SET CURATION                                │   │
│  │                                                                       │   │
│  │  Weekly Celery Beat Job:                                              │   │
│  │  1. Aggregate feedback from past week                                 │   │
│  │  2. Filter by quality (rating >= 4 for positive, <= 2 for negative)    │   │
│  │  3. Auto-label: thumbs_up → CORRECT, thumbs_down → IRRELEVANT         │   │
│  │  4. Curate eval sets: positive, negative, hard (borderline)          │   │
│  │  5. Store in evaluation_sets table                                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      ACTIVE LEARNING                                  │   │
│  │                                                                       │   │
│  │  Priority = f(uncertainty, frequency, user_trust, recency)            │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐     │   │
│  │  │  SELECT query_id, query_text                                │     │   │
│  │  │  FROM user_feedback                                        │     │   │
│  │  │  WHERE confidence < 0.7                                     │     │   │
│  │  │    AND retrieval_grade < 0.6                                │     │   │
│  │  │  ORDER BY priority_score DESC                               │     │   │
│  │  │  LIMIT 100                                                  │     │   │
│  │  └────────────────────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      RETRIEVER FINE-TUNING                            │   │
│  │                                                                       │   │
│  │  Model: Sentence-transformers (e.g., BAAI/bge-base-en-v1.5)            │   │
│  │  Method: Contrastive learning with hard negatives                     │   │
│  │                                                                       │   │
│  │  Schedule: Weekly batch via Celery Beat                               │   │
│  │  A/B Test: 10% traffic on new model, compare metrics                  │   │
│  │                                                                       │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │   │
│  │  │ Fine-tune   │────▶│  Evaluate   │────▶│  Approve &  │           │   │
│  │  │  Model      │     │  on Eval    │     │  Deploy     │           │   │
│  │  │ (LoRA)     │     │  Set       │     │  (A/B)     │           │   │
│  │  └─────────────┘     └─────────────┘     └─────────────┘           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.4.2 Feedback Collection

```python
# app/models/feedback.py

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import Enum
import uuid


class FeedbackType(str, Enum):
    """Types of user feedback."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    ERROR_REPORT = "error_report"
    CORRECTION = "correction"
    CITATION_CLICK = "citation_click"
    STARRED = "starred"


class FeedbackLabel(str, Enum):
    """Automated labels for feedback."""
    HALLUCINATION = "hallucination"
    INCOMPLETE = "incomplete"
    IRRELEVANT = "irrelevant"
    CORRECT = "correct"
    OUTDATED = "outdated"
    UNCLEAR = "unclear"


class UserFeedback:
    """SQLAlchemy model for user feedback."""
    
    __tablename__ = "user_feedback"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # References
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Feedback type
    feedback_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    
    # Explicit rating (1-5)
    rating: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    
    # Implicit signals
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    source_clicks: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    
    # LLM-assessed quality scores (from CRAG)
    retrieval_confidence: Mapped[float | None] = mapped_column(Float(), nullable=True)
    answer_quality: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Detailed feedback
    user_comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    correction_text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    
    # Automated labeling
    label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    label_confidence: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean(), default=False)
    included_in_eval: Mapped[bool] = mapped_column(Boolean(), default=False)
    eval_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_sets.id"),
        nullable=True
    )
    
    # Metadata
    extra_data: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("now()")
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )
    
    __table_args__ = (
        Index("ix_feedback_user_message", "user_id", "message_id"),
        Index("ix_feedback_quality", "retrieval_confidence", "answer_quality"),
        Index("ix_feedback_created", "created_at"),
        Index("ix_feedback_unprocessed", "processed", "created_at"),
    )


class EvaluationSet:
    """SQLAlchemy model for evaluation sets."""
    
    __tablename__ = "evaluation_sets"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    
    # Set type
    set_type: Mapped[str] = mapped_column(
        String(32),
        server_default="'training'"
    )  # "training", "validation", "test"
    
    # Curated from feedback
    feedback_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID),
        server_default="{}"
    )
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer(), default=1)
    parent_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_sets.id"),
        nullable=True
    )
    
    # Quality metrics
    positive_count: Mapped[int] = mapped_column(Integer(), default=0)
    negative_count: Mapped[int] = mapped_column(Integer(), default=0)
    hard_count: Mapped[int] = mapped_column(Integer(), default=0)
    
    # Evaluation results
    last_evaluated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )
    evaluation_metrics: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )  # {"ndcg@10": 0.85, "mrr": 0.78, ...}
    
    # Model checkpoint
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fine_tuned_from: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("now()")
    )
    created_by: Mapped[str] = mapped_column(
        String(64),
        server_default="'system'"
    )  # "system", "human_reviewer", "user_id"
    
    __table_args__ = (
        Index("ix_eval_sets_name", "name"),
        Index("ix_eval_sets_type", "set_type"),
        Index("ix_eval_sets_created", "created_at"),
    )
```

#### 4.4.3 Feedback Collector Service

```python
# app/services/feedback_collector.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID


@dataclass
class FeedbackData:
    """Input data for feedback collection."""
    message_id: UUID
    user_id: UUID
    feedback_type: FeedbackType
    rating: Optional[int] = None
    time_spent_seconds: Optional[int] = None
    source_clicks: Optional[int] = None
    user_comment: Optional[str] = None
    correction_text: Optional[str] = None
    retrieval_confidence: Optional[float] = None
    answer_quality: Optional[float] = None


@dataclass
class PrioritizedFeedback:
    """Feedback with priority score for active learning."""
    feedback: UserFeedback
    priority_score: float
    uncertainty: float
    frequency: int
    user_trust: float
    recency_score: float


class FeedbackCollector:
    """
    Collects and processes user feedback for continual learning.
    
    Handles:
    - Explicit feedback (thumbs up/down)
    - Implicit signals (time spent, citation clicks)
    - Automated labeling via LLM
    - Integration with evaluation pipeline
    """
    
    def __init__(
        self,
        db: AsyncSession,
        llm_client: AsyncLLMClient,
    ):
        self.db = db
        self.llm = llm_client
    
    async def collect(self, data: FeedbackData) -> UserFeedback:
        """
        Record user feedback.
        
        Steps:
        1. Create feedback record
        2. Auto-label based on feedback type
        3. Queue for evaluation processing
        """
        # Determine label based on feedback type
        label, label_confidence = await self._auto_label(data)
        
        feedback = UserFeedback(
            message_id=data.message_id,
            user_id=data.user_id,
            feedback_type=data.feedback_type.value,
            rating=data.rating,
            time_spent_seconds=data.time_spent_seconds,
            source_clicks=data.source_clicks,
            retrieval_confidence=data.retrieval_confidence,
            answer_quality=data.answer_quality,
            user_comment=data.user_comment,
            correction_text=data.correction_text,
            label=label.value if label else None,
            label_confidence=label_confidence,
        )
        
        self.db.add(feedback)
        await self.db.commit()
        
        # Trigger async processing
        await self._queue_processing(feedback)
        
        return feedback
    
    async def _auto_label(
        self, 
        data: FeedbackData
    ) -> tuple[Optional[FeedbackLabel], Optional[float]]:
        """Attempt automated labeling based on feedback type."""
        
        # Explicit positive = CORRECT
        if data.feedback_type == FeedbackType.THUMBS_UP:
            return FeedbackLabel.CORRECT, 1.0
        
        # Explicit negative
        if data.feedback_type == FeedbackType.THUMBS_DOWN:
            if data.rating and data.rating <= 2:
                # Strong negative
                return FeedbackLabel.IRRELEVANT, 0.9
            elif data.user_comment:
                # Use LLM to classify
                return await self._classify_from_comment(data.user_comment)
            return FeedbackLabel.IRRELEVANT, 0.5
        
        # Error report
        if data.feedback_type == FeedbackType.ERROR_REPORT:
            if self._has_hallucination_markers(data.user_comment):
                return FeedbackLabel.HALLUCINATION, 0.8
            return FeedbackLabel.INCOMPLETE, 0.6
        
        # Correction
        if data.feedback_type == FeedbackType.CORRECTION:
            return FeedbackLabel.OUTDATED, 0.7
        
        return None, None
    
    async def _classify_from_comment(
        self, 
        comment: str
    ) -> tuple[FeedbackLabel, float]:
        """Use LLM to classify feedback from user comment."""
        prompt = f"""Classify this user feedback comment:

Comment: {comment}

Categories:
- hallucination: The answer contains false or made-up information
- irrelevant: The answer doesn't address what was asked
- incomplete: The answer is correct but missing important details
- unclear: The answer is confusing or poorly formatted

Return JSON:
{{
    "label": "hallucination" | "irrelevant" | "incomplete" | "unclear",
    "confidence": 0.0-1.0
}}"""
        
        response = await self.llm.chat.completions.create(
            model="openrouter/meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return FeedbackLabel(result["label"]), result["confidence"]
    
    @staticmethod
    def _has_hallucination_markers(comment: str | None) -> bool:
        """Check for obvious hallucination markers in comment."""
        if not comment:
            return False
        
        markers = [
            "made up", "didn't say", "not in", "fabricated",
            "hallucinated", "wrong", "false", "invented",
        ]
        return any(marker in comment.lower() for marker in markers)
    
    async def _queue_processing(self, feedback: UserFeedback) -> None:
        """Queue feedback for async processing."""
        # In production, this would publish to Celery
        # process_feedback.delay(feedback.id)
        pass


class EvalSetCurator:
    """
    Curates evaluation sets from collected feedback.
    
    Weekly Celery Beat job:
    1. Aggregate recent feedback
    2. Apply quality filters
    3. Create balanced eval sets
    4. Update training pipeline
    """
    
    MIN_POSITIVE_RATING = 4
    MIN_NEGATIVE_RATING = 2
    TIME_WINDOW_DAYS = 7
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def curate_weekly_sets(self) -> tuple[EvaluationSet, EvaluationSet]:
        """
        Curate training and validation sets from past week's feedback.
        
        Returns:
            Tuple of (training_set, validation_set)
        """
        cutoff = datetime.utcnow() - timedelta(days=self.TIME_WINDOW_DAYS)
        
        # Get positive examples
        positive_ids = await self._get_quality_feedback(
            min_rating=self.MIN_POSITIVE_RATING,
            cutoff=cutoff,
            label=FeedbackLabel.CORRECT,
        )
        
        # Get negative examples
        negative_ids = await self._get_quality_feedback(
            max_rating=self.MIN_NEGATIVE_RATING,
            cutoff=cutoff,
            label=FeedbackLabel.IRRELEVANT,
        )
        
        # Get hard examples (borderline confidence)
        hard_ids = await self._get_hard_examples(cutoff)
        
        # Create training set (80% of data)
        training_positive = positive_ids[:int(len(positive_ids) * 0.8)]
        training_negative = negative_ids[:int(len(negative_ids) * 0.8)]
        training_hard = hard_ids[:int(len(hard_ids) * 0.8)]
        
        training_set = EvaluationSet(
            name=f"training_set_{datetime.utcnow().strftime('%Y%m%d')}",
            description="Training set from weekly feedback curation",
            set_type="training",
            feedback_ids=training_positive + training_negative + training_hard,
            positive_count=len(training_positive),
            negative_count=len(training_negative),
            hard_count=len(training_hard),
            created_by="system",
        )
        
        # Create validation set (20% of data)
        val_positive = positive_ids[int(len(positive_ids) * 0.8):]
        val_negative = negative_ids[int(len(negative_ids) * 0.8):]
        val_hard = hard_ids[int(len(hard_ids) * 0.8):]
        
        validation_set = EvaluationSet(
            name=f"validation_set_{datetime.utcnow().strftime('%Y%m%d')}",
            description="Validation set from weekly feedback curation",
            set_type="validation",
            feedback_ids=val_positive + val_negative + val_hard,
            positive_count=len(val_positive),
            negative_count=len(val_negative),
            hard_count=len(val_hard),
            created_by="system",
        )
        
        self.db.add(training_set)
        self.db.add(validation_set)
        await self.db.commit()
        
        return training_set, validation_set
    
    async def _get_quality_feedback(
        self,
        cutoff: datetime,
        min_rating: int | None = None,
        max_rating: int | None = None,
        label: FeedbackLabel | None = None,
    ) -> list[UUID]:
        """Get feedback meeting quality criteria."""
        query = select(UserFeedback).where(
            UserFeedback.created_at >= cutoff,
            UserFeedback.processed == True,
        )
        
        if min_rating:
            query = query.where(UserFeedback.rating >= min_rating)
        if max_rating:
            query = query.where(UserFeedback.rating <= max_rating)
        if label:
            query = query.where(UserFeedback.label == label.value)
        
        result = await self.db.execute(query)
        feedbacks = result.scalars().all()
        
        return [f.id for f in feedbacks]
    
    async def _get_hard_examples(self, cutoff: datetime) -> list[UUID]:
        """Get borderline cases for harder training."""
        query = select(UserFeedback).where(
            UserFeedback.created_at >= cutoff,
            UserFeedback.retrieval_confidence.between(0.4, 0.6),
            UserFeedback.processed == True,
        ).limit(100)
        
        result = await self.db.execute(query)
        feedbacks = result.scalars().all()
        
        return [f.id for f in feedbacks]
```

#### 4.4.4 Active Learning Prioritizer

```python
# app/services/active_learning.py

class ActiveLearningPrioritizer:
    """
    Prioritizes feedback for labeling based on learning potential.
    
    Uses uncertainty sampling to select most informative examples:
    - Low confidence predictions
    - Borderline cases
    - Frequently repeated queries
    """
    
    # Priority weights
    UNCERTAINTY_WEIGHT = 0.4
    FREQUENCY_WEIGHT = 0.3
    TRUST_WEIGHT = 0.2
    RECENCY_WEIGHT = 0.1
    
    def __init__(
        self,
        db: AsyncSession,
        reranker: Reranker,
    ):
        self.db = db
        self.reranker = reranker
    
    async def prioritize(
        self,
        top_k: int = 50,
        min_confidence: float = 0.7,
    ) -> list[PrioritizedFeedback]:
        """
        Rank feedback by learning potential.
        
        Priority = w1×uncertainty + w2×frequency + w3×trust + w4×recency
        
        Args:
            top_k: Number of examples to return
            min_confidence: Only consider below this confidence
        
        Returns:
            List of prioritized feedback items
        """
        # Get unprocessed low-confidence feedback
        query = select(UserFeedback).where(
            UserFeedback.processed == False,
            UserFeedback.retrieval_confidence < min_confidence,
            UserFeedback.label.is_(None),
        )
        
        result = await self.db.execute(query)
        feedbacks = result.scalars().all()
        
        prioritized = []
        
        for feedback in feedbacks:
            # Compute priority components
            uncertainty = await self._compute_uncertainty(feedback)
            frequency = await self._get_frequency(feedback)
            trust = await self._get_user_trust(feedback.user_id)
            recency = self._compute_recency(feedback.created_at)
            
            # Compute overall priority
            priority = (
                self.UNCERTAINTY_WEIGHT * uncertainty +
                self.FREQUENCY_WEIGHT * frequency +
                self.TRUST_WEIGHT * trust +
                self.RECENCY_WEIGHT * recency
            )
            
            prioritized.append(PrioritizedFeedback(
                feedback=feedback,
                priority_score=priority,
                uncertainty=uncertainty,
                frequency=frequency,
                user_trust=trust,
                recency_score=recency,
            ))
        
        # Sort by priority and return top_k
        prioritized.sort(key=lambda x: x.priority_score, reverse=True)
        return prioritized[:top_k]
    
    async def _compute_uncertainty(self, feedback: UserFeedback) -> float:
        """
        Compute prediction uncertainty.
        
        Based on:
        - Reranker score variance across top-k
        - Retrieval confidence spread
        """
        if feedback.retrieval_confidence is None:
            return 0.5
        
        # High uncertainty = low confidence OR borderline
        if feedback.retrieval_confidence < 0.3:
            return 1.0
        elif feedback.retrieval_confidence > 0.7:
            return 0.2
        else:
            # Borderline case = highest uncertainty
            return 1.0 - abs(0.5 - feedback.retrieval_confidence) * 2
    
    async def _get_frequency(self, feedback: UserFeedback) -> float:
        """Count similar queries to measure importance."""
        # In production, would hash query and count occurrences
        # Simplified: just use click count
        return min(1.0, (feedback.source_clicks or 0) / 10)
    
    async def _get_user_trust(self, user_id: UUID) -> float:
        """
        Get trust score for user based on historical accuracy.
        
        Users who consistently give accurate feedback get higher trust.
        """
        query = select(func.count(UserFeedback.id)).where(
            UserFeedback.user_id == user_id,
            UserFeedback.label == FeedbackLabel.CORRECT.value,
        )
        result = await self.db.execute(query)
        correct_count = result.scalar()
        
        query = select(func.count(UserFeedback.id)).where(
            UserFeedback.user_id == user_id,
        )
        result = await self.db.execute(query)
        total_count = result.scalar()
        
        if total_count == 0:
            return 0.5  # New user
        
        return correct_count / total_count
    
    @staticmethod
    def _compute_recency(created_at: datetime) -> float:
        """Compute recency score (newer = higher)."""
        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
        # Exponential decay with 24-hour half-life
        return 0.5 ** (age_hours / 24)
```

---

### 4.5 Confidence Calibration

**Research Background**: Platt scaling / Isotonic regression for calibrated uncertainty

**Key Capabilities**:
- Calibrated confidence scores per claim
- Statistical calibration against eval sets
- 95% confidence intervals
- UI signaling for low-confidence answers

#### 4.5.1 Confidence Calibration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONFIDENCE CALIBRATION SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUTS:                                                                   │
│  ────────                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Retrieval   │  │ Reranker    │  │ CRAG        │  │ Answer      │        │
│  │ Scores     │  │ Scores      │  │ Confidence  │  │ Quality     │        │
│  │ (avg 0.72) │  │ (avg 0.85) │  │ (avg 0.68) │  │ (avg 0.78) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                │              │
│         └────────────────┴────────────────┴────────────────┘              │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   FEATURE ENGINEERING                                 │   │
│  │                                                                       │   │
│  │  features = [                                                         │   │
│  │    retrieval_confidence,      # Mean retrieval score                  │   │
│  │    retrieval_variance,        # Variance in retrieval scores          │   │
│  │    reranker_score,           # Jina reranker score                   │   │
│  │    crag_score,               # CRAG grader confidence               │   │
│  │    evidence_count,            # Number of supporting docs            │   │
│  │    source_diversity,          # Number of unique sources              │   │
│  │    temporal_decay,            # Recency weight                       │   │
│  │  ]                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   CALIBRATION MODELS                                  │   │
│  │                                                                       │   │
│  │  Method 1: Platt Scaling (Logistic Regression)                      │   │
│  │    - Fits sigmoid to predicted vs actual                              │   │
│  │    - Good for well-behaved probability outputs                        │   │
│  │                                                                       │   │
│  │  Method 2: Isotonic Regression (Non-parametric)                      │   │
│  │    - Monotonic piecewise constant                                     │   │
│  │    - Better for non-monotonic relationships                           │   │
│  │                                                                       │   │
│  │  Method 3: Temperature Scaling                                      │   │
│  │    - Single parameter: T (temperature)                                │   │
│  │    - softmax(logits / T)                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   OUTPUTS                                              │   │
│  │                                                                       │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Answer Confidence: 0.82 (CI: 0.78-0.86)                      │   │   │
│  │  │                                                              │   │   │
│  │  │  Per-claim confidences:                                        │   │   │
│  │  │  - "Transformers use attention": 0.91 (CI: 0.87-0.94)          │   │   │
│  │  │  - "Attention was introduced in 2017": 0.76 (CI: 0.68-0.83)     │   │   │
│  │  │                                                              │   │   │
│  │  │  Calibration quality: ECE = 0.03 (well-calibrated)            │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.5.2 Confidence Calibration Implementation

```python
# app/services/confidence_calibrator.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from scipy.special import expit  # sigmoid


@dataclass
class ClaimConfidence:
    """Confidence score for a single claim."""
    claim: str
    confidence: float
    confidence_interval_95: tuple[float, float]
    supporting_docs: list[str]
    calibration_method: str
    raw_score: float


@dataclass
class AnswerConfidence:
    """Aggregated confidence for a complete answer."""
    overall: float
    confidence_interval_95: tuple[float, float]
    claims: list[ClaimConfidence]
    calibration_method: str
    
    # Calibration metrics
    ece: float                    # Expected Calibration Error
    nll: float                    # Negative Log Likelihood
    
    # Contributing factors
    retrieval_confidence: float
    reranker_confidence: float
    crag_confidence: float
    evidence_count: int
    source_diversity: int
    
    @property
    def display_level(self) -> str:
        """Human-readable confidence level."""
        if self.overall >= 0.9:
            return "high"
        elif self.overall >= 0.7:
            return "medium"
        elif self.overall >= 0.5:
            return "low"
        return "very_low"
    
    @property
    def ui_color(self) -> str:
        """Color for UI display."""
        colors = {
            "high": "#22c55e",      # Green
            "medium": "#eab308",     # Yellow
            "low": "#f97316",       # Orange
            "very_low": "#ef4444",   # Red
        }
        return colors.get(self.display_level, "#6b7280")


class CalibrationModel:
    """
    Base class for calibration models.
    
    All models implement:
    - fit(): Train on labeled data
    - predict(): Calibrate raw scores
    - predict_interval(): Return confidence intervals
    """
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "CalibrationModel":
        raise NotImplementedError
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError
    
    def predict_interval(
        self, 
        X: np.ndarray, 
        confidence: float = 0.95
    ) -> tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError


class PlattScaling(CalibrationModel):
    """
    Platt Scaling (Logistic Regression on scores).
    
    Fits: P(y=1) = sigmoid(a * score + b)
    
    Good for: Well-behaved probability outputs that need slight adjustment.
    """
    
    def __init__(self):
        self.model = LogisticRegression()
        self.calibrated = False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "PlattScaling":
        """Fit Platt scaling model."""
        # X should be 1D array of raw scores
        X = X.reshape(-1, 1)
        self.model.fit(X, y)
        self.calibrated = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Calibrate scores."""
        X = X.reshape(-1, 1)
        return self.model.predict_proba(X)[:, 1]
    
    def predict_interval(
        self, 
        X: np.ndarray, 
        confidence: float = 0.95
    ) -> tuple[np.ndarray, np.ndarray]:
        """Predict with confidence intervals (approximate)."""
        calibrated = self.predict(X)
        # Approximate using score variance
        variance = np.var(calibrated) * 0.1
        std = np.sqrt(variance)
        z = 1.96  # 95% confidence
        
        lower = np.clip(calibrated - z * std, 0, 1)
        upper = np.clip(calibrated + z * std, 0, 1)
        
        return lower, upper


class IsotonicCalibration(CalibrationModel):
    """
    Isotonic Regression for non-parametric calibration.
    
    Monotonically maps raw scores to calibrated probabilities.
    
    Good for: Non-monotonic relationships between raw scores and accuracy.
    """
    
    def __init__(self):
        self.model = IsotonicRegression(out_of_bounds="clip")
        self.calibrated = False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "IsotonicCalibration":
        """Fit isotonic regression."""
        self.model.fit(X, y)
        self.calibrated = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Calibrate scores."""
        return self.model.predict(X)
    
    def predict_interval(
        self, 
        X: np.ndarray, 
        confidence: float = 0.95
    ) -> tuple[np.ndarray, np.ndarray]:
        """Predict with confidence intervals."""
        calibrated = self.predict(X)
        
        # Bin-based variance estimation
        bins = np.digitize(X, np.linspace(0, 1, 11))
        variances = np.array([np.var(y[bins == i]) if np.sum(bins == i) > 1 else 0.01 
                              for i in range(11)])
        var_for_samples = variances[bins]
        
        std = np.sqrt(var_for_samples)
        z = 1.96
        
        lower = np.clip(calibrated - z * std, 0, 1)
        upper = np.clip(calibrated + z * std, 0, 1)
        
        return lower, upper


class TemperatureScaling(CalibrationModel):
    """
    Temperature Scaling - single parameter calibration.
    
    Calibrates: softmax(logits / T)
    
    Good for: LLM logit outputs, minimal overfitting risk.
    """
    
    def __init__(self):
        self.temperature = 1.0
        self.calibrated = False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "TemperatureScaling":
        """Find optimal temperature via NLL minimization."""
        def nll_loss(T):
            scaled = X / T
            # Binary cross-entropy
            return -np.mean(y * np.log(expit(scaled)) + (1 - y) * np.log(1 - expit(scaled)))
        
        # Grid search for temperature
        best_t, best_loss = 1.0, nll_loss(1.0)
        for t in np.linspace(0.5, 3.0, 50):
            loss = nll_loss(t)
            if loss < best_loss:
                best_t, best_loss = t, loss
        
        self.temperature = best_t
        self.calibrated = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Calibrate using temperature."""
        return expit(X / self.temperature)
    
    def predict_interval(
        self, 
        X: np.ndarray, 
        confidence: float = 0.95
    ) -> tuple[np.ndarray, np.ndarray]:
        """Predict with approximate intervals."""
        calibrated = self.predict(X)
        # Wider intervals for extreme temperatures
        width_factor = max(1.0, abs(self.temperature - 1.0))
        std = 0.05 * width_factor
        z = 1.96
        
        lower = np.clip(calibrated - z * std, 0, 1)
        upper = np.clip(calibrated + z * std, 0, 1)
        
        return lower, upper


@dataclass
class CalibrationFeatures:
    """Features for confidence calibration."""
    retrieval_scores: list[float]
    reranker_score: float
    crag_score: float
    evidence_count: int
    source_diversity: int
    temporal_weight: float
    
    def to_array(self) -> np.ndarray:
        """Convert to feature array."""
        return np.array([
            np.mean(self.retrieval_scores) if self.retrieval_scores else 0,
            np.var(self.retrieval_scores) if len(self.retrieval_scores) > 1 else 0,
            np.max(self.retrieval_scores) if self.retrieval_scores else 0,
            np.min(self.retrieval_scores) if self.retrieval_scores else 0,
            self.reranker_score,
            self.crag_score,
            np.log1p(self.evidence_count),
            np.log1p(self.source_diversity),
            self.temporal_weight,
        ])


# ─────────────────────────────────────────────────────────────────────────────
# COMPLETE SYSTEM - ALL SOTA TECHNIQUES INTEGRATED
# ─────────────────────────────────────────────────────────────────────────────

## 4.S SOTA Integration Test Suite

```python
# tests/test_sota_integration.py

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.agents.crag_agent import grade_retrieval, RetrievalGrade
from app.memory.temporal_embeddings import TemporalEncoder, TemporalEmbedder
from app.agents.multihop_agent import MultiHopReasoner
from app.agents.continual_learning import ContinualLearner
from app.calibration.confidence_calibrator import ConfidenceCalibrator, CalibrationFeatures


class TestCorrectiveRAG:
    """Test CRAG grading and web fallback."""
    
    @pytest.fixture
    def sample_docs(self):
        return [
            {"id": "doc1", "content": "Transformers use self-attention mechanisms."},
            {"id": "doc2", "content": "The weather today is sunny."},
            {"id": "doc3", "content": "BERT is a transformer-based model."},
        ]
    
    @pytest.mark.asyncio
    async def test_crag_grades_relevant_docs(self, sample_docs, mock_llm):
        """CRAG should identify relevant documents."""
        mock_llm.return_value = '{"score": 0.85, "classification": "relevant", "reasoning": "Mentions transformers"}'
        
        result = await grade_retrieval(sample_docs, "What are transformers?")
        
        assert not result.needs_web_fallback
        assert result.graded_documents[0].grade == RetrievalGrade.RELEVANT
    
    @pytest.mark.asyncio
    async def test_crag_triggers_web_fallback(self, sample_docs, mock_llm):
        """CRAG should trigger fallback when docs are irrelevant."""
        # Return low scores for all docs
        mock_llm.return_value = '{"score": 0.2, "classification": "irrelevant", "reasoning": "Unrelated content"}'
        
        result = await grade_retrieval(sample_docs, "What is quantum computing?")
        
        assert result.needs_web_fallback
        assert result.fallback_reason is not None


class TestTemporalMemory:
    """Test temporal encoding and time-aware retrieval."""
    
    def test_temporal_encoder_absolute(self):
        """Temporal encoder should capture absolute time."""
        encoder = TemporalEncoder()
        
        t1 = datetime(2024, 1, 1)
        t2 = datetime(2024, 6, 1)
        
        v1 = encoder.encode(t1)
        v2 = encoder.encode(t2)
        
        # Different times should produce different vectors
        assert not np.allclose(v1, v2)
    
    def test_temporal_encoder_cyclical(self):
        """Temporal encoder should capture cyclical patterns."""
        encoder = TemporalEncoder()
        
        # Same day of week, different months
        d1 = datetime(2024, 1, 1)  # Monday
        d2 = datetime(2024, 4, 1)  # Monday
        
        v1 = encoder.encode_cyclical(d1)
        v2 = encoder.encode_cyclical(d2)
        
        # Same day of week should have similar encoding
        similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        assert similarity > 0.8


class TestMultiHopReasoning:
    """Test multi-hop query decomposition and reasoning."""
    
    @pytest.mark.asyncio
    async def test_hop_detection(self, mock_llm):
        """Should detect multi-hop queries."""
        reasoner = MultiHopReasoner()
        
        # Set up mock to return hops
        mock_llm.return_value = 'hops: 2'
        
        query = "What is the relationship between transformers and BERT?"
        hop_count = await reasoner.detect_hops(query)
        
        assert hop_count == 2
    
    @pytest.mark.asyncio
    async def test_subquery_generation(self, mock_llm):
        """Should generate appropriate subqueries."""
        reasoner = MultiHopReasoner()
        
        mock_llm.return_value = "Query: transformers architecture"
        
        context = "Transformers use self-attention."
        subquery = await reasoner.generate_subquery(context, query_number=1)
        
        assert "transformer" in subquery.lower()


class TestContinualLearning:
    """Test continual learning feedback pipeline."""
    
    @pytest.mark.asyncio
    async def test_positive_feedback_improves_retrieval(self, mock_vector_store):
        """Positive feedback should increase doc weight."""
        learner = ContinualLearner()
        
        doc_id = "doc1"
        initial_score = 0.5
        
        # Submit positive feedback
        await learner.process_feedback(
            doc_id=doc_id,
            query_hash="test_query",
            is_positive=True,
        )
        
        # Check weight increased
        weight = learner.get_document_weight(doc_id)
        assert weight > 1.0  # Should be boosted


class TestConfidenceCalibration:
    """Test confidence score calibration."""
    
    def test_platt_scaling_fit(self):
        """Platt scaling should fit to eval set."""
        calibrator = ConfidenceCalibrator()
        
        # Generate synthetic data
        X = np.random.rand(100, 5)
        y = (X[:, 0] > 0.5).astype(float)
        
        calibrator.fit_platt(X, y)
        
        assert calibrator.platt_model.calibrated
    
    def test_calibration_improves_reliability(self):
        """Calibration should reduce ECE."""
        calibrator = ConfidenceCalibrator()
        
        # Create miscalibrated predictions
        X = np.random.rand(1000, 5)
        y = (X[:, 0] > 0.5).astype(float)
        probs = np.clip(X[:, 0] + np.random.normal(0, 0.2, 1000), 0, 1)
        
        # Fit calibrator
        calibrator.fit_isotonic(probs.reshape(-1, 1), y)
        
        # Apply calibration
        calibrated = calibrator.calibrate_scores(probs.reshape(-1, 1))
        
        # Check ECE improved
        ece_before = expected_calibration_error(probs, y)
        ece_after = expected_calibration_error(calibrated, y)
        
        assert ece_after < ece_before


def expected_calibration_error(probs, labels, n_bins=10):
    """Calculate Expected Calibration Error."""
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        mask = (probs > bin_edges[i]) & (probs <= bin_edges[i + 1])
        if mask.sum() > 0:
            bin_acc = labels[mask].mean()
            bin_conf = probs[mask].mean()
            ece += mask.sum() * abs(bin_acc - bin_conf)
    
    return ece / len(probs)
```

## 4.T Deployment Checklist

### Pre-Deployment Verification

```yaml
# deployment/sota-verify.yml

pre_deployment_checks:
  crag:
    - Grading model responds < 500ms p95
    - Web fallback triggers correctly at threshold
    - Domain filtering blocks known bad sources
    - Cache hit rate > 70%
  
  temporal_memory:
    - Temporal encoder produces valid vectors
    - Time-range queries execute < 1s
    - Recency weighting affects ranking
  
  multihop:
    - Hop detection accuracy > 80%
    - Subquery generation relevant > 75%
    - Max 3 hops enforced
  
  continual_learning:
    - Feedback ingestion latency < 100ms
    - Weight updates converge within 10 iterations
    - Retraining triggers at 1000 feedback samples
  
  confidence_calibration:
    - ECE < 5% on eval set
    - Calibration model updates weekly
    - Per-claim confidence variance < 0.1

smoke_tests:
  - Query "What did I conclude last quarter?" returns time-filtered results
  - Query "Explain X's relationship to Y" triggers multi-hop
  - Query about novel topic triggers web fallback
  - All answers include calibrated confidence scores
```

### Rollback Procedures

```python
# app/rollback.py

ROLLBACK_PROCEDURES = {
    "crag": {
        "disable_flag": "CRAG_ENABLED=false",
        "health_check": "GET /health?component=crag",
        "rollback_time": "5 minutes",
    },
    "temporal_memory": {
        "disable_flag": "TEMPORAL_MEMORY_ENABLED=false",
        "health_check": "GET /health?component=temporal",
        "rollback_time": "5 minutes",
    },
    "multihop": {
        "disable_flag": "MULTIHOP_ENABLED=false",
        "health_check": "GET /health?component=multihop",
        "rollback_time": "5 minutes",
    },
    "continual_learning": {
        "disable_flag": "CONTINUAL_LEARNING_ENABLED=false",
        "health_check": "GET /health?component=learning",
        "rollback_time": "10 minutes (drain queue)",
    },
    "confidence_calibration": {
        "disable_flag": "CALIBRATION_ENABLED=false",
        "health_check": "GET /health?component=calibration",
        "rollback_time": "5 minutes",
    },
}
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Weeks 1-4)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Implement CRAG grading agent | 3 days | Existing grade_docs node |
| Add web fallback with Tavily | 5 days | CRAG agent |
| Temporal encoder + embedding pipeline | 5 days | ChromaDB integration |
| Configure CRAG thresholds via env | 1 day | CRAG agent |
| Unit tests for CRAG + temporal | 3 days | Agent implementations |
| Integration tests for fallback | 2 days | Web fallback |

### Phase 2: Reasoning (Weeks 5-8)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Multi-hop detector + subquery generator | 5 days | Router agent |
| Branch-solve-merge implementation | 5 days | Multi-hop detector |
| Temporal filter in retrieval | 3 days | Temporal embeddings |
| Temporal query parser | 2 days | LLM integration |
| Multi-hop integration into LangGraph | 3 days | All above |
| Multi-hop eval on benchmark set | 3 days | Benchmark data |

### Phase 3: Learning (Weeks 9-12)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Feedback collection API + hooks | 3 days | Answer generation |
| Document weight updater | 3 days | Feedback API |
| Periodic retraining job | 5 days | Celery Beat |
| Eval set curator | 4 days | User feedback |
| Closed-loop integration test | 3 days | All above |

### Phase 4: Calibration (Weeks 13-16)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Calibration feature extraction | 3 days | All SOTA components |
| Platt scaling implementation | 3 days | Feature extraction |
| Per-claim confidence display | 2 days | Calibration model |
| Weekly recalibration job | 3 days | Celery Beat |
| A/B test: calibrated vs raw confidence | 5 days | Feature complete |
| ECE monitoring dashboard | 2 days | Metrics pipeline |

### Phase 5: Production Hardening (Weeks 17-20)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Circuit breakers for all new components | 3 days | All components |
| Distributed tracing (OpenTelemetry) | 5 days | LangGraph nodes |
| Performance optimization | 5 days | Profiling results |
| Security audit | 3 days | All components |
| Load testing at 10x capacity | 3 days | Infra team |
| Documentation + runbooks | 2 days | All components |

### Critical Path Analysis

```
Phase 1 (CRAG) ──┬── Phase 2 (Multi-hop) ─── Phase 5 (Hardening)
                 │
                 └── Phase 2 (Temporal) ──────┘
                                           
Phase 3 (Learning) can run parallel to Phase 2
Phase 4 (Calibration) depends on Phases 1-3 complete
```

---

## Quick Reference

### SOTA Component Summary

| Component | File | Class/Function | Key Method |
|-----------|------|----------------|------------|
| CRAG Grading | `app/agents/crag_agent.py` | `grade_retrieval()` | LLM-based doc scoring |
| Web Fallback | `app/agents/web_search_agent.py` | `WebFallbackExecutor` | `execute()` |
| Temporal Encoder | `app/memory/temporal_embeddings.py` | `TemporalEncoder` | `encode()` |
| Multi-hop Reasoner | `app/agents/multihop_agent.py` | `MultiHopReasoner` | `reason()` |
| Continual Learner | `app/agents/continual_learning.py` | `ContinualLearner` | `process_feedback()` |
| Confidence Calibrator | `app/calibration/confidence_calibrator.py` | `ConfidenceCalibrator` | `calibrate_scores()` |

### Environment Variables

```bash
# CRAG
CRAG_ENABLED=true
CRAG_RELEVANCE_THRESHOLD=0.7
CRAG_FALLBACK_THRESHOLD=0.5
TAVILY_API_KEY=tvly-xxx
WEB_FALLBACK_PROVIDER=tavily

# Temporal Memory
TEMPORAL_MEMORY_ENABLED=true
TEMPORAL_WEIGHT=0.3
RECENCY_DECAY_HALF_LIFE_DAYS=90

# Multi-hop
MULTIHOP_ENABLED=true
MAX_HOPS=3
MULTIHOP_MODEL=gpt-4o-mini

# Continual Learning
CONTINUAL_LEARNING_ENABLED=true
RETRAINING_INTERVAL_HOURS=168
MIN_FEEDBACK_SAMPLES=1000
FEEDBACK_RETENTION_DAYS=90

# Confidence Calibration
CALIBRATION_ENABLED=true
CALIBRATION_METHOD=isotonic
CALIBRATION_INTERVAL_DAYS=7
```

---

**Document End**  
*For questions or clarifications, contact the MindLayer Architecture team.*