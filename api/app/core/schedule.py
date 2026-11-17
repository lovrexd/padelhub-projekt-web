from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.core.errors import AppError

CLUB_TZ = ZoneInfo("Europe/Zagreb")
OPENING_TIME = time(9, 0)
CLOSING_TIME = time(23, 0)
ALLOWED_DURATIONS_SECONDS = (60 * 60, 90 * 60, 120 * 60)

# Fiksni neradni dani: Nova godina, Božić i Stara godina
FIXED_HOLIDAYS = {(1, 1), (12, 25), (12, 31)}


def calculate_easter_sunday(year: int) -> date:
    """Računa datum katoličkog Uskrsa za zadanu godinu (gregorijanski algoritam)."""
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
    """Vraća True ako klub taj dan ne radi (Nova godina, Uskrs, Božić, Stara)."""
    return (day.month, day.day) in FIXED_HOLIDAYS or day == calculate_easter_sunday(
        day.year
    )


def validate_player_booking_slot(starts_at: datetime, ends_at: datetime) -> None:
    """Provjerava radno vrijeme (09-23), blagdane, poravnanje i trajanje za igrače."""
    local_start = starts_at.astimezone(CLUB_TZ)
    local_end = ends_at.astimezone(CLUB_TZ)

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
