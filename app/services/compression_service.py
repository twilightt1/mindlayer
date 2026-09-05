"""Compression-before-storage — the claude-mem lesson, Orivory-flavored.

Long tool outputs and pasted transcripts waste tokens when stored raw and
crowd retrieval. When ``COMPRESSION_ENABLED`` is on (default **off** — the
flag exists so behaviour is opt-in and deterministic in tests), a memory
whose content exceeds ``COMPRESSION_THRESHOLD_CHARS`` gets an AI-written
summary + a compressed body before persisting.

Design constraints (why a seam function, not inline logic):
- The summarize call is best-effort: any LLM failure degrades to storing
  the original content unchanged — a compression outage must never block a
  write (the same graceful-degradation rule claude-mem's hooks follow).
- The summarizer runs through the existing OpenAI-compatible client so lite
  mode and full mode share one code path.
- ``summary`` (one-line) and the compressed ``content`` are returned to the
  caller, which persists them; this module never touches the DB.
"""
from __future__ import annotations

import logging

from app.config import settings

log = logging.getLogger(__name__)

COMPRESSION_MARKER = "[compressed by orivory]"

_SYSTEM_PROMPT = (
    "You compress AI-agent session notes for long-term storage. Given a note, "
    "return STRICT JSON with two keys and nothing else: "
    '{"summary": "<one sentence, <=160 chars>", '
    '"content": "<the durable facts, <=40% of the original length, keep ids, '
    'paths, decisions, and numbers verbatim>"}'
)


def should_compress(content: str) -> bool:
    """Gate: flag on AND content long enough to be worth a round-trip."""
    return bool(
        getattr(settings, "COMPRESSION_ENABLED", False)
        and content
        and len(content) >= settings.COMPRESSION_THRESHOLD_CHARS
    )


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _parse_verdict(text: str, original: str) -> tuple[str, str] | None:
    """Parse the model's strict-JSON answer; None on any deviation."""
    import json

    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    summary = payload.get("summary")
    compressed = payload.get("content")
    if not isinstance(summary, str) or not summary.strip():
        return None
    if not isinstance(compressed, str) or not compressed.strip():
        return None
    # Never accept a "compression" that grew the content.
    if len(compressed) > len(original):
        return None
    return _clip(summary.strip(), 200), compressed.strip()


async def compress_memory(content: str) -> tuple[str, str] | None:
    """Compress one memory body.

    Returns ``(summary, compressed_content)`` on success, or ``None`` when
    compression is disabled/not-worth-it or the LLM failed — callers store
    the original content in that case (never block a write).
    """
    if not should_compress(content):
        return None
    try:
        from openai import AsyncOpenAI

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise RuntimeError("no OPENAI_API_KEY configured")
        client = AsyncOpenAI(api_key=api_key)
        completion = await client.chat.completions.create(
            model=settings.COMPRESSION_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content[: 4 * settings.COMPRESSION_THRESHOLD_CHARS]},
            ],
            temperature=0.0,
            max_tokens=1024,
        )
        verdict = _parse_verdict(completion.choices[0].message.content or "", content)
        if verdict is None:
            log.warning("compression output rejected (malformed JSON or grew content)")
            return None
        summary, compressed = verdict
        compressed = f"{compressed}\n\n{COMPRESSION_MARKER}"
        log.info("memory compressed", extra={"orig": len(content), "new": len(compressed)})
        return summary, compressed
    except Exception as exc:
        log.warning("compression unavailable, storing raw: %s", exc)
        return None
