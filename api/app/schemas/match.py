from datetime import datetime

from pydantic import BaseModel, computed_field

from app.core.phases import BookingPhase, get_booking_phase
from app.schemas.court import CourtBrief


class PlayerBrief(BaseModel):
    """Osnovni javni prikaz igrača u otvorenom meču (bez e-pošte i lozinke)."""

    id: int
    full_name: str
    skill_level: float

    model_config = {"from_attributes": True}


class ParticipantResponse(BaseModel):
    """Prijava igrača unutar otvorenog meča."""

    id: int
    player_id: int
    status: str
    joined_at: datetime
    player: PlayerBrief

    model_config = {"from_attributes": True}


class OpenMatchResponse(BaseModel):
    """Prikaz otvorenog padel meča sa slobodnim mjestima i aktivnim igračima."""

    id: int
    court_id: int
    creator_id: int
    starts_at: datetime
    ends_at: datetime
    cancellation_deadline: datetime
    max_players: int
    min_level: float
    max_level: float
    status: str
    court: CourtBrief
    active_players_count: int
    active_participants: list[ParticipantResponse]

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def phase(self) -> BookingPhase:
        return get_booking_phase(self)

    @computed_field
    @property
    def spots_left(self) -> int:
        return max(0, self.max_players - self.active_players_count)
