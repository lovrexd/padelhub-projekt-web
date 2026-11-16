from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.court import Court
    from app.models.match_participant import MatchParticipant
    from app.models.user import User


class Booking(Base):
    """Rezervacija padel terena (privatni termin ili otvoreni meč)."""

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(
            "booking_type IN ('private', 'open_match')", name="ck_booking_type"
        ),
        CheckConstraint("starts_at < ends_at", name="ck_booking_time_range"),
        CheckConstraint(
            "cancellation_deadline <= starts_at",
            name="ck_booking_cancellation_deadline",
        ),
        CheckConstraint("max_players IN (2, 4)", name="ck_booking_max_players"),
        CheckConstraint(
            "min_level >= 1.0 AND max_level <= 7.0 AND min_level <= max_level",
            name="ck_booking_level_range",
        ),
        CheckConstraint("status IN ('active', 'cancelled')", name="ck_booking_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(
        ForeignKey("courts.id"), nullable=False, index=True
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    booking_type: Mapped[str] = mapped_column(String(20), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancellation_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    max_players: Mapped[int] = mapped_column(nullable=False, server_default=text("4"))
    min_level: Mapped[float] = mapped_column(
        Numeric(3, 1, asdecimal=False), nullable=False, server_default=text("1.0")
    )
    max_level: Mapped[float] = mapped_column(
        Numeric(3, 1, asdecimal=False), nullable=False, server_default=text("7.0")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'active'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    court: Mapped["Court"] = relationship(back_populates="bookings")
    creator: Mapped["User"] = relationship(back_populates="bookings")
    participants: Mapped[list["MatchParticipant"]] = relationship(
        back_populates="booking"
    )
