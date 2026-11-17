from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.court import Court


async def get_by_id(db: AsyncSession, court_id: int) -> Court | None:
    """Dohvaća teren po ID-u."""
    return await db.get(Court, court_id)


async def list_courts(
    db: AsyncSession,
    surface: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Court]:
    """Vraća popis padel terena uz opcionalni filtar podloge i straničenje."""
    stmt = select(Court)
    if surface is not None:
        stmt = stmt.where(Court.surface == surface)
    stmt = stmt.order_by(Court.id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, court: Court) -> Court:
    """Sprema novi teren u sesiju baze."""
    db.add(court)
    await db.flush()
    return court


async def delete(db: AsyncSession, court: Court) -> None:
    """Briše teren iz baze."""
    await db.delete(court)
    await db.flush()


async def has_bookings(db: AsyncSession, court_id: int) -> bool:
    """Provjerava ima li teren ijednu postojeću rezervaciju u bazi."""
    stmt = select(exists().where(Booking.court_id == court_id))
    return bool(await db.scalar(stmt))


async def list_occupied_slots(
    db: AsyncSession,
    court_id: int,
    window_start: datetime,
    window_end: datetime,
    exclude_booking_id: int | None = None,
) -> list[Booking]:
    """Vraća aktivne termine na terenu koji se preklapaju sa zadanim prozorom."""
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
