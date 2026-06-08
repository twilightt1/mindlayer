import datetime
import logging

from sqlalchemy import update

from app.models.user_quota import UserQuota
from app.tasks.celery_app import celery_app
from app.tasks.db import sync_session

log = logging.getLogger(__name__)


def _utc_today() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


@celery_app.task(name="tasks.reset_daily_quotas")
def reset_daily_quotas() -> None:
    """Reset daily request counters — runs at midnight UTC via Celery Beat."""
    with sync_session() as db:
        db.execute(
            update(UserQuota).values(
                requests_today=0,
                tokens_today=0,
                last_daily_reset=_utc_today(),
            )
        )
        db.commit()
    log.info("Daily quotas reset")


@celery_app.task(name="tasks.reset_monthly_quotas")
def reset_monthly_quotas() -> None:
    """Reset monthly counters — runs at 00:00 UTC on the 1st of each month.

    Guarded by ``last_monthly_reset`` so a re-run within the same month is a
    no-op (idempotent), which matters because Celery Beat can fire a missed
    schedule more than once after downtime.
    """
    today = _utc_today()
    month_start = today.replace(day=1)
    with sync_session() as db:
        db.execute(
            update(UserQuota)
            .where(UserQuota.last_monthly_reset < month_start)
            .values(
                requests_month=0,
                tokens_month=0,
                last_monthly_reset=today,
            )
        )
        db.commit()
    log.info("Monthly quotas reset")
