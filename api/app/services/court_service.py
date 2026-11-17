from datetime import date, datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.booking import Booking
from app.models.court import Court
from app.repositories import court_repo
from app.schemas.court import CourtCreate, CourtUpdate


async def get_court_or_404(db: AsyncSession, court_id: int) -> Court:
    """Dohvaća teren ili baca 404 ako ne postoji."""
    court = await court_repo.get_by_id(db, court_id)
    if not court:
        raise AppError("not_found", "Teren nije pronađen", 404)
    return court


async def list_courts(
    db: AsyncSession,
    surface: str | None,
    limit: int,
    offset: int,
) -> list[Court]:
    """Vraća straničeni popis terena."""
    return await court_repo.list_courts(db, surface, limit, offset)


async def create_court(db: AsyncSession, body: CourtCreate) -> Court:
    """Dodaje novi padel teren uz provjeru jedinstvenosti naziva."""
    court = Court(**body.model_dump())
    try:
        return await court_repo.create(db, court)
    except IntegrityError:
        raise AppError("duplicate", "Teren s tim nazivom već postoji", 409)


async def update_court(db: AsyncSession, court_id: int, body: CourtUpdate) -> Court:
    """Mijenja samo poslana polja postojećeg terena."""
    court = await get_court_or_404(db, court_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(court, field, value)
    try:
        await db.flush()
    except IntegrityError:
        raise AppError("duplicate", "Teren s tim nazivom već postoji", 409)
    return court


async def delete_court(db: AsyncSession, court_id: int) -> None:
    """Briše teren ako na njemu nema nikakvih rezervacija."""
    court = await get_court_or_404(db, court_id)
    if await court_repo.has_bookings(db, court.id):
        raise AppError(
            "has_bookings",
            "Teren ima postojeće rezervacije i ne može se obrisati",
            409,
        )
    try:
        await court_repo.delete(db, court)
    except IntegrityError:
        raise AppError(
            "has_bookings",
            "Teren ima postojeće rezervacije i ne može se obrisati",
            409,
        )


async def get_court_availability(
    db: AsyncSession, court_id: int, day: date
) -> list[Booking]:
    """Vraća zauzete vremenske raspone za teren na zadani UTC dan."""
    await get_court_or_404(db, court_id)
    window_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    window_end = window_start + timedelta(days=1)
    return await court_repo.list_occupied_slots(db, court_id, window_start, window_end)
