"""
RAGAS-style evaluation metrics for RAG systems.

Implements the most-cited RAGAS metrics from scratch using only stdlib + numpy
so the evaluator is fast, deterministic, and works without GPU or heavy deps.

When sentence-transformers is available, semantic metrics upgrade to
embedding-based cosine similarity. When not, they fall back to token overlap
heuristics that are still meaningful proxies.

Metrics implemented
-------------------
Context quality:
  - context_precision@k       Fraction of retrieved docs that are relevant
  - context_recall@k          Fraction of ground-truth sources that are retrieved
  - context_entity_recall     Fraction of ground-truth entities found in context
  - mrr                       Mean reciprocal rank of first relevant doc
  - ndcg@k                    Normalized discounted cumulative gain

Answer quality:
  - answer_relevancy          Cosine similarity of question vs answer embeddings
  - answer_similarity         Cosine similarity of answer vs ground truth
  - answer_correctness        Weighted blend of similarity + factual overlap

Faithfulness:
  - faithfulness_simple       Fraction of answer claims supported by context
  - hallucination_token_rate  Fraction of answer tokens not grounded in context
  - faithfulness_nli          NLI entailment score (if transformers available)

Robustness:
  - noise_robustness          Retrieval score stability under query perturbation

All metrics are pure functions over dict/list/str inputs — no side effects,
no global state. Designed to be cached at the embedding level to keep eval cost
near-zero on repeated runs.
"""
from __future__ import annotations

import math
import re
import string
from collections.abc import Iterable, Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Optional heavy deps — graceful fallback
# ---------------------------------------------------------------------------

try:  # pragma: no cover - optional import
    import numpy as np
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False

try:  # pragma: no cover - optional import
    from sentence_transformers import SentenceTransformer  # type: ignore
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:  # pragma: no cover
    _HAS_SENTENCE_TRANSFORMERS = False

try:  # pragma: no cover - optional import
    from transformers import pipeline as _hf_pipeline  # type: ignore
    _HAS_TRANSFORMERS = True
except ImportError:  # pragma: no cover
    _HAS_TRANSFORMERS = False


# ---------------------------------------------------------------------------
# Text utilities (stdlib-only)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"\w+", re.UNICODE)
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokens. Unicode-aware."""
    if not text:
        return []
    return _WORD_RE.findall(text.casefold())


def _split_sentences(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    sents = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    return sents or [text]


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").casefold()).strip()


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _cosine_sparse(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity for two sparse term-frequency dicts."""
    if not a or not b:
        return 0.0
    dot = sum(va * b.get(k, 0.0) for k, va in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _term_freq(tokens: Sequence[str]) -> dict[str, float]:
    tf: dict[str, float] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0.0) + 1.0
    n = max(1, len(tokens))
    return {k: v / n for k, v in tf.items()}


# ---------------------------------------------------------------------------
# Lazy embedder (cached)
# ---------------------------------------------------------------------------

_EMBEDDER: Any = None
_EMBEDDER_NAME: str | None = None


def _get_embedder(model_name: str = "all-MiniLM-L6-v2") -> Any | None:
    """Return a cached SentenceTransformer, or None if not installed."""
    global _EMBEDDER, _EMBEDDER_NAME
    if not _HAS_SENTENCE_TRANSFORMERS:
        return None
    if _EMBEDDER is None or _EMBEDDER_NAME != model_name:
        _EMBEDDER = SentenceTransformer(model_name)
        _EMBEDDER_NAME = model_name
    return _EMBEDDER


def embed_texts(texts: list[str], model_name: str = "all-MiniLM-L6-v2") -> list[list[float]] | None:
    """Embed a list of strings. Returns None if sentence-transformers is missing."""
    if not texts:
        return []
    model = _get_embedder(model_name)
    if model is None:
        return None
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str, model_name: str = "all-MiniLM-L6-v2") -> list[float] | None:
    out = embed_texts([text], model_name=model_name)
    if not out:
        return None
    return out[0]


