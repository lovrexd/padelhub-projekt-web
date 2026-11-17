from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.court import Court


async def get_by_id(db: AsyncSession, court_id: int) -> Court | None:
    """Dohvaća teren po ID-u."""
    return await db.get(Court, court_id)


async def list_courts(
    db: AsyncSession,
    is_active: bool | None = None,
    surface: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Court]:
    """Vraća popis padel terena uz opcionalne filtre i straničenje."""
    stmt = select(Court)
    if is_active is not None:
        stmt = stmt.where(Court.is_active == is_active)
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


async def list_occupied_slots(
    db: AsyncSession,
    court_id: int,
    window_start: datetime,
    window_end: datetime,
) -> list[Booking]:
    """Vraća aktivne termine na terenu koji se preklapaju sa zadanim prozorom."""
    stmt = (
        select(Booking)
        .where(
            Booking.court_id == court_id,
            Booking.status == "active",
            Booking.starts_at < window_end,
            Booking.ends_at > window_start,
        )
        .order_by(Booking.starts_at, Booking.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
