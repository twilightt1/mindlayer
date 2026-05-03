"""
Prompt version registry for SupportMind agents.

All agent prompts are loaded from this registry, which:
  - Provides versioned, named variants (e.g. `router_v1`, `router_v2`)
  - Supports per-conversation A/B variant assignment
  - Persists assignment + outcome to Redis (or fallback in-memory map)
  - Exposes helpers for diffing prompts across versions

Usage:

    from app.agents.prompts import PromptRegistry, get_active_variant

    variant = get_active_variant("router", conversation_id="abc-123")
    prompt = PromptRegistry.get("router", variant)
"""
from app.agents.prompts.registry import (  # noqa: F401
    PromptNotFoundError,
    PromptRegistry,
    PromptVariant,
    get_active_variant,
    list_variants,
)
from app.agents.prompts.versions import (  # noqa: F401
    PROMPT_VERSIONS,
    get_default_variants,
)

__all__ = [
    "PromptNotFoundError",
    "PromptRegistry",
    "PromptVariant",
    "get_active_variant",
    "list_variants",
    "PROMPT_VERSIONS",
    "get_default_variants",
]
