# Orivory SOTA Technical Specification v1.0

## RAG-native Answer Engine for Researchers: State-of-the-Art Enhancement Plan

---

## 1. Executive Summary

This document defines the technical specification for implementing five state-of-the-art (SOTA) retrieval and generation techniques into the Orivory platform. These enhancements target significant improvements in answer accuracy, temporal reasoning, multi-hop question answering, continuous learning from user feedback, and confidence calibration.

### 1.1 Current System Baseline

Orivory currently operates with:
- **21-node LangGraph workflow** for answer generation (includes CRAG, Temporal, HyDE, Multi-hop)
- **Hybrid retrieval**: BM25 + Vector search with Reciprocal Rank Fusion (RRF)
- **Jina-based reranking** for top-k document selection
- **Source attribution** from chunks to citations
- **Agent trace recording** for observability
- **CRAG self-critique** with web search fallback
- **Temporal memory** with sinusoidal encoding
- **Multi-hop reasoning** with EfficientRAG pattern

### 1.2 SOTA Techniques to Implement

| # | Technique | Primary Benefit | Paper/Source |
|---|-----------|----------------|--------------|
| 1 | **Corrective-RAG (CRAG)** | 36.6% accuracy improvement on PubHealth | Yan et al., arXiv 2401.15884 |
| 2 | **Temporal Memory (TimeR4)** | Time-filtered retrieval with recency weighting | TimeR4 + EM-LLM research |
| 3 | **Multi-hop Reasoning (EfficientRAG)** | 10x efficiency improvement | EMNLP 2024 |
| 4 | **Continual Learning (Pistis-RAG)** | Closed-loop retriever improvement | Pistis-RAG framework |
| 5 | **Confidence Calibration** | Calibrated uncertainty estimation | Platt scaling / Isotonic regression |

### 1.3 Implementation Priority Matrix

```
Impact →
Cost ↓          | High Impact     | Medium Impact    | Low Impact
----------------|-----------------|------------------|----------------
High Cost       | CRAG (P0)       | Multi-hop (P1)   | -
Medium Cost     | Temporal (P1)   | -                | -
Low Cost        | Calibration (P0)| Continual (P2)   | -
```

### 1.4 Expected Impact Summary

| Metric | Current | Post-Implementation | Improvement |
|--------|---------|-------------------|-------------|
| Answer Accuracy (PubHealth) | ~65% | ~90% | +36.6% |
| Multi-hop Recall | ~70% | ~95% | +25% |
| Retrieval Efficiency | baseline | 10x faster | 10x |
| Confidence Calibration Error | ~25% | <5% | 4x |
| User Feedback Loop | none | weekly | new capability |

---

## 2. Technique 1: Corrective-RAG (CRAG)

### 2.1 Research Background

**Paper**: "Corrective Retrieval Augmented Generation" - Yan et al., arXiv 2401.15884

**Key Findings:**
- A lightweight classifier can evaluate the quality of retrieved documents
- Three outcomes: Correct, Incorrect, Ambiguous
- For Incorrect/Ambiguous cases, web search fallback dramatically improves accuracy
- Decompose-then-recompose algorithm filters key information from noisy documents
- **36.6% accuracy improvement** on PubHealth benchmark over naive RAG

**Why It Matters for Orivory:**
Researchers frequently ask questions where the uploaded documents are insufficient. Current system retries retrieval up to 3 times using the same strategy. CRAG provides a principled fallback to external search and intelligent document refinement.

### 2.2 Implementation Design

#### 2.2.1 LangGraph Node Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    grade_docs_with_crag                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Classify each chunk: [correct, incorrect, ambiguous]      │  │
│  │  → LLM-based classifier with confidence scores              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Aggregate classification results:                        │  │
│  │  • Majority Correct (>60%): → internal_refinement        │  │
│  │  • Majority Incorrect (>60%): → web_search_fallback       │  │
│  │  • Majority Ambiguous: → decompose_recompose              │  │
│  │  • Mixed: weighted combination                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Output State Update:                                     │  │
│  │  • corrected_chunks: Refined document content              │  │
│  │  • correction_type: enum (correct, incorrect, ambiguous)  │  │
│  │  • crag_confidence: float [0, 1]                         │  │
│  │  • should_web_search: bool                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 Classifier Approach: Hybrid Strategy

We implement a **tiered classifier strategy**:

```
┌────────────────────────────────────────────────────┐
│              CRAG Classification Pipeline           │
├────────────────────────────────────────────────────┤
│                                                    │
│  Tier 1: Fast Heuristic Filter (no LLM call)      │
│  ├─ Check chunk-query keyword overlap              │
│  ├─ Check semantic similarity threshold (>0.7)      │
│  └─ If confident → return early                    │
│                                                    │
│  Tier 2: Lightweight LLM Classifier               │
│  ├─ Use smaller model (e.g., Haicu)                │
│  ├─ Single classification per chunk                │
│  └─ Cost ~0.001 per chunk                        │
│                                                    │
│  Tier 3: Heavyweight Classifier (if needed)       │
│  ├─ Full reasoning model                          │
│  └─ Only for ambiguous Tier 2 results             │
│                                                    │
└────────────────────────────────────────────────────┘
```

#### 2.2.3 CRAG System Prompt for Classification

```python
CRAG_CLASSIFIER_PROMPT = """You are a retrieval quality assessor for a research assistant.
Evaluate whether the retrieved document chunk helps answer the user's question.

Classification Definitions:
- "correct": Document contains information directly relevant to answering the question.
              Even if incomplete, the relevant portions can be used.
- "incorrect": Document contains information that CONTRADICTS the question's premise,
               or is about an entirely different topic. Should NOT be used.
- "ambiguous": Document MAY contain relevant information but:
                1. It's mixed with irrelevant content
                2. The relevant part requires extraction
                3. Confidence is low

Question: {query}

Document Chunk:
{chunk_content}

Respond with JSON:
{{
    "classification": "correct" | "incorrect" | "ambiguous",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "key_information": "extracted relevant portion if ambiguous"
}}
"""
```

#### 2.2.4 Web Search Integration

```python
class WebSearchFallback:
    """Fallback to external search when internal retrieval fails."""
    
    SUPPORTED_PROVIDERS = [
        "tavily",      # Primary: specialized for AI/RAG
        "serpapi",     # Google Search
        "duckduckgo",  # Privacy-preserving
    ]
    
    async def search(
        self, 
        query: str, 
        num_results: int = 5
    ) -> list[SearchResult]:
        # Provider selection logic
        # Rate limiting
        # Result deduplication
        # Snippet extraction
        pass
    
    def format_for_context(
        self, 
        results: list[SearchResult]
    ) -> list[dict]:
        """Format web results as chunks for downstream processing."""
        return [
            {
                "content": r.snippet,
                "source": r.url,
                "title": r.title,
                "type": "web_search",
                "source_attribution": f"[Web] {r.title}"
            }
            for r in results
        ]
```

#### 2.2.5 Decompose-Then-Recompose Algorithm

```python
async def decompose_recompose(
    chunk: dict,
    query: str,
    client: AsyncOpenAI
) -> dict:
    """
    Extract useful information from noisy/ambiguous chunks.
    """
    decompose_prompt = f"""
    Given the user question and document chunk, extract ONLY the parts
    relevant to answering the question.
    
    Question: {query}
    
    Document:
    {chunk['content']}
    
    Extract: sentences/passages that directly relate to the question.
    Discard: tangentially related or irrelevant content.
    """
    
    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": decompose_prompt}],
        temperature=0.0,
    )
    
    refined_content = response.choices[0].message.content
    
    return {
        **chunk,
        "content": refined_content,
        "was_decomposed": True,
        "original_length": len(chunk['content']),
        "refined_length": len(refined_content),
    }
```

### 2.3 Code Architecture

#### 2.3.1 New Components

```
app/
├── agents/
│   ├── crag_agent.py          # Main CRAG classification logic
│   ├── web_search_agent.py    # Web search fallback implementation
│   └── decompose_agent.py     # Decompose-then-recompose logic
├── retrieval/
│   ├── crag_classifier.py     # Lightweight classification models
│   └── web_search.py          # Web search provider integrations
└── graph/
    └── crag_builder.py        # CRAG-specific graph extensions
```

#### 2.3.2 Modified Components

| File | Changes |
|------|---------|
| `app/agents/state.py` | Add CRAG-related state fields |
| `app/agents/graph.py` | Add CRAG nodes and edges |
| `app/agents/routing.py` | Update routing logic for CRAG outcomes |
| `app/config.py` | Add CRAG configuration options |

