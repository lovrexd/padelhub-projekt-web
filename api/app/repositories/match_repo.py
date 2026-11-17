from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.match_participant import MatchParticipant
from app.schemas.common import MAX_INT32


def _with_match_details():
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
    if court_id is not None and not (1 <= court_id <= MAX_INT32):
        return []
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


async def get_open_match_by_id(
    db: AsyncSession, match_id: int, for_update: bool = False
) -> Booking | None:
    if not (1 <= match_id <= MAX_INT32):
        return None
    stmt = (
        _with_match_details()
        .where(Booking.id == match_id, Booking.booking_type == "open_match")
        .execution_options(populate_existing=True)
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_participant(
    db: AsyncSession, booking_id: int, player_id: int
) -> MatchParticipant | None:
    stmt = select(MatchParticipant).where(
        MatchParticipant.booking_id == booking_id,
        MatchParticipant.player_id == player_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_participant(
    db: AsyncSession, participant: MatchParticipant
) -> MatchParticipant:
    db.add(participant)
    await db.flush()
    return participant