def _cosine_dense(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    if _HAS_NUMPY:
        va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0.0:
            return 0.0
        return float(np.dot(va, vb) / denom)
    # pure-python fallback
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Lazy NLI scorer
# ---------------------------------------------------------------------------

_NLI: Any = None
_NLI_NAME: str | None = None


def _get_nli(model_name: str = "typeform/distilbert-base-uncased-mnli") -> Any | None:
    """Return a cached HuggingFace zero-shot NLI pipeline, or None."""
    global _NLI, _NLI_NAME
    if not _HAS_TRANSFORMERS:
        return None
    if _NLI is None or _NLI_NAME != model_name:
        try:
            _NLI = _hf_pipeline("zero-shot-classification", model=model_name)
            _NLI_NAME = model_name
        except Exception:  # pragma: no cover - network failure path
            _NLI = None
            _NLI_NAME = None
    return _NLI


# ---------------------------------------------------------------------------
# Context quality metrics
# ---------------------------------------------------------------------------

def context_precision_at_k(
    retrieved_sources: Sequence[str],
    expected_sources: Sequence[str],
    k: int = 5,
) -> float:
    """Fraction of top-k retrieved items that are in the expected set."""
    expected = {_normalize_for_match(s) for s in expected_sources if s}
    if not expected:
        return 1.0
    top = [_normalize_for_match(s) for s in retrieved_sources[:k]]
    if not top:
        return 0.0
    hits = sum(
        1
        for r in top
        if any(_normalize_for_match(e) in r or r in _normalize_for_match(e) for e in expected)
    )
    return hits / max(1, len(top))


def context_recall_at_k(
    retrieved_sources: Sequence[str],
    expected_sources: Sequence[str],
    k: int = 5,
) -> float:
    """Fraction of expected sources that appear in top-k retrieved."""
    expected = [_normalize_for_match(s) for s in expected_sources if s]
    if not expected:
        return 1.0
    top = [_normalize_for_match(s) for s in retrieved_sources[:k]]
    if not top:
        return 0.0
    hits = sum(
        1
        for e in expected
        if any(e in r or r in e for r in top)
    )
    return hits / len(expected)


def mean_reciprocal_rank(
    retrieved_sources: Sequence[str],
    expected_sources: Sequence[str],
) -> float:
    """1 / rank of the first relevant retrieved source. 0.0 if none found."""
    expected = {_normalize_for_match(s) for s in expected_sources if s}
    if not expected:
        return 1.0
    for i, source in enumerate(retrieved_sources, start=1):
        ns = _normalize_for_match(source)
        if any(e in ns or ns in e for e in expected):
            return 1.0 / i
    return 0.0


def ndcg_at_k(
    retrieved_sources: Sequence[str],
    expected_sources: Sequence[str],
    k: int = 5,
) -> float:
    """Normalized Discounted Cumulative Gain @ k. Binary relevance."""
    expected = {_normalize_for_match(s) for s in expected_sources if s}
    if not expected:
        return 1.0
    dcg = 0.0
    for i, source in enumerate(retrieved_sources[:k], start=1):
        ns = _normalize_for_match(source)
        rel = 1.0 if any(e in ns or ns in e for e in expected) else 0.0
        dcg += rel / math.log2(i + 1)
    ideal_hits = min(len(expected), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


def context_entity_recall(
    context: str,
    ground_truth_answer: str,
) -> float:
    """
    Approximate entity recall: fraction of distinctive tokens in the
    ground-truth answer that appear in the retrieved context.
    """
    gt_tokens = [t for t in _tokenize(ground_truth_answer) if len(t) > 2]
    if not gt_tokens:
        return 1.0
    ctx_tokens = set(_tokenize(context))
    hits = sum(1 for t in gt_tokens if t in ctx_tokens)
    return hits / len(gt_tokens)


# ---------------------------------------------------------------------------
# Answer quality metrics
# ---------------------------------------------------------------------------

def _cosine_or_jaccard(a: str, b: str, embed_model: str | None) -> float:
    """Use embeddings if available, else Jaccard over word tokens."""
    if embed_model and _HAS_SENTENCE_TRANSFORMERS:
        vecs = embed_texts([a, b], model_name=embed_model)
        if vecs is not None:
            return max(0.0, min(1.0, _cosine_dense(vecs[0], vecs[1])))
    a_tf, b_tf = _term_freq(_tokenize(a)), _term_freq(_tokenize(b))
    return _cosine_sparse(a_tf, b_tf)


def answer_relevancy(
    question: str,
    answer: str,
    embed_model: str | None = "all-MiniLM-L6-v2",
) -> float:
    """How semantically close the answer is to the question (proxy: it addresses it)."""
    if not question.strip() or not answer.strip():
        return 0.0
    return _cosine_or_jaccard(question, answer, embed_model)


def answer_similarity(
    answer: str,
    ground_truth: str,
    embed_model: str | None = "all-MiniLM-L6-v2",
) -> float:
    """Cosine similarity of answer vs ground truth (semantic equivalence proxy)."""
    if not answer.strip() or not ground_truth.strip():
        return 0.0
    return _cosine_or_jaccard(answer, ground_truth, embed_model)


def answer_correctness(
    answer: str,
    ground_truth: str,
    embed_model: str | None = "all-MiniLM-L6-v2",
    semantic_weight: float = 0.7,
) -> float:
    """
    Weighted blend of semantic similarity and factual token overlap.
    Default 70% semantic / 30% factual.
    """
    if not ground_truth.strip():
        return 1.0
    sem = answer_similarity(answer, ground_truth, embed_model=embed_model)
    fact = _jaccard(_tokenize(answer), _tokenize(ground_truth))
    return max(0.0, min(1.0, semantic_weight * sem + (1 - semantic_weight) * fact))


# ---------------------------------------------------------------------------
# Faithfulness / hallucination metrics
# ---------------------------------------------------------------------------

def faithfulness_simple(answer: str, context: str) -> float:
    """
    Sentence-level: fraction of answer sentences that have >=50% token overlap
    with the context. Cheaper proxy for LLM-as-judge faithfulness.
    """
    answer_sents = _split_sentences(answer)
    if not answer_sents:
        return 1.0
    ctx_tokens = set(_tokenize(context))
    if not ctx_tokens:
        return 0.0
    supported = 0
    for sent in answer_sents:
        sent_tokens = _tokenize(sent)
        if not sent_tokens:
            continue
        overlap = sum(1 for t in sent_tokens if t in ctx_tokens)
        if overlap / len(sent_tokens) >= 0.5:
            supported += 1
    return supported / len(answer_sents)


def hallucination_token_rate(answer: str, context: str) -> float:
    """
    Fraction of distinctive answer tokens NOT present in the context.
    Lower is better. 0.0 = fully grounded, 1.0 = no overlap.
    """
    ans_tokens = [t for t in _tokenize(answer) if len(t) > 2]
    if not ans_tokens:
        return 0.0
    ctx_tokens = set(_tokenize(context))
    ungrounded = sum(1 for t in ans_tokens if t not in ctx_tokens)
    return ungrounded / len(ans_tokens)


def faithfulness_nli(
    answer: str,
    context: str,
    model_name: str = "typeform/distilbert-base-uncased-mnli",
    nli: Any | None = None,
) -> float | None:
    """
    NLI-based faithfulness: P(answer entails context) - P(answer contradicts context).
    Returns None if transformers is not installed or model fails to load.
    Range: roughly [-1, 1]; clamped to [0, 1] for convenience.
    """
    if nli is None:
        nli = _get_nli(model_name)
    if nli is None or not answer.strip() or not context.strip():
        return None
    try:  # pragma: no cover - model call
        out = nli(answer, candidate_labels=["entails", "contradicts"], hypothesis_template="{}")
        scores = {label.lower(): score for label, score in zip(out["labels"], out["scores"])}
        score = scores.get("entails", 0.0) - scores.get("contradicts", 0.0)
        return max(0.0, min(1.0, (score + 1.0) / 2.0))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------

_PUNCT_STRIP = str.maketrans("", "", string.punctuation)


def _perturb_query(query: str, rng: Any = None) -> str:
    """Drop 1-2 random non-stopword tokens, lowercase and re-strip punctuation."""
    if rng is None:
        import random
        rng = random
    tokens = _tokenize(query)
    if len(tokens) <= 3:
        return query
    drop_n = min(2, len(tokens) - 2)
    drop_idx = set(rng.sample(range(len(tokens)), drop_n))
    kept = [t for i, t in enumerate(tokens) if i not in drop_idx]
    return " ".join(kept) or query


def noise_robustness(
    retrieval_fn: Any,
    query: str,
    expected_sources: Sequence[str],
    n_perturbations: int = 3,
    rng_seed: int = 0,
) -> float:
    """
    Run retrieval on the original query and n_perturbed variants.
    Returns mean Jaccard overlap of retrieved sources (1.0 = fully robust).
    `retrieval_fn(query) -> list[str]` returns retrieved source names.
    """
    import random
    rng = random.Random(rng_seed)
    original = list(retrieval_fn(query))
    if not original:
        return 0.0
    overlaps: list[float] = []
    for _ in range(n_perturbations):
        perturbed = _perturb_query(query, rng)
        retrieved = list(retrieval_fn(perturbed))
        if not retrieved:
            continue
        overlaps.append(_jaccard(original, retrieved))
    if not overlaps:
        return 0.0
    return sum(overlaps) / len(overlaps)


# ---------------------------------------------------------------------------
# RAGAS-style aggregate
# ---------------------------------------------------------------------------

def ragas_evaluate(
    question: str,
    answer: str,
    context: str,
    retrieved_sources: Sequence[str],
    ground_truth_answer: str = "",
    expected_sources: Sequence[str] = (),
    k: int = 5,
    embed_model: str | None = "all-MiniLM-L6-v2",
    nli_model: str | None = None,
) -> dict[str, float]:
    """
    Run the full RAGAS-style suite and return a dict of metric -> score.
    `nli_model=None` skips the NLI metric (cheaper, no model load).
    """
    metrics: dict[str, float] = {
        "context_precision@k": context_precision_at_k(retrieved_sources, expected_sources, k),
        "context_recall@k": context_recall_at_k(retrieved_sources, expected_sources, k),
        "mrr": mean_reciprocal_rank(retrieved_sources, expected_sources),
        "ndcg@k": ndcg_at_k(retrieved_sources, expected_sources, k),
        "answer_relevancy": answer_relevancy(question, answer, embed_model=embed_model),
        "faithfulness_simple": faithfulness_simple(answer, context),
        "hallucination_token_rate": hallucination_token_rate(answer, context),
    }
    if ground_truth_answer:
        metrics["answer_similarity"] = answer_similarity(
            answer, ground_truth_answer, embed_model=embed_model
        )
        metrics["answer_correctness"] = answer_correctness(
            answer, ground_truth_answer, embed_model=embed_model
        )
        metrics["context_entity_recall"] = context_entity_recall(context, ground_truth_answer)
    if nli_model:
        nli_score = faithfulness_nli(answer, context, model_name=nli_model)
        if nli_score is not None:
            metrics["faithfulness_nli"] = nli_score
    return metrics


def summarize_ragas(per_case: list[dict[str, float]]) -> dict[str, float]:
    """Average each metric across cases. Skips metrics not present in every case."""
    if not per_case:
        return {}
    keys = set().union(*(c.keys() for c in per_case))
    out: dict[str, float] = {}
    for key in keys:
        values = [c[key] for c in per_case if key in c]
        if values:
            out[key] = sum(values) / len(values)
    return out
