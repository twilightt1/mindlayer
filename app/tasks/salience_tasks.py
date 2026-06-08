"""Periodic salience decay (P2.1).

The other half of the salience loop: memories that stop being useful should
fade so they don't crowd ranking forever. This task gently decays the salience
of memories that have not been used within a window, with a floor so nothing
drops to zero (a long-dormant memory can still resurface and climb again via
``bump_salience``). Pinned memories are exempt — the user marked them evergreen.

"Untouched" is measured by ``last_used_at`` when present, else ``captured_at``
(a memory that was never used decays from when it was captured).
"""
from __future__ import annotations

import datetime
import logging

from sqlalchemy import func, update

from app.models.memory import Memory
from app.tasks.celery_app import celery_app
from app.tasks.db import sync_session

log = logging.getLogger(__name__)

# Tunables. Conservative by design — a daily 5% nudge takes ~2 weeks to halve.
DECAY_FACTOR = 0.95
DECAY_FLOOR = 0.1
STALE_AFTER_DAYS = 14


@celery_app.task(name="tasks.decay_stale_salience")
def decay_stale_salience() -> dict:
    """Multiply salience by DECAY_FACTOR for stale, non-pinned memories.

    Returns a summary dict: rows_decayed.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=STALE_AFTER_DAYS)

    # last activity = last_used_at if set, else captured_at
    last_activity = func.coalesce(Memory.last_used_at, Memory.captured_at)

    with sync_session() as db:
        result = db.execute(
            update(Memory)
            .where(
                Memory.pinned.is_(False),
                last_activity < cutoff,
                Memory.salience > DECAY_FLOOR,
            )
            .values(
                salience=func.greatest(Memory.salience * DECAY_FACTOR, DECAY_FLOOR),
            )
        )
        db.commit()
        rows = result.rowcount or 0

    summary = {
        "rows_decayed": rows,
        "factor": DECAY_FACTOR,
        "floor": DECAY_FLOOR,
        "stale_after_days": STALE_AFTER_DAYS,
    }
    log.info("Salience decay complete", extra=summary)
    return summary
