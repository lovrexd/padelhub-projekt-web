from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from freezegun import freeze_time

from app.core.phases import BookingPhase, get_booking_phase


def _sample_booking():
    start = datetime(2026, 12, 10, 18, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        starts_at=start,
        cancellation_deadline=start - timedelta(hours=24),
    )


def test_open_change_phase_before_cancellation_deadline():
    b = _sample_booking()
    with freeze_time("2026-12-09 17:59:59+00:00"):
        assert get_booking_phase(b) == BookingPhase.OPEN_CHANGE


def test_locked_phase_at_exact_cancellation_deadline():
    b = _sample_booking()
    with freeze_time("2026-12-09 18:00:00+00:00"):
        assert get_booking_phase(b) == BookingPhase.LOCKED


def test_locked_phase_just_before_start():
    b = _sample_booking()
    with freeze_time("2026-12-10 17:59:59+00:00"):
        assert get_booking_phase(b) == BookingPhase.LOCKED


def test_started_phase_at_exact_start():
    b = _sample_booking()
    with freeze_time("2026-12-10 18:00:00+00:00"):
        assert get_booking_phase(b) == BookingPhase.STARTED
