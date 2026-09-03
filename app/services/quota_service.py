"""User quota enforcement."""
import datetime as dt
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_quota import UserQuota


async def _inline_reset_if_stale(quota: UserQuota, db: AsyncSession) -> bool:
    """Reset counters inline when the beat-driven reset missed this row.

    Returns True if a reset was applied. This is the safety net that keeps
    quotas working when Celery Beat is down: without it a missed midnight
    reset leaves the user hard-blocked at 429 until the beat recovers.
    """
    today = dt.datetime.now(dt.UTC).date()
    month_start = today.replace(day=1)
    if quota.last_daily_reset >= today and quota.last_monthly_reset >= month_start:
        return False

    await db.execute(
        update(UserQuota)
        .where(UserQuota.user_id == quota.user_id)
        .values(
            requests_today=0,
            tokens_today=0,
            requests_month=0,
            tokens_month=0,
            last_daily_reset=today,
            last_monthly_reset=month_start,
        )
    )
    await db.commit()
    await db.refresh(quota)
    return True


async def check_and_increment(user_id: UUID, db: AsyncSession) -> None:
    """Atomically reserve one request against the user's quota.

    Uses a single conditional UPDATE so concurrent requests cannot both
    observe the same pre-increment counters and overshoot the limit
    (TOCTOU). If no row is updated, we re-read the row to decide whether
    the cause was the daily or monthly cap (or simply no quota row, which
    means quotas are not enforced for this user).
    """
    result = await db.execute(
        update(UserQuota)
        .where(
            UserQuota.user_id == user_id,
            UserQuota.requests_today < UserQuota.daily_limit,
            UserQuota.requests_month < UserQuota.monthly_limit,
        )
        .values(
            requests_today=UserQuota.requests_today + 1,
            requests_month=UserQuota.requests_month + 1,
        )
    )

    if result.rowcount and result.rowcount > 0:
        await db.commit()
        return

    # No row incremented: either the user has no quota row (unlimited) or a
    # cap was hit. Re-read to return the correct message without racing.
    quota = await db.scalar(select(UserQuota).where(UserQuota.user_id == user_id))
    if not quota:
        return  # no quota configured -> unlimited

    # Stale counters (missed midnight/monthly reset) — apply the reset
    # inline, then re-run the increment once.
    if await _inline_reset_if_stale(quota, db):
        result = await db.execute(
            update(UserQuota)
            .where(
                UserQuota.user_id == user_id,
                UserQuota.requests_today < UserQuota.daily_limit,
                UserQuota.requests_month < UserQuota.monthly_limit,
            )
            .values(
                requests_today=UserQuota.requests_today + 1,
                requests_month=UserQuota.requests_month + 1,
            )
        )
        if result.rowcount and result.rowcount > 0:
            await db.commit()
            return

    if quota.requests_today >= quota.daily_limit:
        raise HTTPException(429, detail="Daily quota exceeded.")
    if quota.requests_month >= quota.monthly_limit:
        raise HTTPException(429, detail="Monthly quota exceeded.")

    # Reached only under a rare lost race (counters changed between UPDATE
    # and re-read). Treat as exhausted rather than silently allowing.
    raise HTTPException(429, detail="Quota exceeded.")
