from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, StrictInt, field_validator

from app.schemas.common import MAX_INT32, reject_nul_char, reject_null

CourtName = Annotated[
    str,
    Field(min_length=1, max_length=100),
    AfterValidator(reject_nul_char),
]


class CourtCreate(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: CourtName
    surface: Literal["indoor", "outdoor"]
    hourly_rate: StrictInt = Field(gt=0, le=MAX_INT32)


class CourtUpdate(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: CourtName | None = None
    surface: Literal["indoor", "outdoor"] | None = None
    hourly_rate: StrictInt | None = Field(default=None, gt=0, le=MAX_INT32)

    _not_null = field_validator("name", "surface", "hourly_rate", mode="before")(
        reject_null
    )


class CourtBrief(BaseModel):
    name: str
    surface: str
    hourly_rate: int

    model_config = {"from_attributes": True}


class CourtResponse(BaseModel):
    id: int
    name: str
    surface: str
    hourly_rate: int

    model_config = {"from_attributes": True}


class CourtSlotResponse(BaseModel):
    starts_at: datetime
    ends_at: datetime
    booking_type: str

    model_config = {"from_attributes": True}
