import hashlib
from collections import defaultdict


def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Fuse ranked result lists with Reciprocal Rank Fusion.

    Each fused doc carries a stable ``id`` (parent id, or a content hash when
    the retriever provides no parent) so downstream consumers (CRAG grading,
    dedupe) can reference chunks without a KeyError. When several children of
    the same parent appear, the best-ranked child (lowest rank across all
    lists) is kept as the representative.
    """
    scores:      dict[str, float] = defaultdict(float)
    content_map: dict[str, dict]  = {}
    best_rank:   dict[str, int]   = {}
    for results in result_lists:
        for rank, item in enumerate(results):

            doc_id = item.get("parent_id") or item.get("metadata", {}).get("parent_id")
            if not doc_id:
                doc_id = hashlib.md5(item["content"].encode()).hexdigest()
            scores[doc_id] += 1.0 / (k + rank + 1)
            if doc_id not in best_rank or rank < best_rank[doc_id]:
                best_rank[doc_id] = rank
                content_map[doc_id] = item
    return [
        {**content_map[d], "id": d, "rrf_score": scores[d]}
        for d in sorted(scores, key=scores.get, reverse=True)
    ]
