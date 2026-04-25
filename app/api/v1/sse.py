from __future__ import annotations

import json
from typing import Any


def safe_json_dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def format_sse(data: dict[str, Any], event: str | None = None) -> str:
    lines: list[str] = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {safe_json_dumps(data)}")
    return "\n".join(lines) + "\n\n"
