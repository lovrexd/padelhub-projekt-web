from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.court import Court
from app.schemas.common import MAX_INT32


async def get_by_id(
    db: AsyncSession, court_id: int, for_update: bool = False
) -> Court | None:
    if not (1 <= court_id <= MAX_INT32):
        return None
    return await db.get(Court, court_id, with_for_update=for_update)


async def list_courts(
    db: AsyncSession,
    surface: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Court]:
    stmt = select(Court)
    if surface is not None:
        stmt = stmt.where(Court.surface == surface)
    stmt = stmt.order_by(Court.id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, court: Court) -> Court:
    db.add(court)
    await db.flush()
    return court


async def delete(db: AsyncSession, court: Court) -> None:
    await db.delete(court)
    await db.flush()


async def has_bookings(db: AsyncSession, court_id: int) -> bool:
    stmt = select(exists().where(Booking.court_id == court_id))
    return bool(await db.scalar(stmt))


async def list_occupied_slots(
    db: AsyncSession,
    court_id: int,
    window_start: datetime,
    window_end: datetime,
    exclude_booking_id: int | None = None,
) -> list[Booking]:
    conditions = [
        Booking.court_id == court_id,
        Booking.status == "active",
        Booking.starts_at < window_end,
        Booking.ends_at > window_start,
    ]
    if exclude_booking_id is not None:
        conditions.append(Booking.id != exclude_booking_id)
    stmt = select(Booking).where(*conditions).order_by(Booking.starts_at, Booking.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
