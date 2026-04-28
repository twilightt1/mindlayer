"""
Prompt variant data class.

Lives in its own module to avoid a circular import between
`registry.py` and `versions.py`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class PromptVariant:
    name: str
    agent: str
    template: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def render(self, **kwargs: Any) -> str:
        """Render the template with the given placeholders."""
        return self.template.format(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptVariant:
        return cls(
            name=data["name"],
            agent=data["agent"],
            template=data["template"],
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
        )
