from datetime import datetime, timezone
from enum import Enum
from typing import Protocol


class HasBookingDeadlines(Protocol):
    starts_at: datetime
    cancellation_deadline: datetime


class BookingPhase(str, Enum):
    """Vremenska faza termina izračunata u trenutku zahtjeva."""

    OPEN_CHANGE = "open_change"
    LOCKED = "locked"
    STARTED = "started"


def get_booking_phase(booking: HasBookingDeadlines) -> BookingPhase:
    """Računa trenutnu fazu termina na temelju UTC vremena.

    - open_change: prije cancellation_deadline (dopuštena izmjena, otkaz i odjava)
    - locked: između roka otkazivanja i starts_at (nema otkaza, ali 4. igrač može ući)
    - started: nakon starts_at (termin je počeo ili prošao, sve je zaključano)
    """
    now = datetime.now(timezone.utc)
    if now >= booking.starts_at:
        return BookingPhase.STARTED
    if now >= booking.cancellation_deadline:
        return BookingPhase.LOCKED
    return BookingPhase.OPEN_CHANGE
