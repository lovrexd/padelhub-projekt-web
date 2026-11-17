from datetime import datetime, timezone

from freezegun import freeze_time

from app.core.phases import BookingPhase, get_booking_phase
from app.models import Booking

BOOKING = Booking(
    court_id=1,
    creator_id=1,
    booking_type="private",
    cancellation_deadline=datetime(2026, 12, 25, 12, 0, tzinfo=timezone.utc),
    starts_at=datetime(2026, 12, 25, 18, 0, tzinfo=timezone.utc),
    ends_at=datetime(2026, 12, 25, 19, 30, tzinfo=timezone.utc),
)


@freeze_time("2026-12-25 11:59:59")
def test_open_just_before_cancellation_deadline():
    assert get_booking_phase(BOOKING) == BookingPhase.OPEN_CHANGE


@freeze_time("2026-12-25 12:00:00")
def test_locked_at_cancellation_deadline():
    assert get_booking_phase(BOOKING) == BookingPhase.LOCKED


@freeze_time("2026-12-25 18:00:00")
def test_started_at_start():
    assert get_booking_phase(BOOKING) == BookingPhase.STARTED
