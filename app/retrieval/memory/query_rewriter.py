"""
Phase 3 — LLM-based query rewriter + entity extractor.

A single LLM call produces BOTH a self-contained rewritten query AND
a list of entities mentioned in the query. The personal context
(recent + pinned memories) is injected so the rewriter can resolve
pronouns like "she", "that project", "yesterday's article".

The function is fully best-effort: on any LLM error, it returns the
original query unchanged with an empty entity list.
"""
from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from app.agents.llm_parsing import parse_llm_json_object
from app.config import settings
from app.models.memory import Memory
from app.retrieval.memory.context import format_personal_context as _format_context

# Re-exported so existing callers / tests that imported _format_context
# from this module continue to work.
__all__ = ["rewrite_query", "_format_context", "_fallback"]

log = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Lazily construct the async OpenAI-compatible client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
    return _client


# System prompt: Vietnamese-friendly, structured JSON output.
REWRITER_SYSTEM = """You are a personal-context query optimizer for a Vietnamese second-brain assistant.
Given the user's query and their recent memories (personal context), produce:

1. ``rewritten_query``: a self-contained version of the query that resolves any
   pronouns, abbreviations, or implicit references using the context.
2. ``entities``: 0-5 named entities (people, projects, topics, dates) the query
   refers to. Match entities that appear in the context if possible.
3. ``reasoning``: one short sentence explaining the rewrite.

## User's query
{query}

## Recent memories (personal context, most recent first)
{context}

---

## Output format
Return ONLY valid JSON. No markdown, no explanation outside the JSON.

{{
  "rewritten_query": "<self-contained version of the query>",
  "entities": [
    {{"name": "<entity name>", "type": "<person|project|topic|concept|organization|place|date|event|other>"}}
  ],
  "reasoning": "<one short sentence>"
}}

## Example
Input query: "what did she say about Atlas?"
Input context: "Mom prefers Project Atlas over Zephyr. 2026-05-12."
Output: {{"rewritten_query": "What did Mom say about Project Atlas?", "entities": [{{"name": "Mom", "type": "person"}}, {{"name": "Project Atlas", "type": "project"}}], "reasoning": "Resolved 'she' -> 'Mom' and 'Atlas' -> 'Project Atlas' from context."}}
## Output:"""





def _fallback(query: str, error: str, raw_preview: str | None = None) -> dict[str, Any]:
    """Return a safe fallback when the LLM call fails or returns bad JSON."""
    return {
        "rewritten_query": query,
        "entities": [],
        "reasoning": f"LLM fallback: {error}",
        "_fallback_used": True,
        "_raw_preview": raw_preview,
    }


async def rewrite_query(
    query: str,
    context: list[Memory] | None = None,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """Rewrite a query and extract entities using the LLM.

    Args:
        query: The raw user query.
        context: Optional list of recent / pinned memories (used to
            resolve pronouns and disambiguate entities).
        model: Optional LLM model override. Defaults to ``settings.LLM_MODEL``.

    Returns:
        Dict with keys:
            - ``rewritten_query`` (str)
            - ``entities`` (list[dict] with ``name`` and ``type``)
            - ``reasoning`` (str)
            - ``_fallback_used`` (bool, internal)
            - ``_raw_preview`` (str | None, internal)
    """
    if not query or not query.strip():
        return _fallback(query, "empty_query")

    try:
        client = _get_client()
        prompt = REWRITER_SYSTEM.format(
            query=query.strip(),
            context=_format_context(context),
        )
        resp = await client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
            extra_headers={
                "HTTP-Referer": settings.FRONTEND_URL,
                "X-Title": "MindLayer Memory Rewriter",
            },
        )
        result_text = resp.choices[0].message.content
        parsed = parse_llm_json_object(result_text)
        if not parsed.ok or parsed.data is None:
            log.warning(
                "Rewriter JSON parsing failed",
                extra={"error": parsed.error},
            )
            return _fallback(query, parsed.error or "invalid_rewriter_json", parsed.raw_preview)

        data = parsed.data
        rewritten = data.get("rewritten_query")
        if not isinstance(rewritten, str) or not rewritten.strip():
            rewritten = query

        raw_entities = data.get("entities", [])
        if not isinstance(raw_entities, list):
            raw_entities = []
        entities: list[dict[str, str]] = []
        for item in raw_entities[:5]:  # cap at 5
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            ent_type = item.get("type", "other")
            if isinstance(name, str) and name.strip():
                entities.append({
                    "name": name.strip(),
                    "type": str(ent_type) if ent_type else "other",
                })

        return {
            "rewritten_query": rewritten.strip(),
            "entities": entities,
            "reasoning": str(data.get("reasoning") or ""),
            "_fallback_used": False,
            "_raw_preview": parsed.raw_preview,
        }

    except Exception as e:
        log.error("Rewriter LLM error", extra={"error": str(e)})
        return _fallback(query, str(e))
