"""P2.2 tests: proactive digest helpers (pure logic, no DB)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services.digest_service import _age_label, _same_calendar_day

pytestmark = pytest.mark.rag


class TestAgeLabel:
    def test_years(self):
        assert _age_label(365) == "1 year ago"
        assert _age_label(730) == "2 years ago"

    def test_months(self):
        assert _age_label(180) == "6 months ago"
        assert _age_label(30) == "1 month ago"


class TestSameCalendarDay:
    def test_exact_anniversary(self):
        past = datetime(2024, 6, 17, 9, 0, tzinfo=timezone.utc)
        today = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)
        assert _same_calendar_day(past, today, tolerance_days=2)

    def test_within_tolerance(self):
        past = datetime(2024, 6, 15, tzinfo=timezone.utc)
        today = datetime(2026, 6, 17, tzinfo=timezone.utc)
        assert _same_calendar_day(past, today, tolerance_days=2)

    def test_outside_tolerance(self):
        past = datetime(2024, 6, 10, tzinfo=timezone.utc)
        today = datetime(2026, 6, 17, tzinfo=timezone.utc)
        assert not _same_calendar_day(past, today, tolerance_days=2)

    def test_leap_day_does_not_crash(self):
        past = datetime(2024, 2, 29, tzinfo=timezone.utc)  # leap day
        today = datetime(2026, 2, 28, tzinfo=timezone.utc)  # non-leap year
        # Should fall back to Feb 28 and match, not raise.
        assert _same_calendar_day(past, today, tolerance_days=2)
