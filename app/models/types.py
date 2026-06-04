"""Custom SQLAlchemy column types."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator


class EncryptedJSONB(TypeDecorator):
    """A JSONB column whose dict value is encrypted at rest.

    On write, the Python dict is JSON-serialized, encrypted, and stored as a
    single JSON string. On read, the string is decrypted back into a dict.

    Backward compatibility: legacy rows that hold a plain JSON object (dict)
    instead of an encrypted string are returned as-is, so this can be rolled
    out without a data migration. New writes are always encrypted.
    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from app.utils.crypto import encrypt_str

        # Store as an encrypted JSON string value inside the JSONB column.
        return encrypt_str(json.dumps(value, separators=(",", ":"), default=str))

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        # Legacy plaintext dict (pre-encryption rows) — pass through.
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            from app.utils.crypto import decrypt_str

            decrypted = decrypt_str(value)
            try:
                return json.loads(decrypted)
            except (json.JSONDecodeError, TypeError):
                return {}
        return value


__all__ = ["EncryptedJSONB"]
