from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.phases import BookingPhase, get_booking_phase
from app.models.booking import Booking
from app.models.match_participant import MatchParticipant
from app.models.user import User
from app.repositories import match_repo


async def list_open_matches(
    db: AsyncSession,
    court_id: int | None,
    status: str | None,
    upcoming_only: bool,
    limit: int,
    offset: int,
) -> list[Booking]:
    return await match_repo.list_open_matches(
        db, court_id, status, upcoming_only, limit, offset
    )


async def get_open_match(
    db: AsyncSession, match_id: int, for_update: bool = False
) -> Booking:
    match = await match_repo.get_open_match_by_id(db, match_id, for_update=for_update)
    if not match:
        raise AppError("not_found", "Otvoreni meč nije pronađen", 404)
    return match


async def join_match(db: AsyncSession, match_id: int, current_user: User) -> Booking:
    match = await get_open_match(db, match_id, for_update=True)
    if match.status != "active":
        raise AppError("match_cancelled", "Otvoreni meč je otkazan", 400)

    if get_booking_phase(match) == BookingPhase.STARTED:
        raise AppError(
            "match_started", "Meč je već počeo i nije se moguće pridružiti", 400
        )

    if not (match.min_level <= current_user.skill_level <= match.max_level):
        raise AppError(
            "skill_out_of_range",
            "Vaša razina igre ne odgovara traženom rasponu ovog meča",
            400,
        )

    existing = await match_repo.get_participant(db, match.id, current_user.id)
    if existing is not None and existing.status == "active":
        raise AppError("already_joined", "Već ste prijavljeni u ovaj otvoreni meč", 409)

    if match.active_players_count >= match.max_players:
        raise AppError("match_full", "Otvoreni meč je već popunjen", 409)

    now = datetime.now(timezone.utc)
    if existing is not None:
        # Odjavljeni igrač ponovno ulazi aktiviranjem postojećeg zapisa
        existing.status = "active"
        existing.joined_at = now
        await db.flush()
    else:
        participant = MatchParticipant(
            booking_id=match.id,
            player_id=current_user.id,
            status="active",
            joined_at=now,
        )
        try:
            await match_repo.add_participant(db, participant)
        except IntegrityError:
            raise AppError(
                "already_joined", "Već ste prijavljeni u ovaj otvoreni meč", 409
            )

    return await get_open_match(db, match.id)


async def leave_match(db: AsyncSession, match_id: int, current_user: User) -> Booking:
    match = await get_open_match(db, match_id, for_update=True)
    if match.status != "active":
        raise AppError("match_cancelled", "Otvoreni meč je otkazan", 400)

    if match.creator_id == current_user.id:
        raise AppError(
            "creator_cannot_leave",
            "Kreator meča mora otkazati termin na /bookings umjesto odjave",
            400,
        )

    existing = await match_repo.get_participant(db, match.id, current_user.id)
    if existing is None or existing.status != "active":
        raise AppError(
            "not_a_participant", "Niste aktivni sudionik ovog otvorenog meča", 400
        )

    if get_booking_phase(match) != BookingPhase.OPEN_CHANGE:
        raise AppError("deadline_passed", "Rok za odjavu iz meča je istekao", 400)

    existing.status = "left"
    await db.flush()
    return await get_open_match(db, match.id)
