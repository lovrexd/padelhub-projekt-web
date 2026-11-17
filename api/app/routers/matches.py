from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.models.user import User
from app.schemas.match import OpenMatchResponse
from app.services import match_service

router = APIRouter()


@router.get("/", response_model=list[OpenMatchResponse])
async def list_open_matches(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
    court_id: int | None = Query(default=None),
    status: str | None = Query(default=None, pattern=r"^(active|cancelled)$"),
    upcoming_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await match_service.list_open_matches(
        db, court_id, status, upcoming_only, limit, offset
    )


@router.get("/{match_id}", response_model=OpenMatchResponse)
async def get_open_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    return await match_service.get_open_match(db, match_id)


@router.post("/{match_id}/join", response_model=OpenMatchResponse)
async def join_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    return await match_service.join_match(db, match_id, user)


@router.post("/{match_id}/leave", response_model=OpenMatchResponse)
async def leave_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    return await match_service.leave_match(db, match_id, user)
