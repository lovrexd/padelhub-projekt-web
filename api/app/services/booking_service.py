from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.phases import BookingPhase, get_booking_phase
from app.models.booking import Booking
from app.models.match_participant import MatchParticipant
from app.models.user import User
from app.repositories import booking_repo
from app.schemas.booking import BookingCreate, BookingUpdate
from app.services.court_service import get_court_or_404


def _check_booking_ownership(booking: Booking, current_user: User) -> None:
    """Igrač smije vidjeti i mijenjati samo vlastite rezervacije; admin sve."""
    if current_user.role != "admin" and booking.creator_id != current_user.id:
        raise AppError("forbidden", "Nemate pristup tuđoj rezervaciji", 403)


async def _get_booking_or_404(db: AsyncSession, booking_id: int) -> Booking:
    booking = await booking_repo.get_by_id(db, booking_id)
    if not booking:
        raise AppError("not_found", "Rezervacija nije pronađena", 404)
    return booking


async def list_bookings(
    db: AsyncSession,
    current_user: User,
    court_id: int | None,
    booking_type: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> list[Booking]:
    """Admin vidi sve rezervacije, a igrač isključivo vlastite."""
    creator_id = None if current_user.role == "admin" else current_user.id
    return await booking_repo.list_bookings(
        db, creator_id, court_id, booking_type, status, limit, offset
    )


async def get_booking(db: AsyncSession, booking_id: int, current_user: User) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    _check_booking_ownership(booking, current_user)
    return booking


async def create_booking(
    db: AsyncSession, body: BookingCreate, current_user: User
) -> Booking:
    """Stvara rezervaciju ili otvoreni meč uz provjeru vremena, terena i preklapanja."""
    now = datetime.now(timezone.utc)
    if body.starts_at <= now:
        raise AppError("slot_in_past", "Termin mora biti u budućnosti", 400)

    court = await get_court_or_404(db, body.court_id)

    if await booking_repo.has_overlapping_booking(
        db, court.id, body.starts_at, body.ends_at
    ):
        raise AppError(
            "slot_conflict", "Odabrani termin na ovom terenu je već zauzet", 409
        )

    deadline = (
        body.cancellation_deadline
        if body.cancellation_deadline is not None
        else body.starts_at - timedelta(hours=24)
    )

    booking = Booking(
        court_id=court.id,
        creator_id=current_user.id,
        booking_type=body.booking_type,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        cancellation_deadline=deadline,
        max_players=body.max_players,
        min_level=body.min_level,
        max_level=body.max_level,
    )
    if body.booking_type == "open_match":
        # Kreator otvorenog meča automatski zauzima prvo mjesto (1/max_players)
        booking.participants.append(
            MatchParticipant(player_id=current_user.id, status="active")
        )
    return await booking_repo.create(db, booking)


async def update_booking(
    db: AsyncSession, booking_id: int, body: BookingUpdate, current_user: User
) -> Booking:
    """Mijenja detalje vlastite rezervacije prije isteka roka za izmjene."""
    booking = await get_booking(db, booking_id, current_user)
    if booking.status != "active":
        raise AppError(
            "booking_cancelled", "Otkazana rezervacija ne može se mijenjati", 400
        )
    if get_booking_phase(booking) != BookingPhase.OPEN_CHANGE:
        raise AppError("deadline_passed", "Rok za izmjenu rezervacije je istekao", 400)

    changes = body.model_dump(exclude_unset=True)
    new_court_id = changes.get("court_id", booking.court_id)
    new_starts_at = changes.get("starts_at", booking.starts_at)
    new_ends_at = changes.get("ends_at", booking.ends_at)
    new_deadline = changes.get("cancellation_deadline", booking.cancellation_deadline)
    new_max_players = changes.get("max_players", booking.max_players)
    new_min_level = changes.get("min_level", booking.min_level)
    new_max_level = changes.get("max_level", booking.max_level)

    if new_starts_at <= datetime.now(timezone.utc):
        raise AppError("slot_in_past", "Termin mora biti u budućnosti", 400)
    if new_starts_at >= new_ends_at:
        raise AppError(
            "invalid_time_range", "Početak termina mora biti prije kraja", 400
        )
    if new_deadline > new_starts_at:
        raise AppError(
            "invalid_deadlines",
            "Rok za otkazivanje ne može biti nakon početka termina",
            400,
        )
    if new_min_level > new_max_level:
        raise AppError(
            "invalid_level_range",
            "Minimalna razina ne smije biti veća od maksimalne",
            400,
        )
    if new_max_players < booking.active_players_count:
        raise AppError(
            "capacity_too_low",
            "Kapacitet ne može biti manji od broja već prijavljenih igrača",
            400,
        )

    await get_court_or_404(db, new_court_id)

    if await booking_repo.has_overlapping_booking(
        db,
        new_court_id,
        new_starts_at,
        new_ends_at,
        exclude_booking_id=booking.id,
    ):
        raise AppError(
            "slot_conflict", "Odabrani termin na ovom terenu je već zauzet", 409
        )

    for field, value in changes.items():
        setattr(booking, field, value)
    await db.flush()
    updated = await booking_repo.get_by_id(db, booking.id)
    assert updated is not None
    return updated


async def cancel_booking(
    db: AsyncSession, booking_id: int, current_user: User
) -> Booking:
    """Otkazuje rezervaciju (mijenja status u cancelled) ako nije prošao rok."""
    booking = await get_booking(db, booking_id, current_user)
    if booking.status == "cancelled":
        raise AppError("already_cancelled", "Rezervacija je već otkazana", 400)
    if get_booking_phase(booking) != BookingPhase.OPEN_CHANGE:
        raise AppError("deadline_passed", "Rok za otkazivanje je istekao", 400)

    booking.status = "cancelled"
    await db.flush()
    return booking


async def reactivate_booking(
    db: AsyncSession, booking_id: int, current_user: User
) -> Booking:
    """Ponovno aktivira otkazanu rezervaciju ako je termin još slobodan i u roku."""
    booking = await get_booking(db, booking_id, current_user)
    if booking.status == "active":
        raise AppError("already_active", "Rezervacija je već aktivna", 400)
    if get_booking_phase(booking) != BookingPhase.OPEN_CHANGE:
        raise AppError("deadline_passed", "Rok za ponovnu aktivaciju je istekao", 400)

    await get_court_or_404(db, booking.court_id)

    if await booking_repo.has_overlapping_booking(
        db,
        booking.court_id,
        booking.starts_at,
        booking.ends_at,
        exclude_booking_id=booking.id,
    ):
        raise AppError(
            "slot_conflict", "U međuvremenu je netko drugi rezervirao ovaj termin", 409
        )

    booking.status = "active"
    await db.flush()
    return booking
