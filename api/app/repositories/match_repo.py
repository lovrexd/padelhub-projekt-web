from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.match_participant import MatchParticipant


def _with_match_details():
    """Učitava teren i sudionike otvorenog meča unaprijed (bez N+1 upita)."""
    return select(Booking).options(
        selectinload(Booking.court),
        selectinload(Booking.participants).selectinload(MatchParticipant.player),
    )


async def list_open_matches(
    db: AsyncSession,
    court_id: int | None = None,
    status: str | None = None,
    upcoming_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[Booking]:
    """Dohvaća javne otvorene mečeve uz filtre i straničenje."""
    stmt = _with_match_details().where(Booking.booking_type == "open_match")
    if court_id is not None:
        stmt = stmt.where(Booking.court_id == court_id)
    if status is not None:
        stmt = stmt.where(Booking.status == status)
    if upcoming_only:
        stmt = stmt.where(Booking.starts_at > datetime.now(timezone.utc))
    stmt = stmt.order_by(Booking.starts_at, Booking.id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_open_match_by_id(db: AsyncSession, match_id: int) -> Booking | None:
    """Dohvaća pojedini otvoreni meč; privatne rezervacije ovdje ne postoje."""
    stmt = (
        _with_match_details()
        .where(Booking.id == match_id, Booking.booking_type == "open_match")
        .execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_participant(
    db: AsyncSession, booking_id: int, player_id: int
) -> MatchParticipant | None:
    """Traži postoji li već zapis igrača u tom meču (aktivan ili odjavljen)."""
    stmt = select(MatchParticipant).where(
        MatchParticipant.booking_id == booking_id,
        MatchParticipant.player_id == player_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_participant(
    db: AsyncSession, participant: MatchParticipant
) -> MatchParticipant:
    """Dodaje sudionika u otvoreni meč."""
    db.add(participant)
    await db.flush()
    return participant