#### 2.3.3 State Schema Extensions

```python
class AgentState(TypedDict, total=False):
    # ... existing fields ...
    
    # CRAG-specific fields
    crag_enabled: bool
    chunk_classifications: list[dict]  # [{chunk_id, classification, confidence}]
    correction_type: str  # "correct" | "incorrect" | "ambiguous"
    crag_confidence: float
    should_web_search: bool
    web_search_results: list[dict]
    corrected_chunks: list[dict]
    decomposition_applied: bool
```

#### 2.3.4 Configuration Options

```python
class Settings(BaseSettings):
    # CRAG Configuration
    crag_enabled: bool = True
    crag_classification_threshold: float = 0.6
    crag_use_web_fallback: bool = True
    crag_web_search_provider: str = "tavily"
    crag_max_web_results: int = 5
    crag_decompose_threshold: float = 0.4  # Ambiguous threshold
```

### 2.4 Evaluation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Accuracy Improvement** | +36% on PubHealth | Benchmark evaluation |
| **False Positive Rate** | <5% | Incorrect chunks marked as correct |
| **False Negative Rate** | <10% | Correct chunks marked as incorrect |
| **Latency Overhead** | <200ms | Per-query additional latency |
| **Web Search Trigger Rate** | 15-25% | Expected fallback frequency |
| **Cost Impact** | +$0.002/query | Additional LLM calls |

### 2.5 Implementation Plan

#### Phase 1: Foundation (Week 1-2)
- [ ] Implement `crag_agent.py` with basic classification
- [ ] Add CRAG state fields to `AgentState`
- [ ] Create initial system prompt for classification
- [ ] Unit tests for classifier

#### Phase 2: Integration (Week 3-4)
- [ ] Add CRAG node to LangGraph (`grade_docs_with_crag`)
- [ ] Update routing logic in `routing.py`
- [ ] Connect CRAG output to answer generation
- [ ] Integration tests

#### Phase 3: Web Search (Week 5-6)
- [ ] Implement `web_search_agent.py`
- [ ] Add Tavily/SERP API integration
- [ ] Format web results for context
- [ ] Fallback trigger mechanism

#### Phase 4: Decompose-Recompose (Week 7-8)
- [ ] Implement `decompose_agent.py`
- [ ] Refinement pipeline for ambiguous chunks
- [ ] A/B testing framework setup
- [ ] Performance benchmarking

**Effort Estimate**: 8 weeks, 1 full-stack engineer

---

## 3. Technique 2: Temporal Memory (TimeR4 + EM-LLM)

### 3.1 Research Background

**Concept**: Enable time-aware retrieval by indexing documents with timestamp metadata and enabling temporal reasoning during generation.

**How It Works:**
- Add temporal embeddings alongside semantic embeddings
- Query decomposition extracts time ranges from natural language
- Time-aware retrieval combines relevance with recency weighting
- Temporal reasoning enables "On March 15, you concluded..." style answers

**Why It Matters for Orivory:**
Researchers often ask questions like "What did I conclude about X last quarter?" or "What was the status of Y in January?" Current vector search ignores temporal ordering entirely.

### 3.2 Implementation Design

#### 3.2.1 Schema Additions

```python
# app/models/memory.py - Extensions

class Memory(Base):
    # ... existing fields ...
    
    # Temporal Memory fields
    temporal_embedding: Mapped[bytes | None] = mapped_column(
        "temporal_embedding", BYTEA, nullable=True
    )
    event_date: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
        # Explicit date for events vs captured_at (ingestion time)
    )
    temporal_features: Mapped[dict] = mapped_column(
        "temporal_features", JSONB, server_default="{}"
    )
    # {
    #     "recency_weight": 0.0-1.0,
    #     "decay_rate": 0.0-1.0,
    #     "temporal_precision": "day" | "week" | "month" | "year"
    # }

class DocumentChunk(Base):
    # ... existing fields ...
    
    temporal_features: Mapped[dict] = mapped_column(
        JSONB, server_default="{}"
    )
    # Same structure as Memory.temporal_features
```

#### 3.2.2 Temporal Embedding Generation

```python
# app/retrieval/temporal_embeddings.py

class TemporalEmbedder:
    """
    Generate embeddings that encode temporal context.
    
    Approach: Concatenate semantic embedding with time-aware
    positional encoding, similar to sinusoidal positional encoding
    in transformers but adapted for 1D time series.
    """
    
    def __init__(
        self,
        base_embedder: Embedder,
        time_encoder_dim: int = 64,
    ):
        self.base_embedder = base_embedder
        self.time_encoder_dim = time_encoder_dim
        self.time_encoder = TimeEncoder(dim=time_encoder_dim)
    
    async def embed_with_time(
        self,
        content: str,
        timestamp: datetime,
    ) -> np.ndarray:
        # Base semantic embedding
        semantic = await self.base_embedder.embed(content)
        
        # Time encoding
        time_features = self.time_encoder.encode(timestamp)
        
        # Project time to match embedding dimension
        time_projected = self.time_projector(time_features)
        
        # Combine: semantic + time (weighted by recency factor)
        recency_weight = self._compute_recency(timestamp)
        combined = semantic + recency_weight * time_projected
        
        return normalize(combined)


class TimeEncoder:
    """
    Encode timestamps as periodic features capturing:
    - Absolute position (days since epoch)
    - Cyclical patterns (day of week, month, year)
    - Relative position (recency)
    """
    
    def encode(self, timestamp: datetime) -> np.ndarray:
        days_since_epoch = (timestamp - EPOCH).days
        
        features = np.concatenate([
            # Absolute: logarithmic encoding
            [np.log1p(abs(days_since_epoch)) * np.sign(days_since_epoch)],
            
            # Cyclical: sine/cosine for periodic patterns
            self._cyclical_features(timestamp),
            
            # Relative recency
            [self._recency_score(timestamp)],
            
            # Time of day (if available)
            self._time_of_day_features(timestamp),
        ])
        
        return features
    
    def _cyclical_features(
        self, 
        timestamp: datetime
    ) -> np.ndarray:
        day_of_week = timestamp.weekday()
        day_of_year = timestamp.timetuple().tm_yday
        month = timestamp.month
        
        return np.concatenate([
            self._periodic(day_of_week, 7),    # Weekly cycle
            self._periodic(day_of_year, 365),  # Yearly cycle
            self._periodic(month, 12),         # Monthly cycle
        ])
    
    def _periodic(self, value: float, period: float) -> np.ndarray:
        """Sine/cosine encoding for cyclical features."""
        normalized = 2 * np.pi * value / period
        return np.array([np.sin(normalized), np.cos(normalized)])
    
    def _recency_score(self, timestamp: datetime) -> float:
        """Compute recency score (newer = higher)."""
        days_old = (datetime.now() - timestamp).days
        return np.exp(-days_old / DECAY_HALF_LIFE_DAYS)
```

#### 3.2.3 Temporal Query Decomposition

```python
# app/retrieval/temporal_parser.py

class TemporalQueryParser:
    """
    Extract time ranges and temporal intent from queries.
    
    Examples:
    - "What did I conclude about X last quarter?" 
      → {topic: "X", time_range: (3_months_ago, now), granularity: "month"}
    
    - "Status of Y in January"
      → {topic: "Y", time_range: (jan_1, jan_31), granularity: "day"}
    
    - "My notes on Z"
      → {topic: "Z", time_range: None, recency_weight: 0.5}
    """
    
    TEMPORAL_PATTERNS = [
        # Relative patterns
        (r"last\s+(week|month|quarter|year)", "relative_past"),
        (r"(yesterday|last)\s*(\d+)?\s*days?\s*ago", "relative_past"),
        (r"(in|the)\s+(past|recent|last)\s+\w+", "relative_past"),
        (r"(this|current)\s+(week|month|quarter|year)", "current"),
        
        # Absolute patterns
        (r"in\s+(january|february|march|...)\s+\d{4}", "absolute_month"),
        (r"(Q[1-4])\s+\d{4}", "absolute_quarter"),
        (r"\d{4}", "absolute_year"),
        
        # Event patterns
        (r"on\s+\w+\s+\d{1,2}", "absolute_day"),
        (r"before|after|between.*and", "range"),
    ]
    
    async def parse(self, query: str) -> TemporalQuery:
        # Use LLM for complex temporal extraction
        prompt = f"""
        Extract temporal information from this query.
        
        Query: {query}
        
        Return JSON:
        {{
            "has_temporal": true/false,
            "time_range": {{
                "start": "ISO date or null",
                "end": "ISO date or null",
                "granularity": "day/week/month/quarter/year/null"
            }},
            "recency_weight": 0.0-1.0,
            "temporal_keywords": ["list of time-related words"],
            "interpretation": "natural language interpretation"
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        return TemporalQuery(**json.loads(response.choices[0].message.content))
```

