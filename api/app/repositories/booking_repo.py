from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.match_participant import MatchParticipant
from app.schemas.common import MAX_INT32


def _with_details():
    return select(Booking).options(
        selectinload(Booking.court),
        selectinload(Booking.creator),
        selectinload(Booking.participants).selectinload(MatchParticipant.player),
    )


async def get_by_id(
    db: AsyncSession, booking_id: int, for_update: bool = False
) -> Booking | None:
    if not (1 <= booking_id <= MAX_INT32):
        return None
    stmt = (
        _with_details()
        .where(Booking.id == booking_id)
        .execution_options(populate_existing=True)
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_bookings(
    db: AsyncSession,
    creator_id: int | None = None,
    court_id: int | None = None,
    booking_type: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Booking]:
    if court_id is not None and not (1 <= court_id <= MAX_INT32):
        return []
    stmt = _with_details()
    if creator_id is not None:
        stmt = stmt.where(Booking.creator_id == creator_id)
    if court_id is not None:
        stmt = stmt.where(Booking.court_id == court_id)
    if booking_type is not None:
        stmt = stmt.where(Booking.booking_type == booking_type)
    if status is not None:
        stmt = stmt.where(Booking.status == status)
    stmt = stmt.order_by(Booking.starts_at, Booking.id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def has_overlapping_booking(
    db: AsyncSession,
    court_id: int,
    starts_at: datetime,
    ends_at: datetime,
    exclude_booking_id: int | None = None,
) -> bool:
    conditions = [
        Booking.court_id == court_id,
        Booking.status == "active",
        Booking.starts_at < ends_at,
        Booking.ends_at > starts_at,
    ]
    if exclude_booking_id is not None:
        conditions.append(Booking.id != exclude_booking_id)
    stmt = select(exists().where(*conditions))
    return bool(await db.scalar(stmt))


async def create(db: AsyncSession, booking: Booking) -> Booking:
    db.add(booking)
    await db.flush()
    created = await get_by_id(db, booking.id)
    assert created is not None
    return created
