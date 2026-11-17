from datetime import datetime
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from app.core.phases import BookingPhase, get_booking_phase
from app.schemas.common import reject_null
from app.schemas.court import CourtBrief


class BookingCreate(BaseModel):
    """Podatci za stvaranje privatne rezervacije ili otvorenog meča."""

    court_id: int
    booking_type: Literal["private", "open_match"]
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    cancellation_deadline: AwareDatetime | None = None
    max_players: Literal[2, 4] = 4
    min_level: float = Field(default=1.0, ge=1.0, le=7.0)
    max_level: float = Field(default=7.0, ge=1.0, le=7.0)

    @model_validator(mode="after")
    def validate_ranges(self) -> "BookingCreate":
        if self.starts_at >= self.ends_at:
            raise ValueError("Početak termina mora biti prije kraja")
        if (
            self.cancellation_deadline is not None
            and self.cancellation_deadline > self.starts_at
        ):
            raise ValueError("Rok za otkazivanje ne može biti nakon početka termina")
        if self.min_level > self.max_level:
            raise ValueError("Minimalna razina ne smije biti veća od maksimalne")
        return self


class BookingUpdate(BaseModel):
    """Podatci za djelomičnu izmjenu vlastite rezervacije (PATCH)."""

    court_id: int | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    cancellation_deadline: AwareDatetime | None = None
    max_players: Literal[2, 4] | None = None
    min_level: float | None = Field(default=None, ge=1.0, le=7.0)
    max_level: float | None = Field(default=None, ge=1.0, le=7.0)

    _not_null = field_validator(
        "court_id",
        "starts_at",
        "ends_at",
        "cancellation_deadline",
        "max_players",
        "min_level",
        "max_level",
        mode="before",
    )(reject_null)


class BookingResponse(BaseModel):
    """Prikaz rezervacije s dinamički izračunatom fazom termina."""

    id: int
    court_id: int
    creator_id: int
    booking_type: str
    starts_at: datetime
    ends_at: datetime
    cancellation_deadline: datetime
    max_players: int
    min_level: float
    max_level: float
    status: str
    created_at: datetime
    court: CourtBrief
    active_players_count: int

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def phase(self) -> BookingPhase:
        return get_booking_phase(self)
