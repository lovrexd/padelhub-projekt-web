from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User


class MatchParticipant(Base):
    """Prijava igrača u otvoreni padel meč."""

    __tablename__ = "match_participants"
    __table_args__ = (
        UniqueConstraint(
            "booking_id", "player_id", name="uq_match_participant_booking_player"
        ),
        CheckConstraint("status IN ('active', 'left')", name="ck_participant_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'active'")
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    booking: Mapped["Booking"] = relationship(back_populates="participants")
    player: Mapped["User"] = relationship(back_populates="participations")
