"""Datetime helpers for SQLAlchemy models.

Using datetime.utcnow() directly as a default/onupdate causes issues:
1. It's called at import time, not at row update time
2. datetime.utcnow() is deprecated in Python 3.12+

Use `utc_now` instead as the `onupdate` callable.
"""
from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC datetime for SQLAlchemy onupdate callbacks.

    This is called at row-update time (not import time), unlike using
    datetime.utcnow directly which is deprecated.
    """
    return datetime.now(UTC).replace(tzinfo=None)
