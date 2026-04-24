# RAG Pipeline Architecture & Design Document

## Overview

This document outlines the architectural changes made to the Retrieval-Augmented Generation (RAG) pipeline to bring it to a production-grade level. The primary goals were to drastically reduce latency, improve system scalability, and enhance retrieval accuracy for the Vietnamese language.

## 1. Flattening the Pipeline (Latency Optimization)

### The Problem
The previous pipeline was heavily nested and sequential. It executed multiple LLM calls back-to-back:
1. `query_rewriter` (LLM)
2. `router_agent` (LLM)
3. Multi-query generation (LLM)
4. Evaluator checks (LLM)
5. Answer generation (LLM)

This sequential processing created a "latency bottleneck" where users could wait 10-15 seconds before the first token appeared.

### The Solution: Combined Routing and Query Processing
We have refactored the `router_agent.py` to handle intent classification, query rewriting, and search variant generation in **a single LLM call** using structured JSON output.

```json
{
  "intent": "rag",
  "confidence": 0.95,
  "reasoning": "User asks about product specs",
  "rewritten_query": "What are the specifications of product X?",
  "search_variants": ["Product X technical details", "Features of product X", "Product X datasheet"]
}
```

### Rationale & Trade-offs
- **Why this approach?** Consolidating multiple tasks into a single LLM prompt significantly cuts down network latency. Models like `openrouter/elephant-alpha` (or similar advanced models) are capable of performing multi-step reasoning and returning complex JSON objects efficiently.
- **Trade-off (Accuracy vs. Latency):** While breaking tasks into distinct prompts *might* theoretically increase accuracy on edge cases, the user experience cost (15s latency) is unacceptable in production. A single, well-crafted structured prompt achieves comparable accuracy with a fraction of the delay.

## 2. Trusting the Reranker & Removing Retry Loops

### The Problem
The pipeline previously used an `evaluator_agent` to grade retrieved chunks using an LLM *before* answering. It also implemented a cyclic retry loop (`retry_count`) that retrieved deeper into the vector database if initial results were deemed poor. This turned the system into a cyclic graph, severely impacting latency. Retrieving deeper results from the same embedding space rarely yielded better answers, instead introducing noise.

### The Solution: Streamlined DAG
- Removed `evaluator_agent` and `contextual_compressor`.
- Removed the cyclic `retry_count` loops in `graph.py` and `retrieval_agent.py`.
- Rely entirely on the **Jina Reranker** (`jina-reranker-v2-base-multilingual`) to surface the top chunks.
- The pipeline is now a pure Directed Acyclic Graph (DAG): `router` -> `memory` -> `retrieval` -> `answer` -> `grade_gen` -> `save`.

### Rationale & Trade-offs
- **Why this approach?** Rerankers (cross-encoders) are specifically trained to evaluate query-document relevance far faster and more consistently than a general-purpose LLM acting as a zero-shot grader. If the top 5 reranked documents do not contain the answer, pulling documents ranked 15-25 is highly unlikely to solve the problem; it is better to fast-fail.
- **Trade-off (Simplicity vs. Deep Search):** We lose the ability to iteratively search the database if the first pass fails. However, we gain predictable latency and prevent the LLM from becoming confused by a massive context window filled with low-relevance chunks.

## 3. Improved BM25 Tokenization for Vietnamese

### The Problem
The in-memory `BM25Retriever` tokenized text using a naive regex: `re.findall(r'\w+', text.lower())`. Since Vietnamese relies heavily on compound words (e.g., "trường học"), splitting by `\w+` breaks semantic meaning, leading to poor keyword search recall.

### The Solution: Bigram Expansion
Updated the tokenizer in `bm25_retriever.py` to generate both unigrams and bigrams:
```python
words = re.findall(r'\w+', text.lower())
bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
return words + bigrams
```

### Rationale & Trade-offs
- **Why this approach?** A full NLP tokenizer (like `pyvi` or `underthesea`) introduces significant dependencies and latency overhead. Generating unigrams and bigrams is a lightweight, zero-dependency heuristic that captures adjacent word pairs, drastically improving keyword match accuracy for Vietnamese compound words.
- **Trade-off (Simplicity vs. Linguistic Accuracy):** Bigram expansion is a heuristic. It will generate nonsense pairs alongside valid compound words. However, BM25 natively handles noise well, making this an acceptable trade-off for speed and zero-dependency deployment.

## 4. Asynchronous Hallucination Checking

### The Problem
The `hallucination_agent` previously blocked the final saving of the conversation state.

### The Solution
The `hallucination_agent` now executes *after* the `answer_agent` has finished generating (and streaming) the response. It acts as a safety net and observability metric rather than a blocking guardrail.

### Rationale
Streaming the answer immediately provides the best UX. If a hallucination is detected post-generation, the system logs it for offline evaluation or could be configured to emit a UI warning flag.

## Limitations & Future Work

1. **In-Memory BM25:** The current `BM25Retriever` relies on an in-memory dictionary (`self._indexes`). While acceptable for a single-node prototype, this is a **critical anti-pattern** for horizontal scaling. 
   - *Recommendation:* Migrate keyword search to Elasticsearch, OpenSearch, or PostgreSQL (`pg_trgm` / `pg_search`).
2. **HyDE Usage:** Hypothetical Document Embeddings (HyDE) are still used in the query processor. While effective for general knowledge, HyDE can perform poorly on highly proprietary internal company data where the LLM might hallucinate incorrect internal jargon.
   - *Recommendation:* Evaluate HyDE's performance specifically on your internal documents; consider disabling it in favor of standard multi-query synonym expansion if accuracy degrades.

## Conclusion
The updated architecture shifts the pipeline from a slow, multi-LLM-call cyclic graph to a fast, predictable DAG. By leveraging the Jina Reranker directly, consolidating routing logic, and improving the tokenizer heuristic, the system is significantly closer to meeting production latency targets (< 3 seconds) while maintaining high retrieval quality.
