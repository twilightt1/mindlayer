# Orivory Technical Architecture v2.0

**Document Version:** 2.0  
**Last Updated:** 2026-01-19  
**Status:** Draft for Implementation  

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Current Architecture Analysis](#2-current-architecture-analysis)
3. [SOTA Implementation Architecture](#3-sota-implementation-architecture)
4. [Data Architecture](#4-data-architecture)
5. [API Design](#5-api-design)
6. [Infrastructure Requirements](#6-infrastructure-requirements)
7. [Security \& Privacy](#7-security--privacy)
8. [Monitoring \& Observability](#8-monitoring--observability)
9. [Implementation Phases](#9-implementation-phases)

---

## 1. System Overview

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    CLIENTS                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Web App   │  │   Mobile    │  │   CLI       │  │   API       │             │
│  │  (SSE/WS)  │  │  (REST)    │  │  (REST)     │  │  Integration│             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
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
          ┌────────────────────────┼────────────────────────────────────┐
          │                        │                                     │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐   │
│  LangGraph Engine  │  │   Celery Workers  │  │   Admin API       │   │
│  (Recall Workflow) │  │   (Ingestion)    │  │   (Diagnostics)   │   │
└─────────┬─────────┘  └─────────┬─────────┘  └───────────────────┘   │
          │                     │                                         
    ┌─────┴─────────────────────┴─────┐                              
    │                                   │                              
┌───▼───┐  ┌──────┐  ┌───────┐  ┌────▼────┐  ┌──────────┐           
│Router │  │Memory│  │KG     │  │Retrieval│  │Eval/    │           
│(LLM)  │  │Hist. │  │Context│  │(Hybrid) │  │Calibr.  │  [NEW]   
└───┬───┘  └──┬───┘  └───┬───┘  └───┬───┘  └────┬─────┘           
    │         │           │          │             │                 
    └─────────┴───────────┴──────────┴─────────────┘                 
                      │                                               
    ┌─────────────────┴──────────────────────────────────────────┐  
    │                    RETRIEVAL PIPELINE                        │  
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐    │  
    │  │  BM25   │  │ Vector  │  │  RRF    │  │ Reranker    │    │  
    │  │ (Redis) │  │(ChromaDB│  │ Fusion  │  │ (Jina API)  │    │  
    │  └─────────┘  └─────────┘  └─────────┘  └─────────────┘    │  
    └──────────────────────────────────────────────────────────────┘  
                                                                       

┌────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE LAYER                                  │
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│  │   PostgreSQL    │  │     Redis       │  │    ChromaDB     │           │
│  │                 │  │                 │  │                 │           │
│  │ • Users         │  │ • Rate Limits   │  │ • Vectors       │           │
│  │ • Conversations │  │ • BM25 Cache    │  │ • Col: per-conv │           │
│  │ • Messages      │  │ • Refresh Tokens│  │ • HNSW Index    │           │
│  │ • Memories      │  │ • SSE Task IDs  │  │                 │           │
│  │ • Entities      │  │ • Query Cache   │  └─────────────────┘           │
│  │ • Relations     │  │                 │                                  │
│  │ • Documents     │  └─────────────────┘                                  │
│  │ • Chunks        │                                                     │
│  └─────────────────┘                                                     │
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐                               │
│  │     MinIO       │  │   Celery Beat    │                               │
│  │                 │  │   (Scheduler)    │                               │
│  │ • Original Files│  │                 │                               │
│  │ • Parsed Text   │  │ • Retraining Jobs│  [NEW]                        │
│  │ • Media Assets  │  │ • Decay Tasks   │                               │
│  └─────────────────┘  └─────────────────┘                               │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **API Gateway** | Request routing, auth, rate limiting, SSE streaming | FastAPI |
| **LangGraph Engine** | Orchestrates the recall workflow as a directed graph | LangGraph StateGraph |
| **Router Agent** | Classifies query intent (recall/save_note/web_search) | LLM (OpenRouter) |
| **Memory Agent** | Loads conversation history for context | PostgreSQL |
| **Personal Context Agent** | Retrieves user memories related to query | ChromaDB + Redis |
| **Graph Context Agent** | Extracts entities/relations from knowledge graph | PostgreSQL KG |
| **Retrieval Agent** | Executes hybrid search (BM25 + Vector + RRF) | BM25 + ChromaDB |
| **Reranker** | Re-ranks retrieved chunks using cross-encoder | Jina Reranker API |
| **Answer Agent** | Generates grounded, cited responses | LLM (OpenRouter) |
| **Evaluator Agent** | Grades document relevance (Corrective-RAG) | LLM (OpenRouter) |
| **Hallucination Agent** | Validates answer-grounding | LLM (OpenRouter) |
| **Celery Workers** | Async ingestion, embeddings, scheduled tasks | Celery + Redis |
| **MinIO** | Object storage for original files | MinIO S3-compatible |

### 1.3 Data Flow (Current vs. Target)

#### Current Data Flow
```
Query → Router → Memory → PersonalContext → GraphContext → Retrieval 
    → MergeContext → GradeDocs → Answer → GradeGen → SSE
```

#### Target Data Flow (with SOTA additions)
```
Query → Router → Memory → PersonalContext → GraphContext → Retrieval 
    → GradeDocs → [CRAG: Web Fallback if low confidence] → ParentExpansion 
    → Reranker → TemporalFilter → Answer → CalibrateConfidence → GradeGen → SSE
```

---

## 2. Current Architecture Analysis

### 2.1 Strengths

1. **Production-Ready Foundation**
   - 187 CI-safe tests passing
   - Full-repo ruff clean
   - Security readiness gate implemented

2. **Robust Auth System**
   - JWT + OAuth (Google) authentication
   - Hashed refresh tokens in Redis with O(1) revocation
   - Soft-delete aware user management
   - Production mode enforces strong secrets

3. **Hybrid Retrieval**
   - BM25 + Vector search with RRF fusion
   - Parent-child chunking strategy
   - Jina reranking for quality

4. **LangGraph Workflow**
   - 11 nodes, 6 retry edges
   - Self-correction on irrelevant context and hallucinations
   - Bounded retries prevent infinite loops

5. **Observability**
   - Agent trace metadata
   - Retrieval timing tracking
   - Citation traces
   - Admin diagnostics endpoint

### 2.2 Weaknesses

1. **Single-Pass Retrieval**
   - No retrieval grader integration
   - No web search fallback for gaps
   - Cannot self-correct based on document quality

2. **No Temporal Awareness**
   - `captured_at` timestamps stored but not utilized in retrieval
   - Time-filtered queries not supported
   - Recency bias absent

3. **Flat Retrieval**
   - Single-hop queries only
   - No multi-hop reasoning for complex questions
   - No query decomposition

4. **Static System**
   - No feedback → retraining pipeline
   - No active learning
   - Embeddings never updated based on usage

5. **No Confidence Calibration**
   - Confidence scores not exposed to users
   - No statistical calibration
   - No uncertainty quantification

### 2.3 Technical Debt

| Issue | Location | Impact | Effort |
|-------|----------|--------|--------|
| BM25 rebuild in API process | `app/retrieval/bm25_retriever.py` | Latency spike on cold cache | Low |
| Missing conversation-scoped vector collections | `app/retrieval/` | Cross-conversation bleed risk | Medium |
| No retry queue for failed ingestions | `app/tasks/` | Lost documents | Medium |
| Hardcoded `k=60` for RRF | `app/retrieval/hybrid_retriever.py` | Non-optimal fusion | Low |
| No temporal indexes on timestamps | `app/models/memory.py` | Slow time-range queries | Low |

### 2.4 Scalability Limits

1. **ChromaDB Single-Node**
   - HNSW index not horizontally scalable
   - ~10M vectors before degradation

2. **PostgreSQL Connection Pool**
   - Default: 10 connections + 20 overflow
   - Single-region only

3. **Redis Memory**
   - BM25 cache size unbounded
   - No eviction policy for query cache

4. **LLM Rate Limits**
   - OpenRouter API rate limits not enforced per-user
   - No model routing based on query complexity

---

## 3. SOTA Implementation Architecture

### 3.1 Corrective-RAG Pipeline

**Reference:** "Corrective-RAG (CRAG)" — self-corrects retrieval results using a retrieval grader.

#### 3.1.1 New LangGraph Nodes

```
┌─────────────────────────────────────────────────────────────────┐
│                    CORRECTIVE-RAG NODES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ grade_docs   │ ──► Determines document relevance            │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              ROUTE: grade_docs                          │    │
│  │                                                          │    │
│  │   relevance_score >= 0.7  ──────────────────────────┐   │    │
│  │   0.3 <= relevance_score < 0.7 ───► web_search ───┼──┼──►│    │
│  │   relevance_score < 0.3       ───► transform ──────┘   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │ transform    │ ──► │ web_search   │ ──► │ transform    │     │
│  │ (rewrite     │     │ (fallback)   │     │ (merge web) │     │
│  │  query)      │     │              │     │              │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Retrieval Grader Design

```python
# app/agents/grade_docs_agent.py (NEW)

from dataclasses import dataclass
from enum import Enum


class RelevanceLevel(str, Enum):
    HIGH = "high"       # >= 0.7
    MEDIUM = "medium"   # 0.3 - 0.7
    LOW = "low"         # < 0.3


@dataclass
class RetrievalGrade:
    """Grading result for document relevance."""
    chunk_id: str
    relevance_score: float  # 0.0 - 1.0
    relevance_level: RelevanceLevel
    reasoning: str
    should_include: bool
    suggested_modification: str | None = None  # For transform node


GRADE_DOCS_PROMPT = """You are a retrieval grader. Evaluate whether the retrieved context 
contains sufficient information to answer the user's question.

Question: {question}
Context: {context}

Provide a relevance score from 0.0 to 1.0 where:
- 1.0: Context fully answers the question
- 0.5: Context partially relevant, needs augmentation
- 0.0: Context completely irrelevant

Respond in JSON format:
{{"score": float, "reasoning": str}}
"""
```

#### 3.1.3 Web Fallback Integration

```python
# app/agents/web_search_agent.py (NEW)

from typing import Protocol
import httpx


class WebSearchProvider(Protocol):
    """Pluggable web search interface."""
    async def search(self, query: str, num_results: int = 5) -> list[dict]: ...


class TavilyWebSearch:
    """Tavily API implementation."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
    
    async def search(self, query: str, num_results: int = 5) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"query": query, "max_results": num_results}
            )
            data = response.json()
            return [
                {"title": r["title"], "content": r["content"], "url": r["url"]}
                for r in data.get("results", [])
            ]
```

#### 3.1.4 Confidence Scoring

```python
# app/agents/confidence_scorer.py (NEW)

from dataclasses import dataclass
import numpy as np


@dataclass
class ConfidenceScore:
    """Aggregated confidence for an answer."""
    overall: float                    # 0.0 - 1.0
    retrieval_confidence: float       # Based on retrieval grader scores
    generation_confidence: float      # Based on answer coherence checks
    calibration_method: str           # "platt" | "isotonic" | "histogram"
    confidence_interval_95: tuple[float, float]
    
    @property
    def display_level(self) -> str:
        if self.overall >= 0.9:
            return "high"
        elif self.overall >= 0.7:
            return "medium"
        return "low"


def aggregate_grades(grades: list[RetrievalGrade]) -> float:
    """Aggregate individual grades into overall retrieval confidence."""
    if not grades:
        return 0.0
    
    scores = [g.relevance_score for g in grades]
    weights = [1.0 / (i + 1) for i in range(len(scores))]  # Rank-weighted
    
    weighted_avg = np.average(scores, weights=weights)
    
    # Boost if top results are highly relevant
    top_scores = sorted(scores, reverse=True)[:3]
    if np.mean(top_scores) > 0.8:
        weighted_avg = min(1.0, weighted_avg * 1.1)
    
    return round(weighted_avg, 3)
```

#### 3.1.5 Implementation Pattern

```python
# app/agents/routing.py (APPEND)

def route_after_grade_docs(state: AgentState) -> str:
    """
    CRAG routing logic:
    - HIGH relevance: proceed to answer
    - MEDIUM relevance: try web search
    - LOW relevance: transform query and retry retrieval
    """
    grades = state.get("doc_grades", [])
    if not grades:
        # No grades yet - this shouldn't happen in normal flow
        return "answer"
    
    avg_score = aggregate_grades(grades)
    
    if avg_score >= 0.7:
        return "answer"
    elif avg_score >= 0.3:
        state["web_search_triggered"] = True
        return "web_search"
    else:
        state["query_transformed"] = True
        return "transform"
```

---

### 3.2 Temporal Memory System

**Reference:** Time-aware retrieval using timestamp embeddings and temporal filters.

#### 3.2.1 Timestamp Embedding Strategy

```
┌────────────────────────────────────────────────────────────────┐
│               TEMPORAL EMBEDDING STRATEGY                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Standard Chunk Embedding:                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [CLS] semantic tokens ... [SEP] temporal tokens [SEP]    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Temporal Token Format:                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ YEAR:2024 MONTH:03 DAY:15 DOW:Friday HOUR:14          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Storage in ChromaDB:                                            │
│  ┌────────────┬──────────────────────┬──────────────────────┐   │
│  │  chunk_id  │   embedding (1536d)  │   temporal_vector    │   │
│  │            │   (semantic)        │   (384d, optional)   │   │
│  └────────────┴──────────────────────┴──────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Time-Aware Retrieval

```python
# app/retrieval/temporal_retriever.py (NEW)

from datetime import datetime, timedelta
from typing import Literal
import numpy as np


class TemporalWeightMode(str):
    RECENCY_BIAS = "recency"      # Recent memories weighted higher
    HISTORICAL_WEIGHT = "historical"  # Older memories weighted higher
    UNIFORM = "uniform"           # No temporal weighting


@dataclass
class TemporalQuery:
    """Query with temporal constraints."""
    text: str
    time_range: tuple[datetime, datetime] | None = None
    weight_mode: TemporalWeightMode = TemporalWeightMode.RECENCY_BIAS
    temporal_decay_factor: float = 0.95  # Half-life in days


@dataclass
class TemporalRetrievalResult:
    """Retrieval result with temporal scoring."""
    chunk: dict
    semantic_score: float
    temporal_score: float
    combined_score: float
    days_ago: int  # For display


def compute_temporal_score(
    captured_at: datetime,
    query_time_range: tuple[datetime, datetime] | None,
    weight_mode: TemporalWeightMode,
    decay_factor: float,
    now: datetime | None = None
) -> float:
    """Compute temporal relevance score for a memory."""
    if now is None:
        now = datetime.utcnow()
    
    days_ago = (now - captured_at).days
    
    # If query has explicit time range, score based on range match
    if query_time_range:
        range_start, range_end = query_time_range
        if range_start <= captured_at <= range_end:
            return 1.0
        # Score based on distance from range
        if captured_at < range_start:
            days_outside = (range_start - captured_at).days
            return max(0.1, 1.0 - (days_outside / 365))
        else:
            days_outside = (captured_at - range_end).days
            return max(0.1, 1.0 - (days_outside / 365))
    
    # Otherwise apply decay based on weight mode
    if weight_mode == TemporalWeightMode.RECENCY_BIAS:
        # Exponential decay: score = decay_factor^(days_ago/30)
        return decay_factor ** (days_ago / 30)
    
    elif weight_mode == TemporalWeightMode.HISTORICAL_WEIGHT:
        # Inverse recency: older memories score higher
        return 1.0 / (1.0 + np.log1p(days_ago) * 0.1)
    
    return 1.0  # UNIFORM


async def temporal_retrieve(
    query: TemporalQuery,
    base_retriever,
    top_k: int = 10,
) -> list[TemporalRetrievalResult]:
    """Execute retrieval with temporal scoring."""
    # Get base semantic results
    semantic_results = await base_retriever(query.text, top_k=top_k * 2)
    
    results = []
    now = datetime.utcnow()
    
    for chunk in semantic_results:
        captured_at = chunk.get("metadata", {}).get("captured_at")
        if not captured_at:
            captured_at = now
        
        temporal_score = compute_temporal_score(
            captured_at=captured_at,
            query_time_range=query.time_range,
            weight_mode=query.weight_mode,
            decay_factor=query.temporal_decay_factor,
            now=now
        )
        
        # Combined score: geometric mean of semantic and temporal
        semantic_score = chunk.get("rerank_score", chunk.get("score", 0.5))
        combined = np.sqrt(semantic_score * temporal_score)
        
        results.append(TemporalRetrievalResult(
            chunk=chunk,
            semantic_score=semantic_score,
            temporal_score=temporal_score,
            combined_score=combined,
            days_ago=(now - captured_at).days
        ))
    
    # Re-sort by combined score
    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results[:top_k]
```

#### 3.2.3 Temporal Query Decomposition

```python
# app/agents/temporal_query_agent.py (NEW)

"""
Temporal query patterns and their decomposition:

Patterns:
  - "last week" / "recently" → time_range: (now - 7d, now)
  - "in March 2024" → time_range: (2024-03-01, 2024-03-31)
  - "about a month ago" → time_range: (now - 45d, now - 15d)
  - "before 2023" → time_range: (epoch, 2023-01-01)
  - "during my time at X" → extract date range from KG entity
"""

TEMPORAL_DECOMPOSE_PROMPT = """Analyze this query for temporal references.

Query: {query}

Extract:
1. Any explicit date ranges mentioned
2. Relative time references (last week, recently, etc.)
3. Implicit time constraints from context

Respond in JSON format:
{{
  "explicit_range": {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}} | null,
  "relative_reference": "last week" | null,
  "confidence": float,
  "needs_kg_lookup": bool,
  "kg_entity_hint": "person/project name" | null
}}
"""


def parse_temporal_reference(text: str) -> TemporalQuery:
    """Parse natural language temporal references."""
    text_lower = text.lower()
    
    now = datetime.utcnow()
    
    # Common patterns
    patterns = [
        (r"\blast week\b", 7),
        (r"\blast month\b", 30),
        (r"\brecently\b", 14),
        (r"\btoday\b", 0),
        (r"\byesterday\b", 1),
        (r"\bthis week\b", 7),
        (r"\bthis month\b", 30),
    ]
    
    for pattern, days in patterns:
        if re.search(pattern, text_lower):
            return TemporalQuery(
                text=re.sub(pattern, "", text_lower).strip(),
                time_range=(now - timedelta(days=days), now),
                weight_mode=TemporalWeightMode.RECENCY_BIAS
            )
    
    # Year patterns
    year_match = re.search(r"\b(20\d{2})\b", text)
    if year_match:
        year = int(year_match.group(1))
        return TemporalQuery(
            text=re.sub(r"\b(20\d{2})\b", "", text_lower).strip(),
            time_range=(datetime(year, 1, 1), datetime(year, 12, 31))
        )
    
    # No temporal reference found
    return TemporalQuery(text=text)
```

#### 3.2.4 Storage Schema Changes

```sql
-- Migration: add temporal indexes and columns

ALTER TABLE memories ADD COLUMN IF NOT EXISTS 
    embedding_temporal_id uuid REFERENCES document_chunks(id);

ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS 
    temporal_vector vector(384);  -- Separate temporal embedding

CREATE INDEX IF NOT EXISTS ix_memories_captured_at_temporal 
    ON memories (user_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS ix_memories_time_range
    ON memories (user_id, captured_at) 
    WHERE captured_at > NOW() - INTERVAL '2 years';

-- ChromaDB collection schema update (handled in code)
-- Add temporal_vector to metadata for filtering
```

---

### 3.3 Multi-hop Reasoning

**Reference:** EfficientRAG-style iterative retrieval with next-hop query generation.

#### 3.3.1 EfficientRAG Implementation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTI-HOP REASONING GRAPH                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐         │
│   │  START  │────►│  HOP 1   │────►│  HOP 2  │────►│  HOP N  │         │
│   └─────────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘         │
│                        │                │                │               │
│                        ▼                ▼                ▼               │
│                  ┌──────────┐     ┌──────────┐     ┌──────────┐         │
│                  │Extract   │     │Extract   │     │Extract   │         │
│                  │Entities  │     │Entities  │     │Entities  │         │
│                  └────┬─────┘     └────┬─────┘     └────┬─────┘         │
│                       │                │                │               │
│                       ▼                ▼                ▼               │
│   ┌──────────────────────────────────────────────────────────┐         │
│   │              HOP BUFFER (shared state)                   │         │
│   │  • collected_facts: list[str]                            │         │
│   │  • derived_entities: set[str]                           │         │
│   │  • hop_count: int                                        │         │
│   │  • max_hops: int (configurable, default 3)              │         │
│   └──────────────────────────────────────────────────────────┘         │
│                        │                                               │
│                        ▼                                               │
│                  ┌──────────┐                                          │
│                  │ ANSWER   │                                          │
│                  │ GENERATE  │                                          │
│                  └──────────┘                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Next-hop Query Generation

```python
# app/agents/multihop_agent.py (NEW)

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class MultiHopState(AgentState):
    """Extended state for multi-hop reasoning."""
    hop_count: int = 0
    max_hops: int = 3
    collected_facts: list[str] = field(default_factory=list)
    derived_entities: list[str] = field(default_factory=list)
    sub_queries: list[str] = field(default_factory=list)
    is_multi_hop: bool = False
    

GENERATE_SUBQUERY_PROMPT = """You are reasoning through a complex question.

Original question: {question}
Previous sub-queries: {previous_queries}
Collected facts so far: {collected_facts}

Determine if this question requires multiple reasoning steps.
A multi-hop question requires finding intermediate information 
before answering the main question.

Examples of multi-hop:
- "What did X do after graduating from Y university?" 
  → Need Y first, then X's career
- "Who was the CEO of the company that acquired X?"
  → Need X's acquirer first, then the CEO

Examples of single-hop:
- "What is the capital of France?" → Direct answer
- "When was Python created?" → Direct answer

If multi-hop, generate the NEXT sub-query to answer.
If single-hop or complete, respond with "DONE".

Respond in JSON format:
{{
  "is_multi_hop": bool,
  "sub_query": "next question to answer" | null,
  "reasoning": "why this is/isn't multi-hop"
}}
"""


def should_continue_hopping(state: MultiHopState) -> bool:
    """Determine if we should continue to the next hop."""
    if state.hop_count >= state.max_hops:
        return False
    
    if not state.is_multi_hop:
        return False
    
    # Check if we have enough facts to answer
    if len(state.collected_facts) >= 2 and state.hop_count >= 1:
        return False
    
    return True


async def generate_next_hop(state: MultiHopState, llm) -> str:
    """Generate the next sub-query in the reasoning chain."""
    state.hop_count += 1
    
    # Check for multi-hop complexity
    analysis = await llm.agenerate([
        GENERATE_SUBQUERY_PROMPT.format(
            question=state.query,
            previous_queries=", ".join(state.sub_queries),
            collected_facts="\n".join(f"- {f}" for f in state.collected_facts)
        )
    ])
    
    result = json.loads(analysis.generations[0][0].text)
    
    if not result.get("is_multi_hop"):
        state.is_multi_hop = False
        return "answer"
    
    state.is_multi_hop = True
    state.sub_queries.append(result["sub_query"])
    
    if should_continue_hopping(state):
        return "retrieval"
    else:
        return "answer"
```

#### 3.3.3 Branch-Solve-Merge Pattern

```python
# app/agents/branch_solve_merge.py (NEW)

"""
For questions with parallel sub-questions:

"Compare X and Y's approaches to Z"

Branching:     ┌─► Sub-question A (retrieve X)
               │
START ─────────┼─► Sub-question B (retrieve Y)
               │
               └─► Sub-question C (retrieve Z context)

Solving:       Each branch retrieved independently

Merging:      Combine into unified answer with comparison
"""

@dataclass
class BranchResult:
    """Result from a single branch."""
    branch_id: str
    retrieved_context: list[str]
    answer_fragment: str
    confidence: float


async def parallel_branch_retrieve(
    sub_questions: list[str],
    retriever,
    max_concurrent: int = 3
) -> list[BranchResult]:
    """Execute multiple retrieval branches in parallel."""
    
    async def retrieve_branch(bq_id: str, query: str) -> BranchResult:
        results = await retriever(query, top_k=5)
        context = [r["content"] for r in results]
        return BranchResult(
            branch_id=bq_id,
            retrieved_context=context,
            answer_fragment="",  # Filled by answer agent
            confidence=results[0].get("score", 0.5) if results else 0.0
        )
    
    # Use asyncio.gather with semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_retrieve(bq_id: str, query: str):
        async with semaphore:
            return await retrieve_branch(bq_id, query)
    
    tasks = [
        bounded_retrieve(f"branch_{i}", q) 
        for i, q in enumerate(sub_questions)
    ]
    
    return await asyncio.gather(*tasks)


MERGE_PROMPT = """You have retrieved context for multiple sub-questions.

Sub-questions and their context:
{branch_results}

Original question: {original_question}

Generate a unified answer that:
1. Addresses each sub-question
2. Synthesizes findings into a coherent response
3. Properly attributes information to sources

Respond with the unified answer.
"""
```

#### 3.3.4 Hop Counter and Depth Limiting

```python
# app/agents/routing.py (MODIFY)

# Add to routing.py

MAX_HOP_THRESHOLD = 3  # Configurable via settings


def detect_multi_hop_complexity(query: str, llm) -> tuple[bool, int]:
    """
    Detect if a query requires multi-hop reasoning.
    Returns (is_multi_hop, estimated_hop_count).
    """
    # Simple heuristic first
    complex_indicators = [
        "who was",  # Subject resolution
        "after",    # Temporal sequence
        "which company",  # Entity resolution
        "compared to",   # Parallel reasoning
        "because",        # Causal chain
        "therefore",      # Inference chain
    ]
    
    complexity_score = sum(1 for ind in complex_indicators if ind in query.lower())
    
    # If heuristic suggests complexity, use LLM for confirmation
    if complexity_score >= 2:
        # LLM call for precise hop count estimation
        ...
    
    estimated_hops = min(max(1, complexity_score), MAX_HOP_THRESHOLD)
    return complexity_score > 0, estimated_hops
```

---

### 3.4 Continual Learning Pipeline

**Reference:** Feedback → Eval Sets → Active Learning → Retriever Fine-tuning

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTINUAL LEARNING PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      FEEDBACK COLLECTION                          │   │
│  │                                                                   │   │
│  │  User Feedback:    👍 / 👎 / Correction                          │   │
│  │  Implicit Signals: Time on answer, Click-through on sources       │   │
│  │  Explicit Signals: Starred answers, Re-asked questions          │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      EVAL SET CURATION                            │   │
│  │                                                                   │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │   │
│  │  │ Positive   │  │ Negative   │  │ Hard       │                  │   │
│  │  │ Examples   │  │ Examples   │  │ Examples   │                  │   │
│  │  │ (upvoted)  │  │ (downvoted)│ │ (clicked   │                  │   │
│  │  │            │  │            │  │  no cite)  │                  │   │
│  │  └────────────┘  └────────────┘  └────────────┘                  │   │
│  │                                                                   │   │
│  │  Quality filters: Language model judge, keyword overlap           │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      ACTIVE LEARNING                              │   │
│  │                                                                   │   │
│  │  Uncertainty sampling: Focus on low-confidence retrievals        │   │
│  │  Diversity sampling: Ensure coverage of topic space              │   │
│  │  Margin sampling: Focus on borderline retrievals                  │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  SELECT query_id, query_text                              │  │   │
│  │  │  FROM user_feedback                                        │  │   │
│  │  │  WHERE confidence < 0.7                                    │  │   │
│  │  │    AND retrieval_grade < 0.6                               │  │   │
│  │  │  ORDER BY RANDOM()                                         │  │   │
│  │  │  LIMIT 100                                                  │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      RETRIEVER FINE-TUNING                        │   │
│  │                                                                   │   │
│  │  Model: Sentence-transformers / Instructor models                │   │
│  │  Method: Contrastive learning with hard negatives                │   │
│  │  Schedule: Weekly batch fine-tuning via Celery Beat               │   │
│  │                                                                   │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │   │
│  │  │ Fine-tune  │────►│  Evaluate   │────►│  Approve &  │        │   │
│  │  │  Model     │     │  on Eval    │     │  Deploy     │        │   │
│  │  └─────────────┘     └─────────────┘     └─────────────┘        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.4.1 Feedback Collection

```python
# app/models/feedback.py (NEW)

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import uuid


class UserFeedback(Base):
    """Captures user feedback on answers for continual learning."""
    
    __tablename__ = "user_feedback"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )
    
    # Reference to the answer
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
    feedback_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "thumbs_up" | "thumbs_down" | "correction" | "citation_click"
    
    # Explicit rating
    rating: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    # 1-5 scale, null for implicit feedback
    
    # Implicit signals
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    source_clicks: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    
    # LLM-assessed quality scores (from evaluator)
    retrieval_confidence: Mapped[float | None] = mapped_column(Float(), nullable=True)
    answer_quality: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # For corrections
    correction_text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    
    # Metadata
    extra_data: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=text("now()")
    )
    
    __table_args__ = (
        Index("ix_feedback_user_message", "user_id", "message_id"),
        Index("ix_feedback_quality", "retrieval_confidence", "answer_quality"),
    )
```

#### 3.4.2 Eval Set Curation

```python
# app/services/eval_curation.py (NEW)

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID


@dataclass
class EvalExample:
    """A curated evaluation example for retriever fine-tuning."""
    query_id: UUID
    query_text: str
    relevant_memory_ids: list[UUID]  # Ground truth
    irrelevant_memory_ids: list[UUID]  # Known negatives
    difficulty: str  # "easy" | "medium" | "hard"
    source: str  # "user_feedback" | "admin_curated" | "synthetic"
    created_at: datetime


class EvalSetCurator:
    """Curates evaluation sets from user feedback."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def curate_from_feedback(
        self,
        user_id: UUID,
        min_rating: int = 4,
        time_window_days: int = 30
    ) -> list[EvalExample]:
        """Extract high-quality examples from user feedback."""
        
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)
        
        # Get positively rated queries with good retrieval confidence
        query = select(UserFeedback).where(
            UserFeedback.user_id == user_id,
            UserFeedback.created_at >= cutoff,
            UserFeedback.rating >= min_rating,
            UserFeedback.retrieval_confidence >= 0.7,
            UserFeedback.feedback_type == "thumbs_up"
        )
        
        results = await self.db.execute(query)
        feedback_rows = results.scalars().all()
        
        examples = []
        for fb in feedback_rows:
            # Get the associated memories from citation trace
            message = await self.db.get(Message, fb.message_id)
            if not message:
                continue
            
            trace = message.extra_metadata or {}
            cited_ids = trace.get("cited_memory_ids", [])
            
            examples.append(EvalExample(
                query_id=fb.id,
                query_text=self._extract_query_from_message(message),
                relevant_memory_ids=cited_ids,
                irrelevant_memory_ids=[],  # Need separate negative mining
                difficulty="medium",
                source="user_feedback",
                created_at=fb.created_at
            ))
        
        return examples
    
    def _extract_query_from_message(self, message: Message) -> str:
        """Extract the original query from a message."""
        # Message structure: role='user' for queries, role='assistant' for answers
        # This needs to be implemented based on actual schema
        ...
```

#### 3.4.3 Active Learning Selection

```python
# app/services/active_learning.py (NEW)

from enum import Enum


class SamplingStrategy(str, Enum):
    UNCERTAINTY = "uncertainty"      # Focus on low confidence
    DIVERSITY = "diversity"          # Ensure topic coverage
    MARGIN = "margin"               # Borderline cases


@dataclass
class ActiveLearningCandidate:
    """Query selected for active learning annotation."""
    query_id: UUID
    query_text: str
    current_retrieval_ids: list[UUID]
    confidence: float
    selection_reason: str
    priority: float  # Higher = more valuable for training


class ActiveLearningSelector:
    """Selects queries for retriever fine-tuning based on learning value."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def select_candidates(
        self,
        user_id: UUID,
        strategy: SamplingStrategy = SamplingStrategy.UNCERTAINTY,
        num_candidates: int = 100
    ) -> list[ActiveLearningCandidate]:
        """Select the most valuable queries for retriever improvement."""
        
        if strategy == SamplingStrategy.UNCERTAINTY:
            return await self._uncertainty_sampling(user_id, num_candidates)
        elif strategy == SamplingStrategy.DIVERSITY:
            return await self._diversity_sampling(user_id, num_candidates)
        else:
            return await self._margin_sampling(user_id, num_candidates)
    
    async def _uncertainty_sampling(
        self, 
        user_id: UUID, 
        num: int
    ) -> list[ActiveLearningCandidate]:
        """Select queries where retrieval confidence is lowest."""
        
        query = (
            select(Message, UserFeedback)
            .join(UserFeedback, UserFeedback.message_id == Message.id)
            .where(
                Message.user_id == user_id,
                UserFeedback.retrieval_confidence < 0.7,
                UserFeedback.retrieval_confidence > 0.0
            )
            .order_by(UserFeedback.retrieval_confidence.asc())
            .limit(num)
        )
        
        results = await self.db.execute(query)
        
        candidates = []
        for msg, fb in results:
            candidates.append(ActiveLearningCandidate(
                query_id=msg.id,
                query_text=self._extract_query(msg),
                current_retrieval_ids=self._extract_cited_ids(msg),
                confidence=fb.retrieval_confidence or 0.5,
                selection_reason="low_retrieval_confidence",
                priority=1.0 - (fb.retrieval_confidence or 0.5)
            ))
        
        return candidates
```

#### 3.4.4 Retriever Fine-tuning Pipeline

```python
# app/tasks/retraining_tasks.py (NEW)

from celery import shared_task
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import json


@shared_task(bind=True, max_retries=3)
def fine_tune_retriever(
    self,
    user_id: str,
    eval_set_path: str,
    base_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    epochs: int = 3,
    batch_size: int = 16,
    output_path: str = "/models/retriever/"
) -> dict:
    """
    Fine-tune the retriever model on user-specific feedback.
    
    Run weekly via Celery Beat.
    """
    
    # Load eval set
    with open(eval_set_path) as f:
        eval_data = json.load(f)
    
    # Convert to InputExamples
    train_examples = []
    for item in eval_data:
        # Positive pair: query → relevant memory
        for mem_id in item["relevant_memory_ids"]:
            train_examples.append(InputExample(
                texts=[item["query_text"], item["memory_text"]],
                label=1.0
            ))
        
        # Hard negative: query → irrelevant memory
        for mem_id in item["irrelevant_memory_ids"]:
            train_examples.append(InputExample(
                texts=[item["query_text"], item["memory_text"]],
                label=0.0
            ))
    
    # Load base model
    model = SentenceTransformer(base_model)
    
    # Create DataLoader with MultipleNegativesRankingLoss
    train_dataloader = DataLoader(
        train_examples, 
        shuffle=True, 
        batch_size=batch_size
    )
    
    train_loss = losses.MultipleNegativesRankingLoss(model)
    
    # Fine-tune
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        show_progress_bar=True
    )
    
    # Save fine-tuned model
    model_path = f"{output_path}/{user_id}_v{self.request.id[:8]}"
    model.save(model_path)
    
    # Evaluate on holdout set
    metrics = evaluate_retriever(model_path, eval_data["test"])
    
    return {
        "model_path": model_path,
        "metrics": metrics,
        "training_examples": len(train_examples)
    }


@shared_task
def schedule_weekly_retraining():
    """Celery Beat: Run weekly retraining for active users."""
    
    # Get users with sufficient feedback (100+ examples)
    active_users = get_users_needing_retraining(threshold=100)
    
    for user in active_users:
        # Check if enough new feedback since last training
        new_feedback_count = count_new_feedback(user.id)
        if new_feedback_count >= 50:
            # Create eval set
            eval_path = create_eval_set(user.id)
            
            # Queue fine-tuning
            fine_tune_retriever.delay(
                user_id=str(user.id),
                eval_set_path=eval_path
            )
```

---

### 3.5 Confidence Calibration

**Reference:** Statistical calibration of confidence scores using Platt scaling and histogram binning.

#### 3.5.1 Calibration Methodology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIDENCE CALIBRATION PIPELINE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Raw Score Sources:                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ Retrieval      │  │ Reranker       │  │ Generation     │            │
│  │ Grader (0-1)   │  │ Scores (0-1)   │  │ Coherence (0-1)│            │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘            │
│          │                    │                    │                      │
│          └────────────────────┼────────────────────┘                      │
│                               │                                           │
│                               ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    SCORE AGGREGATION                              │  │
│  │                                                                   │  │
│  │  confidence = w1 * retrieval + w2 * rerank + w3 * generation     │  │
│  │                                                                   │  │
│  │  where weights are learned from historical feedback               │  │
│  └────────────────────────────┬─────────────────────────────────────┘  │
│                               │                                           │
│                               ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    CALIBRATION METHODS                             │  │
│  │                                                                   │  │
│  │  1. PLATT SCALING (sigmoid calibration)                          │  │
│  │     confidence_calibrated = 1 / (1 + exp(-(a * raw + b)))        │  │
│  │                                                                   │  │
│  │  2. ISOTONIC REGRESSION (non-parametric)                        │  │
│  │     confidence_calibrated = isotonic_transform(raw)              │  │
│  │                                                                   │  │
│  │  3. HISTOGRAM BINNING                                            │  │
│  │     confidence_calibrated = expected_accuracy_in_bin(raw)       │  │
│  │                                                                   │  │
│  └────────────────────────────┬─────────────────────────────────────┘  │
│                               │                                           │
│                               ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    CALIBRATION METRICS                           │  │
│  │                                                                   │  │
│  │  Expected Calibration Error (ECE):                               │  │
│  │  ECE = Σ (|B_m| / n) * |accuracy(B_m) - confidence(B_m)|      │  │
│  │                                                                   │  │
│  │  Target: ECE < 0.05 (5%) for production                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.5.2 Score Aggregation

```python
# app/agents/confidence_calibrator.py (NEW)

from dataclasses import dataclass
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression


@dataclass
class RawScores:
    """Raw confidence scores from various sources."""
    retrieval_grades: list[float]  # From retrieval grader
    reranker_scores: list[float]  # From Jina reranker
    generation_coherence: float   # From hallucination checker
    retrieval_completeness: float  # From grade_docs


@dataclass
class CalibrationResult:
    """Final calibrated confidence with metadata."""
    raw_confidence: float
    calibrated_confidence: float
    confidence_interval_95: tuple[float, float]
    calibration_method: str
    component_scores: dict[str, float]
    is_calibrated: bool
    calibration_error: float | None  # ECE if calibrated


class ConfidenceCalibrator:
    """Calibrates confidence scores using historical feedback."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._platt_model: LogisticRegression | None = None
        self._isotonic_model: IsotonicRegression | None = None
        self._weights: dict[str, float] = {
            "retrieval": 0.4,
            "rerank": 0.3,
            "generation": 0.2,
            "completeness": 0.1
        }
    
    def aggregate_scores(self, raw: RawScores) -> float:
        """Aggregate raw scores into raw confidence."""
        
        # Retrieval: weighted average of grades, boost for top docs
        if raw.retrieval_grades:
            top_grades = sorted(raw.retrieval_grades, reverse=True)[:3]
            retrieval_score = (
                0.6 * np.mean(raw.retrieval_grades) +
                0.4 * np.mean(top_grades)
            )
        else:
            retrieval_score = 0.0
        
        # Reranker: weighted by position
        if raw.reranker_scores:
            weights = [1.0 / (i + 1) for i in range(len(raw.reranker_scores))]
            rerank_score = np.average(raw.reranker_scores, weights=weights)
        else:
            rerank_score = 0.0
        
        # Weighted combination
        raw_confidence = (
            self._weights["retrieval"] * retrieval_score +
            self._weights["rerank"] * rerank_score +
            self._weights["generation"] * raw.generation_coherence +
            self._weights["completeness"] * raw.retrieval_completeness
        )
        
        return min(1.0, max(0.0, raw_confidence))
    
    async def calibrate(
        self, 
        raw: RawScores,
        method: str = "isotonic"  # "platt" | "isotonic" | "histogram"
    ) -> CalibrationResult:
        """Apply calibration to raw confidence scores."""
        
        raw_confidence = self.aggregate_scores(raw)
        
        # Load calibration models (cached, refreshed weekly)
        if method == "isotonic":
            calibrated = await self._calibrate_isotonic(raw_confidence)
        elif method == "platt":
            calibrated = await self._calibrate_platt(raw_confidence)
        else:
            calibrated = raw_confidence
        
        # Calculate confidence interval
        interval = self._bootstrap_interval(raw, calibrated)
        
        return CalibrationResult(
            raw_confidence=raw_confidence,
            calibrated_confidence=calibrated,
            confidence_interval_95=interval,
            calibration_method=method,
            component_scores={
                "retrieval": raw.retrieval_grades[0] if raw.retrieval_grades else 0.0,
                "rerank": raw.reranker_scores[0] if raw.reranker_scores else 0.0,
                "generation": raw.generation_coherence,
                "completeness": raw.retrieval_completeness
            },
            is_calibrated=method in ("isotonic", "platt"),
            calibration_error=None  # Calculated during model training
        )
    
    async def _calibrate_isotonic(self, raw: float) -> float:
        """Apply isotonic regression calibration."""
        if self._isotonic_model is None:
            self._isotonic_model = await self._load_isotonic_model()
        
        if self._isotonic_model is None:
            return raw
        
        return self._isotonic_model.predict([raw])[0]
    
    def _bootstrap_interval(
        self, 
        raw: RawScores, 
        calibrated: float,
        n_bootstrap: int = 100
    ) -> tuple[float, float]:
        """Calculate 95% confidence interval via bootstrap."""
        
        # Simplified: use component variance as proxy
        scores = [
            *raw.retrieval_grades,
            *raw.reranker_scores,
            [raw.generation_coherence],
            [raw.retrieval_completeness]
        ]
        
        flat_scores = [s for sublist in scores for s in sublist]
        if not flat_scores:
            return (calibrated - 0.1, calibrated + 0.1)
        
        std = np.std(flat_scores)
        margin = 1.96 * std  # 95% CI
        
        return (
            max(0.0, calibrated - margin),
            min(1.0, calibrated + margin)
        )
```

#### 3.5.3 UI Signaling

```python
# app/schemas/confidence.py (NEW)

from pydantic import BaseModel, Field
from typing import Literal


class ConfidenceDisplay(BaseModel):
    """Frontend-facing confidence signal."""
    
    level: Literal["high", "medium", "low"] = Field(
        description="Human-readable confidence level"
    )
    
    score: float = Field(
        ge=0.0, le=1.0,
        description="Calibrated confidence score"
    )
    
    confidence_interval: tuple[float, float] = Field(
        description="95% confidence interval"
    )
    
    reasoning: str | None = Field(
        default=None,
        description="Brief explanation of confidence assessment"
    )
    
    display_hint: Literal["checkmark", "warning", "info"] = Field(
        description="Visual indicator for UI"
    )


def format_confidence_for_ui(calibrated: CalibrationResult) -> ConfidenceDisplay:
    """Convert calibration result to frontend-friendly format."""
    
    if calibrated.calibrated_confidence >= 0.8:
        level = "high"
        display_hint = "checkmark"
        reasoning = "High confidence: multiple strong sources support this answer."
    elif calibrated.calibrated_confidence >= 0.6:
        level = "medium"
        display_hint = "info"
        reasoning = "Medium confidence: some supporting sources, but limited evidence."
    else:
        level = "low"
        display_hint = "warning"
        reasoning = "Low confidence: limited or weak sources. Answer may need verification."
    
    return ConfidenceDisplay(
        level=level,
        score=round(calibrated.calibrated_confidence, 2),
        confidence_interval=(
            round(calibrated.confidence_interval_95[0], 2),
            round(calibrated.confidence_interval_95[1], 2)
        ),
        reasoning=reasoning,
        display_hint=display_hint
    )
```

#### 3.5.4 Monitoring

```python
# app/services/confidence_monitoring.py (NEW)

from dataclasses import dataclass
import numpy as np


@dataclass
class CalibrationMetrics:
    """Ongoing calibration quality metrics."""
    ece: float  # Expected Calibration Error
    nll: float  # Negative Log Likelihood
    brier_score: float  # Brier Score
    num_samples: int
    calibration_timestamp: datetime


async def calculate_calibration_metrics(
    db: AsyncSession,
    lookback_days: int = 7
) -> CalibrationMetrics:
    """
    Calculate calibration metrics over recent feedback.
    Run daily and store for monitoring dashboards.
    """
    
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    
    # Get all predictions with actual outcomes
    query = select(
        Message.extra_metadata["predicted_confidence"].astext.cast(Float),
        UserFeedback.rating
    ).join(
        UserFeedback, UserFeedback.message_id == Message.id
    ).where(
        Message.created_at >= cutoff,
        UserFeedback.rating.isnot(None)
    )
    
    results = await db.execute(query)
    rows = results.all()
    
    if len(rows) < 100:
        raise ValueError(f"Insufficient samples for calibration metrics: {len(rows)}")
    
    predictions = np.array([float(r[0]) for r in rows])
    outcomes = np.array([r[1] >= 3 for r in rows])  # rating >= 3 is "correct"
    
    # Calculate ECE with 10 bins
    ece = calculate_ece(predictions, outcomes, n_bins=10)
    
    # Calculate Brier Score
    brier = np.mean((predictions - outcomes) ** 2)
    
    # Calculate NLL
    nll = -np.mean(
        outcomes * np.log(predictions + 1e-10) + 
        (1 - outcomes) * np.log(1 - predictions + 1e-10)
    )
    
    return CalibrationMetrics(
        ece=ece,
        nll=nll,
        brier_score=brier,
        num_samples=len(rows),
        calibration_timestamp=datetime.utcnow()
    )


def calculate_ece(
    predictions: np.ndarray, 
    outcomes: np.ndarray, 
    n_bins: int = 10
) -> float:
    """Calculate Expected Calibration Error."""
    
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        bin_mask = (predictions >= bin_edges[i]) & (predictions < bin_edges[i + 1])
        if np.sum(bin_mask) == 0:
            continue
        
        bin_accuracy = np.mean(outcomes[bin_mask])
        bin_confidence = np.mean(predictions[bin_mask])
        bin_weight = np.sum(bin_mask) / len(predictions)
        
        ece += bin_weight * abs(bin_accuracy - bin_confidence)
    
    return ece
```

---

## 4. Data Architecture

### 4.1 PostgreSQL Schema Changes

#### 4.1.1 New Tables

```sql
-- Corrective-RAG: Document grades for self-correction
CREATE TABLE document_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL,
    relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    relevance_level VARCHAR(20) NOT NULL CHECK (relevance_level IN ('high', 'medium', 'low')),
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT unique_message_chunk UNIQUE (message_id, chunk_id)
);

CREATE INDEX ix_document_grades_message ON document_grades(message_id);
CREATE INDEX ix_document_grades_score ON document_grades(relevance_score);

-- User feedback for continual learning
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    feedback_type VARCHAR(20) NOT NULL CHECK (
        feedback_type IN ('thumbs_up', 'thumbs_down', 'correction', 'citation_click')
    ),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    
    -- Implicit signals
    time_spent_seconds INTEGER,
    source_clicks INTEGER,
    
    -- LLM-assessed scores
    retrieval_confidence FLOAT,
    answer_quality FLOAT,
    
    -- For corrections
    correction_text TEXT,
    
    extra_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_feedback_user ON user_feedback(user_id, created_at);
CREATE INDEX ix_feedback_quality ON user_feedback(retrieval_confidence, answer_quality);

-- Web search results for CRAG fallback
CREATE TABLE web_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    title VARCHAR(500),
    content TEXT,
    url TEXT,
    score FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_web_search_message ON web_search_results(message_id);

-- Calibration models (trained weekly)
CREATE TABLE calibration_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model_type VARCHAR(20) NOT NULL CHECK (model_type IN ('platt', 'isotonic')),
    weights JSONB NOT NULL,
    isotonic_mapping JSONB,  -- For isotonic: bin edges and values
    platt_coefficients JSONB, -- For platt: {a, b}
    ece_score FLOAT,
    num_training_samples INTEGER,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_calibration_user_active ON calibration_models(user_id, is_active);

-- Eval sets for retriever fine-tuning
CREATE TABLE eval_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_id UUID NOT NULL,
    query_text TEXT NOT NULL,
    relevant_memory_ids UUID[] DEFAULT '{}',
    irrelevant_memory_ids UUID[] DEFAULT '{}',
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    source VARCHAR(20) CHECK (source IN ('user_feedback', 'admin_curated', 'synthetic')),
    priority FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    used_for_training BOOLEAN DEFAULT false
);

CREATE INDEX ix_eval_examples_user ON eval_examples(user_id, used_for_training);
```

#### 4.1.2 Memory Model Changes

```sql
-- Add temporal embedding reference
ALTER TABLE memories ADD COLUMN temporal_vector_id UUID;

-- Add for tracking retriever model version
ALTER TABLE memories ADD COLUMN embedding_model_version VARCHAR(50);

-- Add index for time-based queries
CREATE INDEX ix_memories_user_captured_desc ON memories (user_id, captured_at DESC);
```

#### 4.1.3 Document Chunk Changes

```sql
-- Add temporal embedding vector
ALTER TABLE document_chunks ADD COLUMN temporal_embedding VECTOR(384);

-- Add embedding version for tracking
ALTER TABLE document_chunks ADD COLUMN embedding_version VARCHAR(50);
```

### 4.2 ChromaDB Schema Changes

```python
# app/retrieval/vector_store.py (MODIFY)

class ChromaCollectionConfig:
    """ChromaDB collection configuration."""
    
    # Standard semantic embedding
    SEMANTIC_EMBEDDING_DIM = 1536  # For text-embedding-3-small
    SEMANTIC_METADATA = ["chunk_id", "memory_id", "conversation_id", 
                        "captured_at", "source_type", "embedding_version"]
    
    # Temporal embedding (optional, added on demand)
    TEMPORAL_EMBEDDING_DIM = 384
    
    @staticmethod
    def get_collection_schema(
        name: str, 
        include_temporal: bool = False
    ) -> dict:
        """Generate collection configuration for ChromaDB."""
        
        schema = {
            "name": name,
            "metadata": {
                "description": f"Memory chunks for conversation {name}"
            }
        }
        
        if include_temporal:
            schema["get_or_create"] = True
        
        return schema
```

### 4.3 Redis Key Structure

```
# Redis key patterns for new SOTA features

# CRAG: Web search cache
web_search:{message_id} -> JSON (TTL: 1 hour)

# Confidence calibration cache
calibration:model:{user_id} -> JSON (TTL: 7 days)
calibration:metrics:{user_id}:{date} -> JSON (TTL: 30 days)

# Active learning queue
active_learning:queue:{user_id} -> Sorted Set (score: priority)

# Eval set storage
eval_set:{user_id}:{version} -> JSON (TTL: 14 days)

# Retriever model metadata
retriever:model:{user_id}:current -> JSON (version, path, metrics)

# Calibration feedback buffer
calibration:feedback_buffer:{user_id} -> List (capped at 1000)
```

### 4.4 New Collections/Indexes

```python
# ChromaDB: Temporal collections (per user, optional)

TEMPORAL_COLLECTION_PREFIX = "temporal_"

def get_temporal_collection_name(user_id: str) -> str:
    """Get temporal embedding collection name for user."""
    return f"{TEMPORAL_COLLECTION_PREFIX}{user_id}"

# ChromaDB: User-specific fine-tuned retriever collections

FINE_TUNED_COLLECTION_PREFIX = "finetuned_"

def get_finetuned_collection_name(user_id: str, version: str) -> str:
    """Get fine-tuned collection name."""
    return f"{FINE_TUNED_COLLECTION_PREFIX}{user_id}_{version}"
```

---

## 5. API Design

### 5.1 New Endpoints for SOTA Features

#### 5.1.1 Feedback API

```python
# app/api/v1/feedback.py (NEW)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackCreate(BaseModel):
    """Create feedback for an answer."""
    message_id: UUID
    feedback_type: str = Field(
        pattern="^(thumbs_up|thumbs_down|correction|citation_click)$"
    )
    rating: int | None = Field(default=None, ge=1, le=5)
    correction_text: str | None = None
    time_spent_seconds: int | None = None
    source_clicks: int | None = None


class FeedbackResponse(BaseModel):
    id: UUID
    message_id: UUID
    feedback_type: str
    rating: int | None
    created_at: datetime
    
    model_config = {"from_attributes": True}


@router.post("", response_model=FeedbackResponse)
async def create_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    feedback_service: FeedbackService = Depends()
) -> FeedbackResponse:
    """
    Submit feedback for an answer.
    
    This feedback is used for:
    - Continual learning (retriever fine-tuning)
    - Confidence calibration
    - Answer quality monitoring
    """
    
    result = await feedback_service.create(
        user_id=current_user.id,
        feedback_data=feedback
    )
    
    return result


@router.get("", response_model=list[FeedbackResponse])
async def list_feedback(
    message_id: UUID | None = None,
    feedback_type: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    feedback_service: FeedbackService = Depends()
) -> list[FeedbackResponse]:
    """List feedback submitted by the current user."""
    
    return await feedback_service.list(
        user_id=current_user.id,
        message_id=message_id,
        feedback_type=feedback_type,
        limit=limit,
        offset=offset
    )
```

#### 5.1.2 Confidence API

```python
# app/api/v1/confidence.py (NEW)

router = APIRouter(prefix="/confidence", tags=["Confidence"])


class ConfidenceResponse(BaseModel):
    """Confidence information for an answer."""
    message_id: UUID
    level: Literal["high", "medium", "low"]
    score: float = Field(ge=0.0, le=1.0)
    confidence_interval: tuple[float, float]
    reasoning: str | None
    display_hint: Literal["checkmark", "warning", "info"]
    component_scores: dict[str, float]
    
    model_config = {"from_attributes": True}


class CalibrationMetricsResponse(BaseModel):
    """Calibration quality metrics."""
    ece: float
    nll: float
    brier_score: float
    num_samples: int
    calculated_at: datetime


@router.get("/message/{message_id}", response_model=ConfidenceResponse)
async def get_message_confidence(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    confidence_service: ConfidenceService = Depends()
) -> ConfidenceResponse:
    """
    Get confidence information for a specific message/answer.
    
    Returns calibrated confidence with:
    - Overall level (high/medium/low)
    - Calibrated score (0-1)
    - 95% confidence interval
    - Component breakdown
    """
    
    return await confidence_service.get_for_message(
        user_id=current_user.id,
        message_id=message_id
    )


@router.get("/metrics", response_model=CalibrationMetricsResponse)
async def get_calibration_metrics(
    current_user: User = Depends(get_current_user),
    confidence_service: ConfidenceService = Depends()
) -> CalibrationMetricsResponse:
    """
    Get calibration quality metrics for the current user.
    
    Returns Expected Calibration Error (ECE), Brier Score, and NLL
    computed over the last 7 days of feedback.
    """
    
    return await confidence_service.get_metrics(
        user_id=current_user.id
    )
```

#### 5.1.3 Temporal Query API

```python
# app/api/v1/temporal.py (NEW)

router = APIRouter(prefix="/temporal", tags=["Temporal"])


class TemporalQueryRequest(BaseModel):
    """Query with temporal preferences."""
    query: str
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    weight_mode: Literal["recency", "historical", "uniform"] = "recency"
    decay_factor: float = Field(default=0.95, ge=0.1, le=0.99)


class TemporalQueryResponse(BaseModel):
    """Results with temporal scoring."""
    chunks: list[TemporalChunkResult]
    query_interpretation: dict
    total_found: int


@router.post("/query", response_model=TemporalQueryResponse)
async def temporal_query(
    request: TemporalQueryRequest,
    current_user: User = Depends(get_current_user),
    temporal_service: TemporalRetrievalService = Depends()
) -> TemporalQueryResponse:
    """
    Query with temporal awareness.
    
    Examples:
    - "What did I read about RAG last week?"
    - "Notes from March 2024"
    - "Before my trip to Japan"
    """
    
    return await temporal_service.query(
        user_id=current_user.id,
        request=request
    )
```

#### 5.1.4 Active Learning API (Admin)

```python
# app/api/v1/active_learning.py (NEW)

router = APIRouter(prefix="/active-learning", tags=["Active Learning"])


class ActiveLearningCandidateResponse(BaseModel):
    """Query candidate for retriever improvement."""
    query_id: UUID
    query_text: str
    current_confidence: float
    selection_reason: str
    priority: float
    created_at: datetime


@router.get("/candidates", response_model=list[ActiveLearningCandidateResponse])
async def get_active_learning_candidates(
    strategy: Literal["uncertainty", "diversity", "margin"] = "uncertainty",
    limit: int = Query(default=100, le=500),
    current_user: User = Depends(get_current_user),
    active_learning_service: ActiveLearningService = Depends()
) -> list[ActiveLearningCandidateResponse]:
    """
    Get queries selected for active learning.
    
    These queries have low retrieval confidence and are good candidates
    for retriever improvement through fine-tuning.
    """
    
    return await active_learning_service.get_candidates(
        user_id=current_user.id,
        strategy=strategy,
        limit=limit
    )


@router.post("/eval-set")
async def trigger_eval_set_generation(
    current_user: User = Depends(get_current_user),
    active_learning_service: ActiveLearningService = Depends()
) -> dict:
    """
    Trigger generation of eval set for retriever fine-tuning.
    
    Creates a new eval set from recent user feedback.
    """
    
    eval_path = await active_learning_service.create_eval_set(
        user_id=current_user.id
    )
    
    return {"eval_set_path": eval_path, "status": "created"}
```

### 5.2 Request/Response Schemas

#### 5.2.1 CRAG-Enhanced Chat Response

```python
# app/schemas/chat.py (MODIFY)

class ChatMessageResponse(BaseModel):
    """Enhanced chat message with CRAG metadata."""
    
    # Existing fields
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    
    # New CRAG fields
    retrieval_grades: list[dict] | None = None
    web_search_triggered: bool = False
    web_results: list[WebResult] | None = None
    query_transformed: bool = False
    transformed_query: str | None = None
    
    # Confidence calibration
    confidence: ConfidenceDisplay | None = None
    
    # Multi-hop (if applicable)
    is_multi_hop: bool = False
    sub_queries: list[str] | None = None
    hop_count: int | None = None
    
    model_config = {"from_attributes": True}


class WebResult(BaseModel):
    """Web search result for CRAG fallback."""
    title: str
    content: str
    url: str
    relevance_score: float
```

### 5.3 Breaking Changes (if any)

| Change | Type | Migration Path |
|--------|------|----------------|
| `ChatMessageResponse` gains new nullable fields | Additive | Non-breaking, frontend ignores unknown fields |
| `AgentState` TypedDict gains new fields | Additive | Non-breaking, defaults handled |
| ChromaDB collections gain new metadata | Additive | Non-breaking, backwards compatible |

**No breaking changes.** All additions are backward-compatible.

---

## 6. Infrastructure Requirements

### 6.1 New Services Needed

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NEW INFRASTRUCTURE COMPONENTS                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. WEB SEARCH FALLBACK SERVICE                                         │
│     ┌──────────────────────────────────────────────────────────────┐   │
│     │  Tavily API (recommended)                                     │   │
│     │  - $15/mo for 10,000 searches                               │   │
│     │  - Or self-hosted: SerpAPI, DuckDuckGo, Brave Search        │   │
│     │                                                              │   │
│     │  Configuration:                                              │   │
│     │  TAVILY_API_KEY=sk-...                                      │   │
│     │  WEB_SEARCH_PROVIDER=tavily  # tavily | serpapi | brave     │   │
│     └──────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  2. CALIBRATION MODEL STORAGE                                          │
│     ┌──────────────────────────────────────────────────────────────┐   │
│     │  Local filesystem (for MVP):                                 │   │
│     │  /models/calibration/{user_id}/                             │   │
│     │    ├── isotonic_model.pkl                                   │   │
│     │    └── metrics.json                                          │   │
│     │                                                              │   │
│     │  Future: S3/MinIO for multi-node:                           │   │
│     │  s3://orivory-models/calibration/{user_id}/               │   │
│     └──────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  3. FINE-TUNED RETRIEVER MODELS                                        │
│     ┌──────────────────────────────────────────────────────────────┐   │
│     │  Storage: ~500MB per user model                             │   │
│     │  - Sentence-transformers model                             │   │
│     │  - Quantized version for inference                         │   │
│     │                                                              │   │
│     │  Compute for fine-tuning:                                   │   │
│     │  - GPU recommended (A10G or similar)                       │   │
│     │  - CPU fallback: ~4 hours per fine-tune                    │   │
│     │                                                              │   │
│     │  /models/retriever/{user_id}/v{timestamp}/                 │   │
│     └──────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  4. TEMPORAL EMBEDDING COMPUTE                                          │
│     ┌──────────────────────────────────────────────────────────────┐   │
│     │  Optional: Separate embedding model for temporal context     │   │
│     │  - TimeLM or similar                                       │   │
│     │  - Or: append temporal tokens to existing embeddings        │   │
│     │                                                              │   │
│     │  Recommendation: Start without temporal embeddings          │   │
│     │  Add later if time-filtered queries show low quality        │   │
│     └──────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Scaling Considerations

| Component | Current | SOTA Enhanced | Scaling Strategy |
|-----------|---------|---------------|------------------|
| **ChromaDB** | Single-node | Multi-collection per user | Shard by user_id hash |
| **PostgreSQL** | 10 + 20 overflow | +3 new tables, indexes | Connection pool increase |
| **Redis** | 20 pool max | + calibration cache, queues | Redis Cluster for sharding |
| **LLM Calls** | ~2 per query | ~4-6 per query | Rate limiting, caching |
| **Embedding Storage** | 1536d vectors | + 384d temporal (optional) | Archive old embeddings |

### 6.3 Cost Projections

#### 6.3.1 LLM Costs (per user per month)

| Feature | Calls/Query | Queries/Day | Cost/Query | Monthly Cost |
|---------|-------------|-------------|------------|-------------|
| **Current (baseline)** | 3 | 20 | $0.002 | $1.20 |
| **+ CRAG Grading** | +1 | 20 | $0.0005 | +$0.30 |
| **+ Web Search (fallback)** | +2 | 2 (avg) | $0.003 | +$0.36 |
| **+ Multi-hop (complex)** | +2 | 2 | $0.0005 | +$0.06 |
| **+ Calibration checks** | +1 | 20 | $0.0002 | +$0.12 |
| **Total Addition** | | | | **+$0.84/mo** |

#### 6.3.2 Storage Costs

| Resource | Current | SOTA Addition | Monthly Cost |
|----------|---------|--------------|--------------|
| **ChromaDB vectors** | ~100K × 1536d | + 100K × 384d (temporal) | +$2.50 |
| **Calibration models** | 0 | ~1MB per user | +$0.05 |
| **Fine-tuned models** | 0 | ~500MB per active user | +$5.00 |
| **PostgreSQL (new tables)** | ~1GB | +500MB | +$0.25 |

#### 6.3.3 External API Costs

| Service | Usage | Monthly Cost |
|---------|-------|-------------|
| **Tavily (web search)** | 10K searches/mo | $15.00 |
| **Jina Reranker** | Current usage | (already in stack) |
| **Total External** | | **$15.00/mo** |

---

## 7. Security & Privacy

### 7.1 Data Isolation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DATA ISOLATION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User A's Data:                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  memories_A → ChromaDB collection: memories_{user_hash_A}        │  │
│  │  feedback_A → PostgreSQL: user_id = A                            │  │
│  │  models_A → /models/retriever/{user_hash_A}/                    │  │
│  │  calibration_A → Redis: calibration:model:{user_hash_A}         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Key Isolation Points:                                                  │
│  • All vectors scoped to user-specific collections                     │
│  • Feedback queries always filter by user_id                            │
│  • Model paths derived from hashed user_id (not raw)                    │
│  • Redis keys namespaced by user hash                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 API Security

```python
# app/api/v1/feedback.py (ADD)

from fastapi.security import HTTPBearer
from app.middleware.rate_limiter import RateLimitExceeded

# Enhanced rate limiting for feedback endpoints
FEEDBACK_RATE_LIMIT = "20/minute"  # Per user

@router.post("", response_model=FeedbackResponse)
@rate_limit(limit_key="feedback", rate=FEEDBACK_RATE_LIMIT)
async def create_feedback(...):
    """Feedback submission with rate limiting."""
    ...

# Sanitize correction text to prevent prompt injection
def sanitize_correction(text: str) -> str:
    """Remove potential prompt injection from corrections."""
    # Remove common injection patterns
    dangerous_patterns = [
        r"ignore previous instructions",
        r"ignore all previous",
        r"disregard.*instructions",
    ]
    for pattern in dangerous_patterns:
        text = re.sub(pattern, "[removed]", text, flags=re.IGNORECASE)
    return text.strip()
```

### 7.3 Compliance Considerations

| Concern | Mitigation |
|---------|-----------|
| **User feedback storage** | User consent on first feedback prompt |
| **Fine-tuning on user data** | Opt-in only, clear explanation |
| **Web search fallback** | User-query never logged by Tavily (if configured) |
| **Calibration model sharing** | Models stay local, never shared |
| **Data retention** | Feedback auto-deleted after 90 days (configurable) |

---

## 8. Monitoring & Observability

### 8.1 New Metrics for SOTA Features

```python
# app/observability/metrics.py (APPEND)

from prometheus_client import Counter, Histogram, Gauge


# CRAG Metrics
CRAG_RETRIEVAL_GRADES = Histogram(
    "crag_retrieval_grade_score",
    "Retrieval grade scores from CRAG",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

CRAG_WEB_SEARCH_TRIGGERED = Counter(
    "crag_web_search_total",
    "Number of times web search fallback was triggered",
    ["reason"]  # low_relevance | medium_relevance
)

CRAG_QUERY_TRANSFORMED = Counter(
    "crag_query_transform_total",
    "Number of times query was transformed for retry"
)

# Multi-hop Metrics
MULTIHOP_HOP_COUNT = Histogram(
    "multihop_hop_count",
    "Distribution of hop counts in multi-hop queries",
    buckets=[1, 2, 3, 4, 5]
)

MULTIHOP_BRANCH_COUNT = Histogram(
    "multihop_branch_count",
    "Distribution of parallel branches in multi-hop",
    buckets=[1, 2, 3, 4, 5]
)

# Calibration Metrics
CALIBRATION_RAW_CONFIDENCE = Histogram(
    "calibration_raw_confidence",
    "Raw confidence scores before calibration",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

CALIBRATION_ERROR = Gauge(
    "calibration_ece",
    "Expected Calibration Error (updated daily)",
    ["user_id_hash"]  # Anonymized
)

CALIBRATION_FEEDBACK_BUFFER = Gauge(
    "calibration_feedback_buffer_size",
    "Number of feedback samples awaiting calibration",
    ["user_id_hash"]
)

# Temporal Metrics
TEMPORAL_QUERY_COUNT = Counter(
    "temporal_query_total",
    "Number of queries with temporal constraints",
    ["weight_mode"]  # recency | historical | uniform
)

TEMPORAL_RETRIEVAL_SCORE_DELTA = Histogram(
    "temporal_retrieval_score_delta",
    "Difference between semantic and temporal scores",
    buckets=[-1.0, -0.5, 0.0, 0.5, 1.0]
)

# Continual Learning Metrics
ACTIV_LEARNING_CANDIDATES = Gauge(
    "active_learning_candidates",
    "Number of queries pending active learning selection",
    ["user_id_hash"]
)

RETRIEVER_FINETUNE_QUEUED = Counter(
    "retriever_finetune_queued_total",
    "Number of retriever fine-tuning jobs queued"
)

RETRIEVER_FINETUNE_COMPLETED = Counter(
    "retriever_finetune_completed_total",
    "Number of retriever fine-tuning jobs completed",
    ["status"]  # success | failure
)

RETRIEVER_FINETUNE_DURATION = Histogram(
    "retriever_finetune_duration_seconds",
    "Time to complete retriever fine-tuning",
    buckets=[600, 1200, 1800, 3600, 7200]  # 10m to 2h
)
```

### 8.2 Alert Thresholds

```python
# app/observability/alerts.py (NEW)

ALERT_RULES = {
    # CRAG Alerts
    "crag_high_relevance_rate_low": {
        "condition": "crag_web_search_total > 0.3 * chat_queries_total",
        "severity": "warning",
        "message": "Web search triggered in >30% of queries - possible retrieval quality degradation"
    },
    
    "crag_grade_score_low": {
        "condition": "rate(crag_retrieval_grade_score_sum[5m]) / rate(crag_retrieval_grade_score_count[5m]) < 0.4",
        "severity": "critical",
        "message": "Average retrieval grade score below 0.4"
    },
    
    # Calibration Alerts
    "calibration_ece_high": {
        "condition": "calibration_ece > 0.15",
        "severity": "warning",
        "message": "ECE above 15% - calibration may need retraining"
    },
    
    "calibration_buffer_full": {
        "condition": "sum(calibration_feedback_buffer_size) > 5000",
        "severity": "info",
        "message": "Feedback buffer filling up - calibration model update needed"
    },
    
    # Multi-hop Alerts
    "multihop_hop_count_high": {
        "condition": "rate(multihop_hop_count_sum[5m]) / rate(multihop_hop_count_count[5m]) > 3.5",
        "severity": "warning",
        "message": "Average hop count > 3.5 - possible infinite loop risk"
    },
    
    # Retriever Fine-tuning
    "finetune_failure_rate": {
        "condition": "rate(retriever_finetune_completed_total{status='failure'}[1h]) / rate(retriever_finetune_queued_total[1h]) > 0.1",
        "severity": "critical",
        "message": "Retriever fine-tuning failure rate > 10%"
    },
}
```

### 8.3 Dashboard Requirements

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEW DASHBOARD PANELS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. CRAG PERFORMANCE                                                   │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │  • Retrieval grade distribution (histogram)                 │     │
│     │  • Web search fallback rate (gauge + trend)                │     │
│     │  • Query transformation rate (counter + trend)             │     │
│     │  • Grade latency (p50, p95, p99)                          │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  2. CONFIDENCE CALIBRATION                                             │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │  • ECE over time (line chart)                              │     │
│     │  • Raw vs calibrated confidence scatter                     │     │
│     │  • Confidence level distribution (pie chart)                │     │
│     │  • Calibration buffer size (gauge)                         │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  3. MULTI-HOP ANALYSIS                                                 │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │  • Hop count distribution (bar chart)                    │     │
│     │  • Multi-hop query rate (% of total)                      │     │
│     │  • Branch count distribution (for parallel queries)       │     │
│     │  • Multi-hop answer quality (vs single-hop baseline)       │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  4. CONTINUAL LEARNING                                                 │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │  • Active learning candidates queue depth                  │     │
│     │  • Fine-tuning job status (queued/running/completed)        │     │
│     │  • Fine-tuning duration (histogram)                        │     │
│     │  • Pre/post fine-tuning retrieval quality delta              │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  5. TEMPORAL RETRIEVAL                                                 │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │  • Temporal query rate (% of total)                        │     │
│     │  • Weight mode distribution (pie)                          │     │
│     │  • Temporal score delta (semantic vs temporal re-rank)     │     │
│     │  • Time-range filter hit rate                               │     │
│     └─────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Implementation Phases

### Phase 1: Corrective-RAG (Week 1-2)

**Objective:** Implement self-correcting retrieval with web fallback

#### Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `grade_docs_agent` node | 2 days | None |
| Add retrieval grader prompt | 0.5 day | None |
| Implement `route_after_grade_docs` routing | 1 day | grade_docs_agent |
| Create web search agent with Tavily | 2 days | None |
| Add `transform_query` agent | 1.5 days | None |
| Wire CRAG nodes into LangGraph | 1 day | All above |
| Add `web_search_results` table | 0.5 day | None |
| Add CRAG metrics to observability | 0.5 day | None |
| Write CRAG-specific tests | 1 day | All above |
| **Total** | **10 days** | |

#### Deliverables

- [ ] Retrieval grader with 0-1 score output
- [ ] Web search fallback triggered on medium relevance
- [ ] Query transformation on low relevance
- [ ] CRAG metrics in Prometheus
- [ ] Unit tests for routing logic

---

### Phase 2: Confidence UI (Week 1-2) *(parallel with Phase 1)*

**Objective:** Surface confidence signals to users

#### Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `ConfidenceScore` dataclass | 0.5 day | None |
| Implement `aggregate_scores()` | 1 day | None |
| Create `calibration_service` | 1.5 days | None |
| Add calibration API endpoints | 1 day | ConfidenceScore |
| Create `ConfidenceDisplay` schema | 0.5 day | None |
| Add frontend SSE confidence event | 1 day | API endpoints |
| Create calibration metrics calculation | 1 day | Feedback table |
| Add calibration to Grafana | 0.5 day | Metrics |
| Write calibration tests | 1 day | All above |
| **Total** | **8 days** | |

#### Deliverables

- [ ] `/api/v1/confidence/message/{id}` endpoint
- [ ] `/api/v1/confidence/metrics` endpoint
- [ ] Confidence display in SSE `done` event
- [ ] ECE tracking in Prometheus
- [ ] Calibration dashboard panel

---

### Phase 3: Temporal Memory (Week 3-4)

**Objective:** Add time-aware retrieval

#### Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `TemporalQuery` and `TemporalRetrievalResult` | 0.5 day | None |
| Implement `compute_temporal_score()` | 1 day | None |
| Create `temporal_retriever` service | 1.5 days | TemporalQuery |
| Add temporal query parser | 1 day | None |
| Modify `retrieval_agent` to use temporal | 1 day | temporal_retriever |
| Add `temporal_query` API endpoint | 1 day | TemporalQuery |
| Add temporal indexes to Postgres | 0.5 day | None |
| Add temporal metrics | 0.5 day | None |
| Write temporal retrieval tests | 1 day | All above |
| **Total** | **8.5 days** | |

#### Deliverables

- [ ] Temporal weighting in retrieval
- [ ] Natural language time parsing ("last week", "March 2024")
- [ ] `/api/v1/temporal/query` endpoint
- [ ] Temporal metrics in Prometheus
- [ ] Tests with mocked time scenarios

---

### Phase 4: Multi-hop Reasoning (Week 5-8)

**Objective:** Support complex multi-step queries

#### Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `MultiHopState` extension | 0.5 day | None |
| Implement `detect_multi_hop_complexity()` | 1 day | None |
| Create `generate_subquery` prompt | 0.5 day | None |
| Implement `generate_next_hop` agent | 2 days | MultiHopState |
| Add hop counter and depth limiting | 1 day | None |
| Implement `should_continue_hopping()` | 0.5 day | None |
| Create branch-solve-merge pattern | 2 days | None |
| Modify LangGraph for multi-hop | 2 days | All above |
| Add multi-hop metrics | 0.5 day | None |
| Write multi-hop tests | 2 days | All above |
| **Total** | **12.5 days** | |

#### Deliverables

- [ ] Automatic multi-hop detection
- [ ] Next-hop query generation
- [ ] Branch-solve-merge for parallel sub-questions
- [ ] Hop count limiting (max 3)
- [ ] Multi-hop metrics in Prometheus
- [ ] Integration tests with complex queries

---

### Phase 5: Continual Learning (Week 9-12)

**Objective:** Feedback-driven retriever improvement

#### Tasks

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `UserFeedback` model | 0.5 day | None |
| Create `FeedbackService` | 1.5 days | UserFeedback |
| Add feedback API endpoints | 1 day | FeedbackService |
| Implement eval set curator | 2 days | UserFeedback |
| Create `ActiveLearningSelector` | 2 days | None |
| Implement `fine_tune_retriever` Celery task | 3 days | None |
| Add `calibration_models` table | 0.5 day | None |
| Implement calibration training | 2 days | None |
| Add Celery Beat schedule for weekly retraining | 1 day | fine_tune_retriever |
| Add active learning API | 1 day | ActiveLearningSelector |
| Write continual learning tests | 2 days | All above |
| **Total** | **16.5 days** | |

#### Deliverables

- [ ] User feedback collection API
- [ ] Eval set curation from feedback
- [ ] Active learning candidate selection
- [ ] Retriever fine-tuning pipeline
- [ ] Weekly auto-retraining via Celery Beat
- [ ] Calibration model training and serving
- [ ] End-to-end continual learning integration tests

---

### Implementation Timeline Summary

```
Week 1  │██████████████│██████████████│██████████████│██████████████│
        │   Phase 1   │   Phase 2    │              │               │
        │  (CRAG - 5d) │ (Conf - 4d)  │              │               │
Week 2  │██████████████│██████████████│██████████████│██████████████│
        │   Phase 1   │   Phase 2    │   Phase 3    │               │
        │  (CRAG - 5d) │ (Conf - 4d)  │ (Temp - 4d)  │               │
Week 3  │██████████████│██████████████│██████████████│██████████████│
        │   Phase 3   │              │   Phase 4    │               │
        │ (Temp - 4d) │              │ (Multi - 6d) │               │
Week 4  │██████████████│██████████████│██████████████│██████████████│
        │   Phase 3   │   Phase 4    │   Phase 4    │   Phase 4    │
        │ (Temp - 4d) │ (Multi - 6d) │ (Multi - 6d) │ (Multi - 1d) │
Week 5  │██████████████│██████████████│██████████████│██████████████│
        │   Phase 4   │   Phase 5    │   Phase 5    │               │
        │ (Multi - 6d)│ (Learn - 5d) │ (Learn - 5d) │               │
Week 6  │██████████████│██████████████│██████████████│██████████████│
        │   Phase 5   │   Phase 5    │   Phase 5    │   Phase 5    │
        │ (Learn - 5d)│ (Learn - 5d) │ (Learn - 5d) │ (Learn - 1d) │
Week 7  │██████████████│██████████████│██████████████│██████████████│
        │   Phase 5   │   Testing    │   Testing    │               │
        │ (Learn - 1d)│   & Polish   │   & Polish   │               │
Week 8  │██████████████│██████████████│██████████████│██████████████│
        │   Testing   │   & Polish   │   & Polish   │   Launch     │
        │   & Polish  │              │              │               │
```

---

## Appendix A: Configuration Additions

```python
# app/config.py (APPEND)

# SOTA Feature Flags
ENABLE_CRAG: bool = True
ENABLE_TEMPORAL_RETRIEVAL: bool = True
ENABLE_MULTIHOP_REASONING: bool = False  # Compute-heavy, enable gradually
ENABLE_CONTINUAL_LEARNING: bool = False  # Requires user opt-in
ENABLE_CONFIDENCE_CALIBRATION: bool = True

# CRAG Settings
WEB_SEARCH_PROVIDER: Literal["tavily", "serpapi", "brave", "none"] = "tavily"
WEB_SEARCH_FALLBACK_THRESHOLD: float = 0.3  # Trigger web search if avg grade < 0.3
WEB_SEARCH_QUERY_TRANSFORM_THRESHOLD: float = 0.1  # Transform if avg grade < 0.1
MAX_WEB_RESULTS: int = 5

# Temporal Settings
TEMPORAL_WEIGHT_MODE: Literal["recency", "historical", "uniform"] = "recency"
TEMPORAL_DECAY_FACTOR: float = 0.95  # Half-life in 30 days
TEMPORAL_VECTOR_DIMENSIONS: int = 384

# Multi-hop Settings
MAX_HOPS: int = 3
MULTIHOP_COMPLEXITY_THRESHOLD: int = 2  # Indicators to trigger multi-hop
PARALLEL_BRANCH_LIMIT: int = 3

# Continual Learning Settings
FEEDBACK_RETENTION_DAYS: int = 90
MIN_FEEDBACK_FOR_EVAL_SET: int = 100
MIN_NEW_FEEDBACK_FOR_RETRAIN: int = 50
RETRAINING_SCHEDULE_CRON: str = "0 2 * * 0"  # Weekly Sunday 2 AM

# Calibration Settings
CALIBRATION_METHOD: Literal["isotonic", "platt", "histogram"] = "isotonic"
CALIBRATION_METRICS_LOOKBACK_DAYS: int = 7
CALIBRATION_BUFFER_MAX_SIZE: int = 1000
```

## Appendix B: API Migration Guide

### No Breaking Changes

All SOTA additions are backward-compatible:

1. **New endpoints** are opt-in (not required for existing clients)
2. **New fields** in responses are nullable (defaults handled)
3. **New SSE events** include type discriminator for safe parsing

### Optional Migration for Clients

To take advantage of confidence signals:

```javascript
// Client-side: Parse new SSE events
const eventSource = new EventSource('/api/v1/chat/conversations/...');

eventSource.addEventListener('done', (event) => {
    const data = JSON.parse(event.data);
    
    // Access confidence if available
    if (data.confidence) {
        showConfidenceIndicator(data.confidence.level);
    }
});
```

---

*Document generated for Orivory v2.0 SOTA implementation planning.*
*Maintained by: Engineering Team*
*Next Review: Before Phase 1 kickoff*
