from datetime import datetime, timezone
from enum import Enum
from typing import Protocol


class HasBookingDeadlines(Protocol):
    starts_at: datetime
    cancellation_deadline: datetime


class BookingPhase(str, Enum):
    OPEN_CHANGE = "open_change"
    LOCKED = "locked"
    STARTED = "started"


def get_booking_phase(booking: HasBookingDeadlines) -> BookingPhase:
    now = datetime.now(timezone.utc)
    if now >= booking.starts_at:
        return BookingPhase.STARTED
    if now >= booking.cancellation_deadline:
        return BookingPhase.LOCKED
    return BookingPhase.OPEN_CHANGE
