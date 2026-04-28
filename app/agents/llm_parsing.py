from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
MAX_PREVIEW_CHARS = 240


@dataclass(frozen=True)
class LLMJsonParseResult:
    data: dict[str, Any] | None
    error: str | None
    raw_preview: str | None

    @property
    def ok(self) -> bool:
        return self.data is not None and self.error is None


def raw_preview(raw: object, limit: int = MAX_PREVIEW_CHARS) -> str | None:
    if raw is None:
        return None
    text = str(raw).replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _extract_json_candidate(text: str) -> str:
    stripped = text.strip()
    fence_match = JSON_FENCE_RE.search(stripped)
    if fence_match:
        stripped = fence_match.group(1).strip()

    start_idx = stripped.find("{")
    end_idx = stripped.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return stripped[start_idx:end_idx + 1]
    return stripped


def parse_llm_json_object(raw: object) -> LLMJsonParseResult:
    preview = raw_preview(raw)
    if raw is None:
        return LLMJsonParseResult(data=None, error="empty_response", raw_preview=None)

    text = str(raw).strip()
    if not text:
        return LLMJsonParseResult(data=None, error="empty_response", raw_preview=preview)

    candidate = _extract_json_candidate(text)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return LLMJsonParseResult(data=None, error=f"invalid_json: {exc.msg}", raw_preview=preview)

    if not isinstance(parsed, dict):
        return LLMJsonParseResult(data=None, error="json_not_object", raw_preview=preview)

    return LLMJsonParseResult(data=parsed, error=None, raw_preview=preview)


def coerce_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "y", "1"}:
            return True
        if normalized in {"false", "no", "n", "0"}:
            return False
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    return default


def coerce_float(value: object, default: float = 0.0, *, minimum: float | None = None, maximum: float | None = None) -> float:
    try:
        coerced = float(value)
    except (TypeError, ValueError):
        coerced = default
    if minimum is not None:
        coerced = max(minimum, coerced)
    if maximum is not None:
        coerced = min(maximum, coerced)
    return coerced


def coerce_string_list(value: object, *, limit: int = 3) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        if len(result) >= limit:
            break
    return result
