"""Application-layer encryption for secrets stored at rest.

Used to encrypt connector credentials (``Source.config``) so a database
snapshot does not leak OAuth tokens / API keys in plaintext.

Design:
    - A single process-wide Fernet built from ``CONFIG_ENCRYPTION_KEY``.
    - In non-production, if no key is configured, one is derived
      deterministically from ``JWT_SECRET_KEY`` so local dev works without
      extra setup. Production requires an explicit key (enforced in config).
    - Encryption is transparent and backward compatible: ciphertext is a
      string prefixed with a small marker so legacy plaintext rows can be
      detected and passed through on read.
"""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

# Marker prefix identifying values this module produced. Anything without it
# is treated as legacy plaintext and returned unchanged on decrypt.
_PREFIX = "enc::v1::"


def _derive_key_from_secret(secret: str) -> bytes:
    """Derive a urlsafe-base64 32-byte Fernet key from an arbitrary secret."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    raw = settings.CONFIG_ENCRYPTION_KEY.strip()
    if raw:
        # Accept either a proper Fernet key or any string (derive from it).
        try:
            return Fernet(raw.encode("utf-8"))
        except (ValueError, TypeError):
            return Fernet(_derive_key_from_secret(raw))
    # Non-production fallback: derive from JWT secret. Production config
    # validation rejects an empty CONFIG_ENCRYPTION_KEY before we get here.
    return Fernet(_derive_key_from_secret(settings.JWT_SECRET_KEY))


def encrypt_str(plaintext: str) -> str:
    """Encrypt a string and return a marked, storable token."""
    token = _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"{_PREFIX}{token}"


def decrypt_str(value: str) -> str:
    """Decrypt a value produced by :func:`encrypt_str`.

    Values without the marker prefix are assumed to be legacy plaintext and
    returned unchanged, so existing rows keep working after rollout.
    """
    if not value.startswith(_PREFIX):
        return value
    token = value[len(_PREFIX):]
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Wrong/rotated key — fail loud rather than silently returning garbage.
        raise ValueError("Failed to decrypt value: key mismatch or corrupted data")


def is_encrypted(value: str) -> bool:
    return isinstance(value, str) and value.startswith(_PREFIX)