#### 3.2.4 Time-Aware Retrieval

```python
# app/retrieval/temporal_retriever.py

class TemporalRetriever:
    """
    Combine semantic similarity with temporal relevance.
    
    Score = α * semantic_similarity + (1-α) * temporal_relevance
    
    Where α is determined by query's temporal specificity.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        temporal_store: TemporalVectorStore,
        default_alpha: float = 0.7,
    ):
        self.vector_store = vector_store
        self.temporal_store = temporal_store
        self.default_alpha = default_alpha
    
    async def search(
        self,
        query: str,
        temporal_query: TemporalQuery,
        top_k: int = 20,
    ) -> list[dict]:
        # Base semantic search
        semantic_results = await self.vector_store.search(
            query, k=top_k * 2  # Oversample for filtering
        )
        
        if temporal_query.has_temporal:
            # Compute temporal relevance scores
            scored_results = []
            for result in semantic_results:
                temporal_score = self._compute_temporal_score(
                    result,
                    temporal_query
                )
                alpha = self._compute_alpha(temporal_query)
                combined_score = (
                    alpha * result['score'] + 
                    (1 - alpha) * temporal_score
                )
                scored_results.append({
                    **result,
                    'combined_score': combined_score,
                    'temporal_score': temporal_score,
                })
            
            # Sort by combined score
            scored_results.sort(key=lambda x: x['combined_score'], reverse=True)
            return scored_results[:top_k]
        else:
            return semantic_results[:top_k]
    
    def _compute_temporal_score(
        self,
        result: dict,
        query: TemporalQuery,
    ) -> float:
        """Compute how well document timestamp matches query time range."""
        doc_time = result.get('timestamp') or result.get('captured_at')
        if not doc_time:
            return 0.5  # No temporal info, neutral
        
        if query.time_range.start and query.time_range.end:
            # Check if document falls within range
            if query.time_range.start <= doc_time <= query.time_range.end:
                # Bonus for being in the middle of the range
                range_mid = (query.time_range.start + query.time_range.end) / 2
                distance_from_mid = abs((doc_time - range_mid).days)
                max_range = (query.time_range.end - query.time_range.start).days
                proximity_score = 1 - (distance_from_mid / max_range)
                return proximity_score
            else:
                # Outside range, very low score
                return 0.1
        
        # No specific range, use recency
        days_old = (datetime.now() - doc_time).days
        recency_score = np.exp(-days_old / DECAY_HALF_LIFE_DAYS)
        return recency_score
```

#### 3.2.5 Temporal Answer Generation

```python
# app/agents/temporal_answer_agent.py

TEMPORAL_ANSWER_PROMPT = """You are answering a question with temporal context.

Query: {query}

Temporal Context:
- Requested time range: {time_range}
- Interpretation: {interpretation}

Retrieved Information:
{context}

Instructions:
1. If the retrieved documents are FROM the requested time period, 
   frame your answer as "In [time period], [content]..."
2. If retrieved documents are ABOUT the requested time period but 
   written later, note "According to records from [time], ..."
3. If no information exists for the requested time, explicitly 
   state what time periods ARE covered by available documents.
4. Be precise with dates and time references.

Generate a temporally-aware answer:"""
```

### 3.3 Code Architecture

#### 3.3.1 New Components

```
app/
├── retrieval/
│   ├── temporal_embeddings.py    # Temporal embedding generation
│   ├── temporal_retriever.py     # Time-aware retrieval
│   ├── temporal_parser.py        # Query temporal decomposition
│   └── temporal_index.py         # Vector index management
├── agents/
│   └── temporal_answer_agent.py  # Temporal reasoning in generation
└── migrations/
    └── add_temporal_fields.py    # Schema migration
```

#### 3.3.2 Migration

```python
# alembic/versions/xxxx_temporal_memory.py

def upgrade():
    # Add temporal embedding column
    op.add_column('memories', sa.Column(
        'temporal_embedding', sa.LargeBinary(), nullable=True
    ))
    op.add_column('memories', sa.Column(
        'event_date', sa.TIMESTAMP(timezone=True), nullable=True
    ))
    op.add_column('memories', sa.Column(
        'temporal_features', JSONB, server_default='{}'
    ))
    
    # Add index for time-based queries
    op.create_index(
        'ix_memories_event_date',
        'memories', ['user_id', 'event_date']
    )
```

### 3.4 Evaluation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Temporal Accuracy** | >90% | Queries with time ranges answered correctly |
| **Recall@K** | >85% | Relevant old documents retrieved |
| **Recency Ranking** | >80% | Newer relevant docs ranked higher (when appropriate) |
| **Index Size** | <2x current | Additional storage overhead |
| **Query Latency** | <100ms overhead | Temporal parsing + scoring |

### 3.5 Implementation Plan

#### Phase 1: Schema & Embeddings (Week 1-3)
- [ ] Database migration for temporal fields
- [ ] Implement `TemporalEmbedder` class
- [ ] Backfill temporal embeddings for existing memories
- [ ] Unit tests

#### Phase 2: Query Parsing (Week 4-5)
- [ ] Implement `TemporalQueryParser`
- [ ] Pattern-based extraction (fast path)
- [ ] LLM-based extraction (accurate path)
- [ ] Integration with existing query rewriting

#### Phase 3: Retrieval Integration (Week 6-8)
- [ ] Implement `TemporalRetriever`
- [ ] Combine semantic + temporal scoring
- [ ] Modify `retrieval_agent.py` to use temporal retrieval
- [ ] A/B testing framework

#### Phase 4: Generation (Week 9-10)
- [ ] Implement temporal answer prompting
- [ ] Date-aware citation formatting
- [ ] End-to-end tests
- [ ] Documentation

**Effort Estimate**: 10 weeks, 1 ML engineer + 1 backend engineer

---

## 4. Technique 3: Multi-hop Reasoning (EfficientRAG)

### 4.1 Research Background

**Paper**: "EfficientRAG: Efficient Retriever for Multi-Hop QA" - EMNLP 2024

**Key Findings:**
- Multi-hop questions require sequential retrieval and reasoning
- Naive approaches retrieve 200+ chunks but with low efficiency
- Token-level labeler identifies useful tokens in retrieved chunks
- Filter module generates next-hop queries from labeled tokens
- **10x efficiency improvement** (200 chunks → 20 chunks equivalent)
- Achieves comparable recall with 10x less computation

**Why It Matters for Orivory:**
Complex research questions often require reasoning across multiple pieces of information: "What is the relationship between X and Y, given Z?" Current single-pass retrieval misses these connections.

### 4.2 Implementation Design

#### 4.2.1 LangGraph Multi-hop Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      iterate_retrieval (Loop)                           │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Hop 1      │───▶│   Hop 2      │───▶│   Hop N      │               │
│  │  Retrieval   │    │  Retrieval   │    │  Retrieval   │               │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Labeler    │    │   Labeler    │    │   Labeler    │               │
│  │ Token-level │    │ Token-level  │    │ Token-level  │               │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ Next-hop     │    │ Next-hop    │    │ Combine     │               │
│  │ Query Gen    │    │ Query Gen   │    │ Evidence    │               │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│         │                   │                   │                       │
│         └───────────────────┴───────────────────┘                       │
│                             │                                           │
│                             ▼                                           │
│                    ┌──────────────────┐                                │
│                    │  Merge & Answer  │                                │
│                    └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 4.2.2 Token-Level Labeler

```python
# app/retrieval/hop_labeler.py

class TokenLevelLabeler:
    """
    Identify which tokens in retrieved chunks are useful for 
    generating the next retrieval query.
    
    Inspired by EfficientRAG's token labeling approach.
    """
    
    LABELER_PROMPT = """Given a question and a retrieved document, identify 
    which tokens (words or phrases) in the document are MOST USEFUL for 
    finding information to answer the question.
    
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
            {{"token": "word", "start": 0, "end": 4, "reason": "why useful"}},
            ...
        ],
        "next_hop_hints": [
            "suggested follow-up search term 1",
            "suggested follow-up search term 2"
        ],
        "confidence": 0.0-1.0
    }}
    """
    
    async def label(
        self,
        question: str,
        document: str,
        max_tokens: int = 50,
    ) -> LabelingResult:
        """Label useful tokens in document for next-hop retrieval."""
        
        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": self.LABELER_PROMPT},
                {"role": "user", "content": f"Question: {question}\n\nDocument: {document}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return LabelingResult(
            useful_tokens=[
                TokenSpan(t["token"], t["start"], t["end"], t["reason"])
                for t in result["useful_tokens"][:max_tokens]
            ],
            next_hop_hints=result["next_hop_hints"],
            confidence=result["confidence"],
        )
```

