from datetime import datetime
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    StrictInt,
    computed_field,
    field_validator,
)

from app.core.phases import BookingPhase, get_booking_phase
from app.schemas.common import reject_null
from app.schemas.court import CourtBrief


class BookingCreate(BaseModel):
    court_id: StrictInt = Field(ge=1)
    booking_type: Literal["private", "open_match"]
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    max_players: Literal[2, 4] = 4
    min_level: float = Field(default=1.0, ge=1.0, le=7.0)
    max_level: float = Field(default=7.0, ge=1.0, le=7.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "court_id": 1,
                "booking_type": "private",
                "starts_at": "2027-03-15 18:00+01:00",
                "ends_at": "2027-03-15 19:30+01:00",
            }
        }
    }

    @field_validator("ends_at")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("starts_at")
        if start and v <= start:
            raise ValueError("Početak termina mora biti prije kraja")
        return v

    @field_validator("max_level")
    @classmethod
    def max_not_below_min(cls, v: float, info) -> float:
        min_lvl = info.data.get("min_level")
        if min_lvl is not None and v < min_lvl:
            raise ValueError("Minimalna razina ne smije biti veća od maksimalne")
        return v


class BookingUpdate(BaseModel):
    court_id: StrictInt | None = Field(default=None, ge=1)
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    max_players: Literal[2, 4] | None = None
    min_level: float | None = Field(default=None, ge=1.0, le=7.0)
    max_level: float | None = Field(default=None, ge=1.0, le=7.0)

    _not_null = field_validator(
        "court_id",
        "starts_at",
        "ends_at",
        "max_players",
        "min_level",
        "max_level",
        mode="before",
    )(reject_null)


class BookingResponse(BaseModel):
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
