"""Shared LLM client factory for all agents.

One place for: client construction (api key, base URL, timeout, retries),
a request-scope cost hook that feeds `cost_helpers.record_cost`, and a
uniform `complete()` wrapper that records usage automatically.

Every agent used to hand-roll its own module-level `AsyncOpenAI` singleton
(12 copies) with no timeout and no cost recording — a hung OpenRouter call
stalled an SSE stream for the SDK default 600s, and a single turn firing
up to ~40 LLM calls had zero spend observability.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

log = logging.getLogger(__name__)

# Per-attempt LLM call timeout. Deliberately tighter than the SDK default of
# 600s: the answer path chains up to ~10 serial stages, and one hung call
# must not stall an SSE stream for 10 minutes.
DEFAULT_LLM_TIMEOUT_SECONDS = 60.0
DEFAULT_LLM_MAX_RETRIES = 2

_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    """Return the shared configured AsyncOpenAI client (OpenRouter by default)."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=DEFAULT_LLM_TIMEOUT_SECONDS,
            max_retries=DEFAULT_LLM_MAX_RETRIES,
        )
    return _client


def _usage_to_tokens(usage: Any) -> tuple[int, int]:
    """Best-effort extraction of (tokens_in, tokens_out) from a usage object."""
    if usage is None:
        return 0, 0
    tokens_in = int(getattr(usage, "prompt_tokens", 0) or 0)
    tokens_out = int(getattr(usage, "completion_tokens", 0) or 0)
    if not tokens_in and not tokens_out:
        total = int(getattr(usage, "total_tokens", 0) or 0)
        tokens_in = total
    return tokens_in, tokens_out


def record_usage(
    state: dict[str, Any] | None,
    agent: str,
    model: str,
    usage: Any,
) -> None:
    """Record token usage/cost for a completion into AgentState + the ledger.

    Fire-and-forget by design: cost tracking must never break a request.
    """
    if state is None:
        return
    tokens_in, tokens_out = _usage_to_tokens(usage)
    if not tokens_in and not tokens_out:
        return
    try:
        from app.agents.cost_helpers import record_cost

        record_cost(
            agent=agent,
            state=state,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
    except Exception:  # pragma: no cover — observability must not break requests
        log.debug("Cost recording failed", exc_info=True)


async def complete(
    *,
    agent: str,
    state: dict[str, Any] | None = None,
    model: str | None = None,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int | None = None,
    response_format: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> Any:
    """Run a chat completion with usage/cost recording built in.

    Returns the raw completion object (callers read `.choices[0].message`).
    """
    client = get_llm_client()
    response = await client.chat.completions.create(
        model=model or settings.LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        response_format=response_format,
        extra_headers=extra_headers,
        timeout=timeout or DEFAULT_LLM_TIMEOUT_SECONDS,
    )
    record_usage(state, agent, model or settings.LLM_MODEL, getattr(response, "usage", None))
    return response


async def complete_stream(
    *,
    agent: str,
    state: dict[str, Any] | None = None,
    model: str | None = None,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> AsyncIterator[Any]:
    """Stream a chat completion, recording usage at the end of the stream.

    Usage chunks are only emitted when the request asks for them; the final
    chunk (if any) carries `usage`.
    """
    client = get_llm_client()
    stream = await client.chat.completions.create(
        model=model or settings.LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        extra_headers=extra_headers,
        timeout=timeout or DEFAULT_LLM_TIMEOUT_SECONDS,
        stream=True,
    )
    last_usage: Any = None
    try:
        async for chunk in stream:
            if getattr(chunk, "usage", None):
                last_usage = chunk.usage
            yield chunk
    finally:
        if last_usage is not None:
            record_usage(state, agent, model or settings.LLM_MODEL, last_usage)
        close = getattr(stream, "close", None)
        if close is not None:
            result = close()
            if asyncio.iscoroutine(result):
                try:
                    await result
                except Exception:  # pragma: no cover
                    pass
