from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse, BookingUpdate
from app.services import booking_service

router = APIRouter()


@router.get("/", response_model=list[BookingResponse])
async def list_bookings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
    court_id: int | None = Query(default=None),
    booking_type: str | None = Query(default=None, pattern=r"^(private|open_match)$"),
    status: str | None = Query(default=None, pattern=r"^(active|cancelled)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Admin vidi sve rezervacije, a igrač isključivo svoje vlastite."""
    return await booking_service.list_bookings(
        db, user, court_id, booking_type, status, limit, offset
    )


@router.post("/", response_model=BookingResponse, status_code=201)
async def create_booking(
    body: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    """Stvara novu privatnu rezervaciju ili otvoreni meč."""
    return await booking_service.create_booking(db, body, user)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    """Vraća detalje pojedine rezervacije (uz provjeru vlasništva)."""
    return await booking_service.get_booking(db, booking_id, user)


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    body: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    """Djelomično mijenja rezervaciju prije isteka roka za izmjenu."""
    return await booking_service.update_booking(db, booking_id, body, user)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    """Otkazuje rezervaciju promjenom statusa u cancelled."""
    return await booking_service.cancel_booking(db, booking_id, user)


@router.post("/{booking_id}/reactivate", response_model=BookingResponse)
async def reactivate_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "player")),
):
    """Ponovno aktivira otkazanu rezervaciju ako termin nije u međuvremenu zauzet."""
    return await booking_service.reactivate_booking(db, booking_id, user)