#### 4.2.3 Next-hop Query Generation

```python
# app/retrieval/next_hop_generator.py

class NextHopQueryGenerator:
    """
    Generate optimized queries for the next retrieval hop based on
    labeled tokens and accumulated evidence.
    """
    
    async def generate(
        self,
        original_question: str,
        previous_hops: list[HopResult],
        labeled_tokens: list[TokenSpan],
    ) -> list[str]:
        """
        Generate 2-3 query variants for next-hop retrieval.
        """
        
        context = self._build_context(original_question, previous_hops)
        token_context = self._format_tokens(labeled_tokens)
        
        prompt = f"""
        Generate search queries to find information that connects to 
        what we've already found.
        
        Original Question: {original_question}
        
        What we've found so far:
        {context}
        
        Key entities/terms to explore:
        {token_context}
        
        Generate 2-3 diverse search queries that:
        1. Build on existing findings
        2. Explore different aspects
        3. Are specific enough to find relevant documents
        
        Return JSON:
        {{
            "queries": ["query 1", "query 2", "query 3"],
            "reasoning": "why these queries"
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return result["queries"]
    
    def _build_context(
        self,
        question: str,
        hops: list[HopResult],
    ) -> str:
        """Build context string from previous hops."""
        lines = [f"Original question: {question}\n"]
        for i, hop in enumerate(hops, 1):
            lines.append(f"\n--- Hop {i} ---")
            lines.append(f"Retrieved: {hop.retrieved_summary}")
            lines.append(f"Key finding: {hop.key_finding}")
        return "\n".join(lines)
```

#### 4.2.4 Multi-hop Agent Implementation

```python
# app/agents/multi_hop_agent.py

class MultiHopAgent:
    """
    Multi-hop retrieval agent for complex questions.
    
    Detects multi-hop questions and iteratively retrieves
    and reasons across multiple hops.
    """
    
    MAX_HOPS = 3
    HOP_CONVERGENCE_THRESHOLD = 0.8
    
    def __init__(
        self,
        labeler: TokenLevelLabeler,
        query_generator: NextHopQueryGenerator,
        retriever: TemporalRetriever,  # Can use temporal or standard
    ):
        self.labeler = labeler
        self.query_generator = query_generator
        self.retriever = retriever
    
    async def run(
        self,
        state: AgentState,
    ) -> AgentState:
        """Execute multi-hop retrieval loop."""
        
        question = state["query"]
        all_evidence: list[dict] = []
        hops: list[HopResult] = []
        
        # Check if multi-hop
        is_multi_hop = await self._detect_multi_hop(question)
        
        if not is_multi_hop:
            # Single-hop, use normal retrieval
            return await self._single_hop_retrieval(state)
        
        # Multi-hop loop
        for hop_num in range(1, self.MAX_HOPS + 1):
            # Generate queries for this hop
            if hop_num == 1:
                queries = [question]
            else:
                queries = await self.query_generator.generate(
                    question, hops, all_labeled_tokens
                )
            
            # Retrieve for this hop
            hop_results = []
            for query in queries:
                results = await self.retriever.search(query, top_k=10)
                hop_results.extend(results)
            
            # Deduplicate and rank
            hop_results = self._deduplicate(hop_results)
            
            # Label useful tokens
            labeled_tokens = []
            for result in hop_results[:5]:  # Label top 5
                labeling = await self.labeler.label(question, result['content'])
                labeled_tokens.extend(labeling.useful_tokens)
            
            # Extract key information
            key_findings = await self._extract_findings(
                question, hop_results, labeled_tokens
            )
            
            hop_result = HopResult(
                hop_num=hop_num,
                queries=queries,
                retrieved=hop_results,
                labeled_tokens=labeled_tokens,
                key_findings=key_findings,
            )
            hops.append(hop_result)
            all_evidence.extend(hop_results)
            
            # Check convergence
            if self._check_convergence(hop_result, question):
                break
        
        # Combine evidence and generate answer
        state["multi_hop_evidence"] = all_evidence
        state["multi_hop_hops"] = [h.to_dict() for h in hops]
        state["agent_trace"]["multi_hop"] = {
            "hops": len(hops),
            "total_evidence": len(all_evidence),
            "efficient": True,
        }
        
        return state
    
    async def _detect_multi_hop(self, question: str) -> bool:
        """Detect if question requires multi-hop reasoning."""
        
        multi_hop_patterns = [
            r"(and|with)\s+respect\s+to",
            r"(relationship|connection|how)\s+between",
            r"(because|therefore|thus)\s+",
            r"(compare|contrast)\s+",
            r"(based\s+on|given)\s+.*\.",
            r"what\s+.*\s+if\s+",
        ]
        
        # Fast pattern check
        for pattern in multi_hop_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return True
        
        # LLM check for complex questions
        prompt = f"""
        Does this question require multi-step reasoning across multiple 
        pieces of information? Answer yes if:
        - It asks about relationships between concepts
        - It requires combining information from different sources
        - It has nested or conditional sub-questions
        
        Question: {question}
        
        Answer: yes or no
        """
        
        # Use fast model for detection
        response = await self.client.chat.completions.create(
            model="haiku",  # Fast, cheap model
            messages=[{"role": "user", "content": prompt}],
        )
        
        return "yes" in response.choices[0].message.content.lower()
```

#### 4.2.5 Evidence Combination

```python
# app/agents/evidence_combiner.py

class EvidenceCombiner:
    """
    Combine evidence from multiple hops into coherent context
    for final answer generation.
    """
    
    async def combine(
        self,
        question: str,
        hops: list[HopResult],
    ) -> str:
        """
        Synthesize findings from multiple hops into coherent context.
        """
        
        evidence_summary = self._summarize_hops(hops)
        
        prompt = f"""
        Synthesize the following research findings into a coherent 
        context that answers the question.
        
        Question: {question}
        
        Evidence from multiple sources:
        {evidence_summary}
        
        Requirements:
        1. Organize by theme/finding, not by source
        2. Resolve any contradictions between sources
        3. Maintain factual accuracy
        4. Preserve citation attributions
        
        Provide synthesized context:"""
        
        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        
        return response.choices[0].message.content
```

### 4.3 Code Architecture

```
app/
├── agents/
│   ├── multi_hop_agent.py       # Main multi-hop orchestrator
│   ├── hop_labeler.py          # Token-level labeling
│   ├── next_hop_generator.py   # Query generation
│   └── evidence_combiner.py    # Evidence synthesis
├── retrieval/
│   ├── efficient_retriever.py   # Efficient retrieval wrapper
│   └── hop_state.py            # Hop state management
└── graph/
    └── multi_hop_builder.py    # Multi-hop graph extensions
```

### 4.4 Evaluation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Multi-hop Recall** | >95% | Correct answers for multi-hop questions |
| **Efficiency Gain** | 10x reduction | Chunks retrieved vs naive |
| **Hop Accuracy** | >90% | Each hop retrieves relevant docs |
| **Convergence Rate** | >80% | Stop early when answer found |
| **Latency** | <2x single-hop | Despite additional hops |

### 4.5 Implementation Plan

#### Phase 1: Detection & Loop (Week 1-3)
- [ ] Implement multi-hop detector
- [ ] Create `MultiHopAgent` class
- [ ] Basic hop loop implementation
- [ ] Convergence detection

#### Phase 2: Token Labeling (Week 4-5)
- [ ] Implement `TokenLevelLabeler`
- [ ] Optimize labeling prompts
- [ ] Batch labeling for efficiency
- [ ] Unit tests

#### Phase 3: Query Generation (Week 6-7)
- [ ] Implement `NextHopQueryGenerator`
- [ ] Query diversity strategies
- [ ] Integration with retrieval
- [ ] A/B testing

#### Phase 4: Evidence Synthesis (Week 8-10)
- [ ] Implement `EvidenceCombiner`
- [ ] Contradiction resolution
- [ ] Citation preservation
- [ ] End-to-end evaluation

**Effort Estimate**: 10 weeks, 1 ML engineer + 1 NLP engineer

---

## 5. Technique 4: Continual Learning (Pistis-RAG)

### 5.1 Research Background

