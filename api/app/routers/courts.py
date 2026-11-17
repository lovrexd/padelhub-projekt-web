from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.core.schedule import CLUB_TZ
from app.models.user import User
from app.schemas.court import (
    CourtCreate,
    CourtResponse,
    CourtSlotResponse,
    CourtUpdate,
)
from app.services import court_service

router = APIRouter()


@router.get("/", response_model=list[CourtResponse])
async def list_courts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
    surface: str | None = Query(default=None, pattern=r"^(indoor|outdoor)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await court_service.list_courts(db, surface, limit, offset)


@router.post("/", response_model=CourtResponse, status_code=201)
async def create_court(
    body: CourtCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    return await court_service.create_court(db, body)


@router.get("/{court_id}", response_model=CourtResponse)
async def get_court(
    court_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    return await court_service.get_court_or_404(db, court_id)


@router.patch("/{court_id}", response_model=CourtResponse)
async def update_court(
    court_id: int,
    body: CourtUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    return await court_service.update_court(db, court_id, body)


@router.delete("/{court_id}", status_code=204)
async def delete_court(
    court_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    await court_service.delete_court(db, court_id)


@router.get("/{court_id}/availability", response_model=list[CourtSlotResponse])
async def get_court_availability(
    court_id: int,
    day: date = Query(default_factory=lambda: datetime.now(CLUB_TZ).date()),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    return await court_service.get_court_availability(db, court_id, day)
