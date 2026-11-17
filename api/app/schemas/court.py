from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import reject_null


class CourtCreate(BaseModel):
    """Podatci za dodavanje novog padel terena."""

    name: str = Field(min_length=1, max_length=100)
    surface: Literal["indoor", "outdoor"]
    hourly_rate: int = Field(gt=0)


class CourtUpdate(BaseModel):
    """Podatci za djelomičnu izmjenu terena (PATCH)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    surface: Literal["indoor", "outdoor"] | None = None
    hourly_rate: int | None = Field(default=None, gt=0)

    _not_null = field_validator("name", "surface", "hourly_rate", mode="before")(
        reject_null
    )


class CourtBrief(BaseModel):
    """Sažetak terena unutar odgovora za rezervacije i mečeve."""

    name: str
    surface: str
    hourly_rate: int

    model_config = {"from_attributes": True}


class CourtResponse(BaseModel):
    """Potpun prikaz padel terena."""

    id: int
    name: str
    surface: str
    hourly_rate: int

    model_config = {"from_attributes": True}


class CourtSlotResponse(BaseModel):
    """Zauzeti vremenski raspon na terenu (bez osobnih podataka korisnika)."""

    starts_at: datetime
    ends_at: datetime
    booking_type: str

    model_config = {"from_attributes": True}
