"""
Prompt registry: store, fetch, A/B-assign, and track outcomes for agent prompts.

The registry is the single source of truth for prompt variants. Agents call
`PromptRegistry.get(agent_name, variant_name)` to fetch the rendered prompt
template. A/B variant assignment for a given conversation is deterministic by
default (hash-based), so the same conversation always gets the same variant
unless explicitly overridden.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.agents.prompts.variant import PromptVariant  # noqa: F401 (re-export)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PromptNotFoundError(KeyError):
    """Raised when an agent or variant is not in the registry."""

    def __init__(self, agent: str, variant: str | None = None) -> None:
        if variant:
            msg = f"No prompt variant '{variant}' for agent '{agent}'"
        else:
            msg = f"No prompt variants registered for agent '{agent}'"
        super().__init__(msg)
        self.agent = agent
        self.variant = variant


# ---------------------------------------------------------------------------
# Variant data class is defined in `app.agents.prompts.variant`
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Assignment store (Redis if available, else in-memory)
# ---------------------------------------------------------------------------


class _AssignmentStore:
    """Persist conversation_id -> variant_name per agent."""

    def __init__(self) -> None:
        self._mem: dict[str, str] = {}
        self._redis: Any = None
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis  # type: ignore

            url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(url, decode_responses=True, socket_timeout=1)
            self._redis.ping()
        except Exception:  # pragma: no cover - redis optional
            self._redis = None

    def _key(self, agent: str, conversation_id: str) -> str:
        return f"prompt_assignment:{agent}:{conversation_id}"

    def get(self, agent: str, conversation_id: str) -> str | None:
        if self._redis is not None:
            try:
                return self._redis.get(self._key(agent, conversation_id))
            except Exception:  # pragma: no cover
                pass
        return self._mem.get(self._key(agent, conversation_id))

    def set(self, agent: str, conversation_id: str, variant: str) -> None:
        if self._redis is not None:
            try:
                self._redis.set(self._key(agent, conversation_id), variant)
                return
            except Exception:  # pragma: no cover
                pass
        self._mem[self._key(agent, conversation_id)] = variant


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class PromptRegistry:
    """Central registry for prompt variants."""

    _variants: dict[str, dict[str, PromptVariant]] = {}
    _store = _AssignmentStore()
    _custom_loaders: list[Any] = []

    @classmethod
    def register(cls, variant: PromptVariant) -> None:
        cls._variants.setdefault(variant.agent, {})[variant.name] = variant

    @classmethod
    def register_many(cls, variants: Iterable[PromptVariant]) -> None:
        for v in variants:
            cls.register(v)

    @classmethod
    def register_from_versions_module(cls) -> None:
        """Load all built-in versions from `app.agents.prompts.versions`."""
        # Import inside the method to avoid circular import at module load.
        from app.agents.prompts.versions import PROMPT_VERSIONS  # type: ignore
        for variants in PROMPT_VERSIONS.values():
            cls.register_many(variants)

    @classmethod
    def register_from_file(cls, path: str | Path) -> int:
        """Load variant definitions from a JSON file. Returns count loaded."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            items = data.get("variants", [])
        else:
            items = data
        for item in items:
            cls.register(PromptVariant.from_dict(item))
        return len(items)

    @classmethod
    def list_agents(cls) -> list[str]:
        return sorted(cls._variants.keys())

    @classmethod
    def list_variants(cls, agent: str | None = None) -> list[PromptVariant]:
        if agent is None:
            return [v for vs in cls._variants.values() for v in vs.values()]
        if agent not in cls._variants:
            return []
        return list(cls._variants[agent].values())

    @classmethod
    def get(cls, agent: str, variant: str | None = None) -> PromptVariant:
        if not cls._variants:
            cls.register_from_versions_module()
        if agent not in cls._variants:
            raise PromptNotFoundError(agent)
        variants = cls._variants[agent]
        if not variants:
            raise PromptNotFoundError(agent)
        if variant is None:
            # Use first (default) variant
            return next(iter(variants.values()))
        if variant not in variants:
            raise PromptNotFoundError(agent, variant)
        return variants[variant]

    # -- A/B assignment ------------------------------------------------------

    @classmethod
    def assign(
        cls,
        agent: str,
        conversation_id: str,
        variants: Iterable[str] | None = None,
        force: str | None = None,
    ) -> str:
        """Assign a variant to a conversation. Deterministic by default."""
        if force is not None:
            cls._store.set(agent, conversation_id, force)
            return force
        existing = cls._store.get(agent, conversation_id)
        if existing:
            return existing
        if not variants:
            # Lazy import to avoid cycle
            from app.agents.prompts.versions import get_default_variants  # type: ignore

            variants = [v.name for v in cls.list_variants(agent)] or [
                get_default_variants().get(agent, "default")
            ]
        names = list(variants)
        if not names:
            raise PromptNotFoundError(agent)
        # Hash-based deterministic assignment
        h = hashlib.sha1(f"{agent}:{conversation_id}".encode("utf-8")).hexdigest()
        idx = int(h, 16) % len(names)
        chosen = names[idx]
        cls._store.set(agent, conversation_id, chosen)
        return chosen

    @classmethod
    def get_assignment(cls, agent: str, conversation_id: str) -> str | None:
        return cls._store.get(agent, conversation_id)

    # -- Comparison ---------------------------------------------------------

    @classmethod
    def diff(cls, agent: str, a: str, b: str) -> dict[str, Any]:
        """Return a structured diff between two variants of the same agent."""
        va = cls.get(agent, a)
        vb = cls.get(agent, b)
        return {
            "agent": agent,
            "variants": [a, b],
            "len_a": len(va.template),
            "len_b": len(vb.template),
            "length_delta_pct": round(100.0 * (len(vb.template) - len(va.template)) / max(1, len(va.template)), 1),
            "a_metadata": va.metadata,
            "b_metadata": vb.metadata,
        }


# Eager-register built-ins on import so the registry is always populated.
PromptRegistry.register_from_versions_module()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def get_active_variant(agent: str, conversation_id: str | None = None) -> str:
    """Return the variant name to use for the given agent + conversation."""
    if not conversation_id:
        # Lazy import to avoid cycle
        from app.agents.prompts.versions import get_default_variants  # type: ignore

        return get_default_variants().get(agent, f"{agent}_v1")
    return PromptRegistry.assign(agent, conversation_id)


def list_variants(agent: str | None = None) -> list[str]:
    return [v.name for v in PromptRegistry.list_variants(agent)]