**Concept**: Closed-loop learning system where user feedback improves retrieval quality over time.

**How It Works:**
- Collect feedback: "Report Error" clicks, thumbs down, corrections
- Label feedback: hallucination, incomplete, irrelevant, correct
- Weekly curation of evaluation sets
- Active learning: prioritize uncertain predictions
- Retrain reranker on failure cases (A/B tested)

**Why It Matters for Orivory:**
Current system has no mechanism to learn from user corrections. A document that consistently fails to answer certain questions could be deprioritized or rewritten.

### 5.2 Implementation Design

#### 5.2.1 Feedback Data Model

```python
# app/models/feedback.py

class FeedbackType(str, Enum):
    THUMBS_DOWN = "thumbs_down"
    THUMBS_UP = "thumbs_up"
    ERROR_REPORT = "error_report"
    CORRECTION = "correction"
    CITATION_CLICK = "citation_click"


class FeedbackLabel(str, Enum):
    HALLUCINATION = "hallucination"
    INCOMPLETE = "incomplete"
    IRRELEVANT = "irrelevant"
    CORRECT = "correct"
    OUTDATED = "outdated"
    UNCLEAR = "unclear"


class UserFeedback(Base):
    """Store user feedback for continual learning."""
    
    __tablename__ = "user_feedback"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    
    # Feedback type
    feedback_type: Mapped[FeedbackType] = mapped_column(String(32))
    label: Mapped[FeedbackLabel | None] = mapped_column(String(32), nullable=True)
    
    # Context
    query: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    chunks_used: Mapped[list[dict]] = mapped_column(JSONB)
    
    # Detailed feedback
    user_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean(), default=False)
    label_source: Mapped[str] = mapped_column(
        String(16), server_default="user"  # user, automated, human_reviewer
    )
    
    __table_args__ = (
        Index("ix_feedback_user_processed", "user_id", "processed"),
        Index("ix_feedback_label", "label"),
        Index("ix_feedback_created", "created_at"),
    )


class EvaluationSet(Base):
    """Curated evaluation sets from feedback."""
    
    __tablename__ = "evaluation_sets"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    
    # Curated from feedback
    feedback_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID))
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer(), default=1)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    created_by: Mapped[str] = mapped_column(String(64))  # "system", "human_reviewer"
    
    # Evaluation results
    last_evaluated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    metrics: Mapped[dict | None] = mapped_column(JSONB)
```

#### 5.2.2 Feedback Collection Pipeline

```python
# app/feedback/collector.py

class FeedbackCollector:
    """
    Collect and process user feedback for continual learning.
    """
    
    async def collect(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        feedback_data: FeedbackData,
    ) -> UserFeedback:
        """Record user feedback."""
        
        # Extract chunks used in the response
        chunks_used = self._extract_chunks_from_response(
            feedback_data.response_id
        )
        
        # Auto-label if possible
        auto_label = await self._auto_label(
            feedback_data.feedback_type,
            feedback_data.user_comment,
        )
        
        feedback = UserFeedback(
            user_id=user_id,
            conversation_id=conversation_id,
            feedback_type=feedback_data.feedback_type,
            label=auto_label,
            query=feedback_data.query,
            response=feedback_data.response,
            chunks_used=chunks_used,
            user_comment=feedback_data.user_comment,
            corrected_answer=feedback_data.corrected_answer,
        )
        
        self.db.add(feedback)
        await self.db.commit()
        
        # Queue for processing
        await self._queue_for_processing(feedback)
        
        return feedback
    
    async def _auto_label(
        self,
        feedback_type: FeedbackType,
        comment: str | None,
    ) -> FeedbackLabel | None:
        """Attempt automated labeling based on feedback type."""
        
        if feedback_type == FeedbackType.THUMBS_UP:
            return FeedbackLabel.CORRECT
        
        if feedback_type == FeedbackType.THUMBS_DOWN:
            # Use LLM to classify based on comment
            if comment:
                return await self._classify_from_comment(comment)
            return FeedbackLabel.IRRELEVANT  # Default
        
        if feedback_type == FeedbackType.ERROR_REPORT:
            # Check for hallucination markers
            if self._has_hallucination_markers(comment):
                return FeedbackLabel.HALLUCINATION
            return FeedbackLabel.INCOMPLETE
        
        return None
```

#### 5.2.3 Active Learning Prioritization

```python
# app/feedback/active_learning.py

class ActiveLearningPrioritizer:
    """
    Prioritize feedback for labeling based on uncertainty.
    
    Use uncertainty sampling to select most informative examples
    for human review and retraining.
    """
    
    def __init__(
        self,
        reranker: Reranker,
        uncertainty_threshold: float = 0.3,
    ):
        self.reranker = reranker
        self.uncertainty_threshold = uncertainty_threshold
    
    async def prioritize(
        self,
        feedback_batch: list[UserFeedback],
        top_k: int = 50,
    ) -> list[PrioritizedFeedback]:
        """
        Rank feedback by learning potential.
        
        Priority factors:
        1. Prediction uncertainty (reranker confidence spread)
        2. Feedback frequency (same query/answer repeated)
        3. User expertise (trusted users' feedback weighted higher)
        4. Recency (newer feedback more relevant)
        """
        
        prioritized = []
        
        for feedback in feedback_batch:
            if feedback.processed:
                continue
            
            # Compute uncertainty score
            uncertainty = await self._compute_uncertainty(feedback)
            
            # Compute priority score
            priority = self._compute_priority(
                uncertainty=uncertainty,
                frequency=self._get_feedback_frequency(feedback),
                user_trust=self._get_user_trust(feedback.user_id),
                recency=self._compute_recency(feedback.created_at),
            )
            
            prioritized.append(PrioritizedFeedback(
                feedback=feedback,
                uncertainty=uncertainty,
                priority=priority,
            ))
        
        # Sort by priority and return top_k
        prioritized.sort(key=lambda x: x.priority, reverse=True)
        return prioritized[:top_k]
    
    async def _compute_uncertainty(
        self,
        feedback: UserFeedback,
    ) -> float:
        """
        Compute prediction uncertainty.
        
        Use prediction disagreement between original reranker
        and current model.
        """
        
        # Get reranker scores for this query
        original_scores = [
            c.get('rerank_score', 0) 
            for c in feedback.chunks_used
        ]
        
        # Re-score with current model
        current_scores = await self.reranker.rescore(
            query=feedback.query,
            chunks=feedback.chunks_used,
        )
        
        # Compute score disagreement (Brier score-like)
        disagreement = np.mean([
            (orig - curr) ** 2 
            for orig, curr in zip(original_scores, current_scores)
        ])
        
        return disagreement
```

#### 5.2.4 Evaluation Set Curation

```python
# app/feedback/curator.py

class EvaluationSetCurator:
    """
    Weekly curation of evaluation sets from feedback.
    """
    
    async def curate_weekly(
        self,
        date_range: tuple[datetime, datetime],
    ) -> EvaluationSet:
        """
        Create weekly evaluation set from recent feedback.
        """
        
        # Fetch recent unprocessed feedback
        feedback = await self._fetch_feedback_in_range(date_range)
        
        # Filter for high-quality samples
        curated = self._filter_quality_samples(feedback)
        
        # Balance categories
        balanced = self._balance_categories(curated)
        
        # Create evaluation set
        eval_set = EvaluationSet(
            name=f"weekly_eval_{date_range[0].strftime('%Y_%m_%d')}",
            description=f"Weekly evaluation set: {len(balanced)} samples",
            feedback_ids=[f.id for f in balanced],
            created_by="system",
            created_at=datetime.now(),
        )
        
        self.db.add(eval_set)
        await self.db.commit()
        
        return eval_set
    
    def _balance_categories(
        self,
        feedback: list[UserFeedback],
    ) -> list[UserFeedback]:
        """
        Balance evaluation set across categories.
        
        Target distribution:
        - 40% correct (positive examples)
        - 20% hallucination
        - 20% incomplete
        - 20% irrelevant
        """
        
        by_category: dict[FeedbackLabel, list[UserFeedback]] = {}
        for f in feedback:
            label = f.label or FeedbackLabel.IRRELEVANT
            by_category.setdefault(label, []).append(f)
        
        balanced = []
        targets = {
            FeedbackLabel.CORRECT: 0.4,
            FeedbackLabel.HALLUCINATION: 0.2,
            FeedbackLabel.INCOMPLETE: 0.2,
            FeedbackLabel.IRRELEVANT: 0.2,
        }
        
        for label, target_ratio in targets.items():
            samples = by_category.get(label, [])
            target_count = int(len(feedback) * target_ratio)
            
            if len(samples) <= target_count:
                balanced.extend(samples)
            else:
                # Random sample
                balanced.extend(random.sample(samples, target_count))
        
        return balanced
```

