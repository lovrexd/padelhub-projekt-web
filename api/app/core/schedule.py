from collections.abc import Sequence
from datetime import date, datetime, time
from typing import Protocol
from zoneinfo import ZoneInfo

from app.core.errors import AppError

CLUB_TZ = ZoneInfo("Europe/Zagreb")
OPENING_TIME = time(9, 0)
CLOSING_TIME = time(23, 0)
MIN_BOOKABLE_GAP_SECONDS = 60 * 60
ALLOWED_DURATIONS_SECONDS = (60 * 60, 90 * 60, 120 * 60)
CANCELLATION_DEADLINE_HOURS = 6

# Neradni dani: Nova godina, Božić i Stara godina (uz Uskrs)
FIXED_HOLIDAYS = {(1, 1), (12, 25), (12, 31)}


class HasTimeSlot(Protocol):
    starts_at: datetime
    ends_at: datetime


def calculate_easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    month = (h + el - 7 * m + 114) // 31
    day = ((h + el - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def is_club_holiday(day: date) -> bool:
    return (day.month, day.day) in FIXED_HOLIDAYS or day == calculate_easter_sunday(
        day.year
    )


def club_day_window(starts_at: datetime) -> tuple[datetime, datetime]:
    try:
        local_day = starts_at.astimezone(CLUB_TZ).date()
    except OverflowError:
        raise AppError(
            "outside_working_hours",
            "Igrači mogu rezervirati termine samo unutar radnog vremena (09:00–23:00)",
            400,
        )
    return (
        datetime.combine(local_day, OPENING_TIME, tzinfo=CLUB_TZ),
        datetime.combine(local_day, CLOSING_TIME, tzinfo=CLUB_TZ),
    )


def validate_player_booking_slot(starts_at: datetime, ends_at: datetime) -> None:
    try:
        local_start = starts_at.astimezone(CLUB_TZ)
        local_end = ends_at.astimezone(CLUB_TZ)
    except OverflowError:
        raise AppError(
            "outside_working_hours",
            "Igrači mogu rezervirati termine samo unutar radnog vremena (09:00–23:00)",
            400,
        )

    if (
        local_start.date() != local_end.date()
        or local_start.time() < OPENING_TIME
        or local_end.time() > CLOSING_TIME
    ):
        raise AppError(
            "outside_working_hours",
            "Igrači mogu rezervirati termine samo unutar radnog vremena (09:00–23:00)",
            400,
        )

    if is_club_holiday(local_start.date()):
        raise AppError(
            "club_closed_holiday",
            "Klub ne radi na Božić, Staru godinu, Novu godinu i Uskrs",
            400,
        )

    if (
        local_start.minute not in (0, 30)
        or local_start.second != 0
        or local_start.microsecond != 0
    ):
        raise AppError(
            "invalid_slot_alignment",
            "Termin za igrače mora početi na puni sat ili pola sata (:00 ili :30)",
            400,
        )

    duration_seconds = (ends_at - starts_at).total_seconds()
    if duration_seconds not in ALLOWED_DURATIONS_SECONDS:
        raise AppError(
            "invalid_slot_duration",
            "Igrači mogu rezervirati termin samo na 60, 90 ili 120 minuta",
            400,
        )


def validate_no_orphan_gap(
    starts_at: datetime, ends_at: datetime, day_slots: Sequence[HasTimeSlot]
) -> None:
    day_open, day_close = club_day_window(starts_at)

    prev_ends = [s.ends_at for s in day_slots if s.ends_at <= starts_at]
    next_starts = [s.starts_at for s in day_slots if s.starts_at >= ends_at]

    left_bound = max([day_open, *prev_ends])
    right_bound = min([day_close, *next_starts])

    gap_before = (starts_at - left_bound).total_seconds()
    gap_after = (right_bound - ends_at).total_seconds()

    if (
        0 < gap_before < MIN_BOOKABLE_GAP_SECONDS
        or 0 < gap_after < MIN_BOOKABLE_GAP_SECONDS
    ):
        raise AppError(
            "unusable_gap_left",
            "Rezervacija ne smije ostaviti neiskoristivu rupu manju od 60 minuta",
            400,
        )