#### 5.2.5 Retriever Improvement Loop

```python
# app/feedback/improvement_loop.py

class RetrieverImprovementLoop:
    """
    Closed-loop improvement of reranker based on feedback.
    """
    
    def __init__(
        self,
        reranker: Reranker,
        eval_curator: EvaluationSetCurator,
        training_pipeline: TrainingPipeline,
    ):
        self.reranker = reranker
        self.eval_curator = eval_curator
        self.training_pipeline = training_pipeline
    
    async def run_weekly_update(
        self,
    ) -> TrainingResult:
        """
        Weekly retrainer update cycle.
        
        1. Curate evaluation set from last week's feedback
        2. Run evaluation on current model
        3. If metrics degraded → trigger retraining
        4. A/B test new model vs current
        5. Deploy if new model wins
        """
        
        # Step 1: Curate evaluation set
        last_week = self._get_last_week_range()
        eval_set = await self.eval_curator.curate_weekly(last_week)
        
        # Step 2: Evaluate current model
        current_metrics = await self._evaluate(
            self.reranker, eval_set
        )
        
        # Step 3: Check if retraining needed
        if not self._should_retrain(current_metrics):
            return TrainingResult(
                status="skipped",
                reason="metrics_stable",
                metrics=current_metrics,
            )
        
        # Step 4: Train new model
        training_data = await self._prepare_training_data(last_week)
        new_model = await self.training_pipeline.train(
            training_data,
            base_model=self.reranker.model_name,
        )
        
        # Step 5: A/B evaluation
        new_metrics = await self._evaluate(new_model, eval_set)
        
        if self._new_model_wins(current_metrics, new_metrics):
            # Deploy new model
            await self._deploy_model(new_model)
            return TrainingResult(
                status="deployed",
                previous_metrics=current_metrics,
                new_metrics=new_metrics,
                model_id=new_model.id,
            )
        else:
            return TrainingResult(
                status="rejected",
                reason="metrics_degraded",
                previous_metrics=current_metrics,
                new_metrics=new_metrics,
            )
```

### 5.3 Code Architecture

```
app/
├── feedback/
│   ├── collector.py            # Feedback collection
│   ├── auto_labeler.py         # Automated labeling
│   ├── active_learning.py      # Prioritization
│   ├── curator.py              # Evaluation set curation
│   └── improvement_loop.py     # Closed-loop training
├── models/
│   ├── feedback.py             # Feedback data models
│   └── evaluation_set.py       # Eval set model
└── training/
    ├── reranker_trainer.py     # Reranker fine-tuning
    └── ab_evaluator.py         # A/B test framework
```

### 5.4 Evaluation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Feedback Collection Rate** | >5% of queries | % queries with feedback |
| **Auto-label Accuracy** | >85% | Agreement with human labels |
| **Retrieval Improvement** | >10% | MAP on eval sets over time |
| **Training Success Rate** | >90% | Successful retraining cycles |
| **A/B Win Rate** | >50% | New models outperforming old |

### 5.5 Implementation Plan

#### Phase 1: Data Infrastructure (Week 1-2)
- [ ] Create feedback data models
- [ ] Implement feedback collection API
- [ ] Frontend feedback UI components
- [ ] Database migration

#### Phase 2: Automated Labeling (Week 3-4)
- [ ] Implement auto-labeler
- [ ] LLM-based classification
- [ ] Label confidence scoring
- [ ] Quality monitoring

#### Phase 3: Active Learning (Week 5-6)
- [ ] Implement prioritization logic
- [ ] Uncertainty computation
- [ ] Human review queue
- [ ] Dashboard for reviewers

#### Phase 4: Training Pipeline (Week 7-10)
- [ ] Evaluation set curation
- [ ] Training data preparation
- [ ] Reranker fine-tuning pipeline
- [ ] A/B testing framework
- [ ] Deployment automation

**Effort Estimate**: 10 weeks, 1 ML engineer + 1 data engineer

---

## 6. Technique 5: Confidence Calibration

### 6.1 Research Background

**Concept**: Calibrate confidence scores based on actual accuracy to provide users with reliable uncertainty estimates.

**How It Works:**
- Log predicted confidence vs actual accuracy over time
- Use Platt scaling or isotonic regression to calibrate
- Adjust raw model confidence to calibrated confidence
- Display calibrated confidence in UI

**Why It Matters for Orivory:**
Raw model confidence is often poorly calibrated (e.g., 78% confidence but only 60% actual accuracy). Researchers need reliable uncertainty estimates to know when to trust answers.

### 6.2 Implementation Design

#### 6.2.1 Calibration Data Collection

```python
# app/calibration/tracker.py

class CalibrationTracker:
    """
    Track prediction confidence vs actual accuracy for calibration.
    """
    
    async def log_prediction(
        self,
        query: str,
        predicted_confidence: float,
        response: str,
        chunks: list[dict],
        user_feedback: UserFeedback | None = None,
    ):
        """
        Log a prediction for later calibration analysis.
        """
        
        # Determine actual outcome
        if user_feedback is None:
            outcome = None  # Unknown yet
        else:
            outcome = self._feedback_to_outcome(user_feedback)
        
        record = CalibrationRecord(
            query_hash=self._hash_query(query),
            query=query[:500],  # Truncate for storage
            predicted_confidence=predicted_confidence,
            chunks_used=[c.get('id') for c in chunks],
            outcome=outcome,
            feedback_id=user_feedback.id if user_feedback else None,
            created_at=datetime.now(),
        )
        
        self.db.add(record)
        await self.db.commit()
    
    def _feedback_to_outcome(
        self,
        feedback: UserFeedback,
    ) -> CalibrationOutcome:
        """Convert user feedback to binary outcome."""
        
        if feedback.label == FeedbackLabel.CORRECT:
            return CalibrationOutcome.CORRECT
        elif feedback.label in [
            FeedbackLabel.HALLUCINATION,
            FeedbackLabel.IRRELEVANT,
            FeedbackLabel.OUTDATED,
        ]:
            return CalibrationOutcome.INCORRECT
        else:
            return CalibrationOutcome.AMBIGUOUS
```

#### 6.2.2 Calibration Model

```python
# app/calibration/calibrator.py

class ConfidenceCalibrator:
    """
    Calibrate model confidence scores using historical data.
    
    Supports multiple calibration methods:
    - Platt Scaling (sigmoid)
    - Isotonic Regression (monotonic)
    - Temperature Scaling (simplest)
    """
    
    def __init__(
        self,
        method: str = "isotonic",  # or "platt", "temperature"
        min_samples: int = 100,
    ):
        self.method = method
        self.min_samples = min_samples
        self.calibration_params: dict | None = None
        self.is_fitted = False
    
    async def fit(
        self,
        db: AsyncSession,
        date_range: tuple[datetime, datetime] | None = None,
    ) -> CalibrationMetrics:
        """
        Fit calibration model on historical data.
        """
        
        # Fetch calibration records with known outcomes
        records = await self._fetch_calibration_data(db, date_range)
        
        if len(records) < self.min_samples:
            return CalibrationMetrics(
                method=self.method,
                n_samples=len(records),
                fitted=False,
                error="insufficient_samples",
            )
        
        # Prepare data
        confidences = np.array([r.predicted_confidence for r in records])
        outcomes = np.array([
            1 if r.outcome == CalibrationOutcome.CORRECT else 0
            for r in records
        ])
        
        # Fit calibration model
        if self.method == "platt":
            self.calibration_params = self._fit_platt(confidences, outcomes)
        elif self.method == "isotonic":
            self.calibration_params = self._fit_isotonic(confidences, outcomes)
        elif self.method == "temperature":
            self.calibration_params = self._fit_temperature(confidences, outcomes)
        
        self.is_fitted = True
        
        # Compute calibration metrics
        metrics = self._compute_metrics(confidences, outcomes)
        
        return CalibrationMetrics(
            method=self.method,
            n_samples=len(records),
            fitted=True,
            ece=metrics['ece'],
            nll=metrics['nll'],
            brier=metrics['brier'],
        )
    
    def _fit_platt(
        self,
        confidences: np.ndarray,
        outcomes: np.ndarray,
    ) -> dict:
        """
        Platt scaling: fit sigmoid function to map confidence to probability.
        
        P(outcome=1) = 1 / (1 + exp(-(a*conf + b)))
        """
        
        # Use logistic regression
        from sklearn.linear_model import LogisticRegression
        
        model = LogisticRegression(
            C=1e10,  # High regularization
            solver='lbfgs',
            max_iter=1000,
        )
        
        X = confidences.reshape(-1, 1)
        model.fit(X, outcomes)
        
        return {
            'a': model.coef_[0][0],
            'b': model.intercept_[0],
            'model': model,
        }
    
    def _fit_isotonic(
        self,
        confidences: np.ndarray,
        outcomes: np.ndarray,
    ) -> dict:
        """
        Isotonic regression: monotonic piecewise constant mapping.
        More flexible than Platt but may overfit.
        """
        
        from sklearn.isotonic import IsotonicRegression
        
        iso = IsotonicRegression(
            y_min=0.0,
            y_max=1.0,
            out_of_bounds='clip',
        )
        
        iso.fit(confidences, outcomes)
        
        return {'model': iso}
    
    def calibrate(
        self,
        raw_confidence: float,
    ) -> CalibratedConfidence:
        """
        Convert raw confidence to calibrated confidence.
        """
        
        if not self.is_fitted:
            return CalibratedConfidence(
                raw=raw_confidence,
                calibrated=raw_confidence,
                method=self.method,
                uncertainty=0.1,  # Default uncertainty
            )
        
        if self.method == "platt":
            calibrated = self._platt_predict(raw_confidence)
        elif self.method == "isotonic":
            calibrated = self._isotonic_predict(raw_confidence)
        else:
            calibrated = raw_confidence
        
        # Compute uncertainty based on calibration curve
        uncertainty = self._compute_uncertainty(
            raw_confidence, calibrated
        )
        
        return CalibratedConfidence(
            raw=raw_confidence,
            calibrated=clamp(calibrated, 0.0, 1.0),
            method=self.method,
            uncertainty=uncertainty,
        )
    
    def _compute_uncertainty(
        self,
        raw: float,
        calibrated: float,
    ) -> float:
        """
        Estimate uncertainty based on calibration gap.
        
        If raw and calibrated differ significantly, uncertainty is higher.
        """
        
        gap = abs(raw - calibrated)
        
        # Map gap to uncertainty (0 to 0.5)
        uncertainty = min(0.5, gap * 2)
        
        return uncertainty
```

#### 6.2.3 Calibration Metrics

```python
# app/calibration/metrics.py

class CalibrationMetrics:
    """Metrics for evaluating calibration quality."""
    
    def __init__(
        self,
        method: str,
        n_samples: int,
        fitted: bool,
        ece: float | None = None,
        nll: float | None = None,
        brier: float | None = None,
        error: str | None = None,
    ):
        self.method = method
        self.n_samples = n_samples
        self.fitted = fitted
        self.ece = ece
        self.nll = nll
        self.brier = brier
        self.error = error
    
    @property
    def is_good(self) -> bool:
        """Check if calibration is acceptable."""
        if not self.fitted or self.error:
            return False
        return self.ece < 0.05  # ECE < 5% is good


def expected_calibration_error(
    confidences: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> float:
    """
    Compute Expected Calibration Error (ECE).
    
    ECE = Σ (|B_m| / n) * |acc(B_m) - conf(B_m)|
    
    Where B_m is bin m containing samples with confidence in 
    [(m-1)/n, m/n).
    """
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        # Samples in this bin
        in_bin = (confidences > bin_boundaries[i]) & (
            confidences <= bin_boundaries[i + 1]
        )
        bin_count = np.sum(in_bin)
        
        if bin_count == 0:
            continue
        
        # Accuracy in bin
        bin_accuracy = np.mean(outcomes[in_bin])
        
        # Average confidence in bin
        bin_confidence = np.mean(confidences[in_bin])
        
        # Add weighted absolute difference
        ece += (bin_count / len(confidences)) * abs(
            bin_accuracy - bin_confidence
        )
    
    return ece


def negative_log_likelihood(
    confidences: np.ndarray,
    outcomes: np.ndarray,
) -> float:
    """
    Compute negative log-likelihood.
    
    NLL = -1/n * Σ [y * log(p) + (1-y) * log(1-p)]
    """
    
    eps = 1e-10  # Prevent log(0)
    p = np.clip(confidences, eps, 1 - eps)
    
    nll = -np.mean(
        outcomes * np.log(p) + (1 - outcomes) * np.log(1 - p)
    )
    
    return nll
```

#### 6.2.4 Integration with Answer Generation

```python
# app/agents/answer_agent.py - Modifications

class CalibratedAnswerAgent:
    """
    Answer agent with calibrated confidence scores.
    """
    
    def __init__(
        self,
        calibrator: ConfidenceCalibrator,
        tracker: CalibrationTracker,
    ):
        self.calibrator = calibrator
        self.tracker = tracker
    
    async def generate(
        self,
        state: AgentState,
    ) -> AgentState:
        """Generate answer with calibrated confidence."""
        
        # Generate raw answer (existing logic)
        raw_response, raw_confidence = await self._generate_raw(state)
        
        # Calibrate confidence
        calibrated = self.calibrator.calibrate(raw_confidence)
        
        # Update state
        state["response"] = raw_response
        state["confidence"] = calibrated.calibrated
        state["raw_confidence"] = calibrated.raw
        state["confidence_uncertainty"] = calibrated.uncertainty
        state["confidence_level"] = self._get_confidence_level(
            calibrated.calibrated
        )
        
        # Log for future calibration
        await self.tracker.log_prediction(
            query=state["query"],
            predicted_confidence=calibrated.calibrated,
            response=raw_response,
            chunks=state.get("reranked_chunks", []),
        )
        
        # Adjust response based on confidence
        state["response"] = self._adjust_response_for_confidence(
            state["response"],
            calibrated,
        )
        
        return state
    
    def _get_confidence_level(
        self,
        confidence: float,
    ) -> str:
        """Categorize confidence level for UI."""
        
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _adjust_response_for_confidence(
        self,
        response: str,
        calibrated: CalibratedConfidence,
    ) -> str:
        """Add appropriate hedging based on confidence."""
        
        if calibrated.calibrated >= 0.8:
            return response  # No hedging
        
        if calibrated.calibrated >= 0.5:
            # Add subtle hedging
            return (
                f"{response}\n\n"
                f"---\n"
                f"*Note: Confidence {calibrated.calibrated:.0%}. "
                f"This answer is based on the available documents.*"
            )
        
        # Low confidence
        return (
            f"I'm not fully confident about this answer "
            f"(calibrated confidence: {calibrated.calibrated:.0%}).\n\n"
            f"{response}\n\n"
            f"---\n"
            f"*Please verify this information with additional sources.*"
        )
```

#### 6.2.5 UI Confidence Display

```json
// Example API response with calibration

{
  "response": "The study found X...",
  "confidence": {
    "raw": 0.78,
    "calibrated": 0.62,
    "uncertainty": 0.08,
    "level": "medium",
    "method": "isotonic",
    "display": {
      "value": "62%",
      "icon": "medium_confidence",
      "color": "#f59e0b",
      "message": "Based on available documents"
    }
  },
  "agent_trace": {
    "confidence_calibration": {
      "method": "isotonic",
      "samples_used": 1250,
      "ece": 0.034,
      "fitted_at": "2024-01-15T00:00:00Z"
    }
  }
}
```

### 6.3 Code Architecture

```
app/
├── calibration/
│   ├── tracker.py          # Data collection
│   ├── calibrator.py       # Calibration models
│   ├── metrics.py          # Calibration metrics
│   ├── fit_job.py          # Scheduled fitting job
│   └── api.py              # Calibration API endpoints
└── agents/
    └── calibrated_answer_agent.py  # Integration
```

### 6.4 Evaluation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **ECE (Expected Calibration Error)** | <5% | Well-calibrated |
| **Brier Score** | <0.15 | Overall accuracy + calibration |
| **Coverage** | >90% | Predictions with confidence |
| **Calibration Drift** | <2% change | Weekly stability |
| **UI Adoption** | >30% | Users notice confidence |

### 6.5 Implementation Plan

#### Phase 1: Data Collection (Week 1-2)
- [ ] Implement `CalibrationTracker`
- [ ] Integrate with answer generation
- [ ] Feedback-to-outcome mapping
- [ ] Storage infrastructure

#### Phase 2: Calibration Models (Week 3-4)
- [ ] Implement calibration models
- [ ] Platt scaling implementation
- [ ] Isotonic regression
- [ ] Temperature scaling

#### Phase 3: Metrics & Monitoring (Week 5)
- [ ] ECE computation
- [ ] Brier score
- [ ] Calibration drift monitoring
- [ ] Dashboard

#### Phase 4: UI Integration (Week 6-7)
- [ ] Confidence display components
- [ ] Hedging language
- [ ] User education
- [ ] A/B testing

**Effort Estimate**: 7 weeks, 1 ML engineer + 1 frontend engineer

---

## 7. Integration Architecture

### 7.1 Technique Combination Strategy

The five SOTA techniques are not independent—they form a complementary system:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         User Query                                      │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Temporal Memory (TimeR4)                                            │
│  ├─ Parse temporal intent from query                                    │
│  ├─ Time-filter retrieval                                               │
│  └─ Output: temporal-aware chunks + metadata                           │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. Multi-hop Reasoning (EfficientRAG)                                  │
│  ├─ Detect multi-hop questions                                          │
│  ├─ Token-level labeling                                                │
│  ├─ Iterative retrieval (up to 3 hops)                                  │
│  └─ Output: combined evidence from multiple hops                       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. Corrective-RAG (CRAG)                                              │
│  ├─ Classify chunk relevance (correct/incorrect/ambiguous)             │
│  ├─ Decompose-then-recompose ambiguous chunks                          │
│  ├─ Trigger web search for incorrect majority                          │
│  └─ Output: corrected chunks + correction_type                         │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. Answer Generation                                                   │
│  ├─ Generate answer from corrected chunks                              │
│  ├─ Add temporal reasoning ("In March 2024...")                        │
│  └─ Output: answer + raw confidence                                    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  5. Confidence Calibration                                              │
│  ├─ Calibrate raw confidence using historical data                      │
│  ├─ Add appropriate hedging based on calibrated confidence              │
│  └─ Output: calibrated confidence + uncertainty                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  6. Continual Learning (Pistis-RAG) - Background                       │
│  ├─ Collect user feedback                                               │
│  ├─ Prioritize for active learning                                      │
│  ├─ Curate evaluation sets                                              │
│  └─ Retrain reranker on failure cases (weekly)                         │
└─────────────────────────────────┴───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         User Response                                   │
│  {answer, citations, calibrated_confidence, agent_trace}               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Priority and Dependencies

| Phase | Techniques | Dependencies | Duration |
|-------|-----------|-------------|----------|
| **P0** | CRAG + Calibration | Baseline | 10 weeks |
| **P1** | Temporal Memory | CRAG completion | 10 weeks |
| **P2** | Multi-hop | Temporal completion | 10 weeks |
| **P3** | Continual Learning | All others | 8 weeks |

**Critical Path**: CRAG → Calibration → Temporal → Multi-hop → Continual Learning

### 7.3 Unified Evaluation Framework

```python
# app/evaluation/unified_framework.py

class UnifiedEvaluationFramework:
    """
    Comprehensive evaluation framework for all SOTA techniques.
    """
    
    def __init__(
        self,
        benchmarks: dict[str, Benchmark],
        metrics_collectors: list[MetricsCollector],
    ):
        self.benchmarks = benchmarks
        self.metrics_collectors = metrics_collectors
    
    async def run_full_evaluation(
        self,
        model: AgentModel,
    ) -> EvaluationReport:
        """
        Run comprehensive evaluation across all benchmarks and metrics.
        """
        
        results = {}
        
        for name, benchmark in self.benchmarks.items():
            benchmark_results = await self._evaluate_benchmark(
                model, benchmark
            )
            results[name] = benchmark_results
        
        # Compute aggregate metrics
        aggregates = self._compute_aggregates(results)
        
        # Generate report
        report = EvaluationReport(
            timestamp=datetime.now(),
            benchmark_results=results,
            aggregates=aggregates,
            recommendations=self._generate_recommendations(aggregates),
        )
        
        return report
    
    BENCHMARKS = {
        "pubhealth": PubHealthBenchmark,      # CRAG evaluation
        "temp Questions": TemporalBenchmark,   # TimeR4 evaluation
        "multi-hop": MultiHopBenchmark,        # EfficientRAG evaluation
        "calibration": CalibrationBenchmark,   # Calibration quality
        "general": GeneralQABenchmark,         # Overall quality
    }
    
    METRICS = {
        "accuracy": AccuracyMetric,
        "calibration_ece": CalibrationECEMetric,
        "latency": LatencyMetric,
        "cost": CostMetric,
        "coverage": CoverageMetric,
    }
```

### 7.4 Rollout Strategy

```
Week 1-10:    [====CRAG====][==Calibration==]
Week 5-15:              [====Temporal Memory====]
Week 10-20:                       [====Multi-hop====]
Week 15-25:                                 [==Continual Learning==]
```

**Feature Flags**: Each technique can be independently enabled/disabled via configuration.

---

## 8. Appendix

### 8.1 Paper References

1. **Corrective-RAG (CRAG)**
   - Yan, S., et al. (2024). "Corrective Retrieval Augmented Generation"
   - arXiv: 2401.15884
   - Key contribution: Self-correcting retrieval with web search fallback

2. **EfficientRAG (Multi-hop)**
   - EfficientRAG: Efficient Retriever for Multi-Hop QA
   - EMNLP 2024
   - Key contribution: Token-level labeling for 10x efficiency

3. **TimeR4 + EM-LLM (Temporal)**
   - TimeR4: Time-aware RAG
   - EM-LLM: Episodic Memory Language Model
   - Key contribution: Temporal embeddings and reasoning

4. **Pistis-RAG (Continual Learning)**
   - Pistis-RAG framework
   - Key contribution: Closed-loop learning from feedback

5. **Confidence Calibration**
   - Platt, J. (1999). "Probabilistic Outputs for SVMs"
   - Niculescu-Mizil, A., & Caruana, R. (2005). "Predicting Good Probabilities"
   - Key contribution: Calibration methods for machine learning models

### 8.2 Additional Reading

- **RAG Survey**: "Retrieval-Augmented Generation for Large Language Models: A Survey" (2024)
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Evaluation Frameworks**: RAGAS, Trulens, LangSmith
- **Calibration**: sklearn.calibration module

### 8.3 Glossary

| Term | Definition |
|------|------------|
| **ECE** | Expected Calibration Error - measure of calibration quality |
| **Brier Score** | Combined measure of accuracy and calibration |
| **RRF** | Reciprocal Rank Fusion - method for combining retrieval results |
| **Platt Scaling** | Sigmoid-based calibration method |
| **Isotonic Regression** | Monotonic calibration method |
| **Multi-hop QA** | Question answering requiring multiple retrieval steps |
| **Token-level Labeling** | Marking useful tokens for next retrieval |
| **Active Learning** | Prioritizing informative samples for labeling |
| **Temporal Embedding** | Embedding that encodes time information |
| **Recency Weighting** | Scoring that favors newer documents |

### 8.4 Configuration Reference

```python
# app/config.py - SOTA Configuration

class Settings(BaseSettings):
    # CRAG Configuration
    crag_enabled: bool = True
    crag_classification_threshold: float = 0.6
    crag_use_web_fallback: bool = True
    crag_web_search_provider: str = "tavily"
    
    # Temporal Memory Configuration
    temporal_enabled: bool = True
    temporal_decay_half_life_days: int = 90
    temporal_alpha: float = 0.3  # Weight for temporal vs semantic
    
    # Multi-hop Configuration
    multi_hop_enabled: bool = True
    multi_hop_max_hops: int = 3
    multi_hop_convergence_threshold: float = 0.8
    
    # Continual Learning Configuration
    continual_learning_enabled: bool = True
    feedback_retention_days: int = 90
    evaluation_set_size: int = 500
    retraining_interval_days: int = 7
    
    # Calibration Configuration
    calibration_enabled: bool = True
    calibration_method: str = "isotonic"  # or "platt", "temperature"
    calibration_min_samples: int = 100
    calibration_update_interval_days: int = 7
```

### 8.5 Migration Checklist

```markdown
## Pre-implementation
- [ ] Review current LangGraph workflow
- [ ] Audit database schema
- [ ] Assess LLM API costs
- [ ] Set up feature flag infrastructure
- [ ] Create evaluation benchmarks

## Per-technique Checklist
- [ ] Unit tests written
- [ ] Integration tests passed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Monitoring dashboards created
- [ ] Rollback plan documented

## Pre-launch
- [ ] A/B test configured
- [ ] Canary deployment ready
- [ ] User communication prepared
- [ ] Support team briefed
```

---

*Document Version: 1.0*
*Last Updated: 2024*
*Authors: Orivory Engineering Team*
