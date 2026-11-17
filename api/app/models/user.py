from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.match_participant import MatchParticipant


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'player')", name="ck_user_role"),
        CheckConstraint(
            "skill_level >= 1.0 AND skill_level <= 7.0", name="ck_user_skill_level"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    skill_level: Mapped[float] = mapped_column(
        Numeric(3, 1, asdecimal=False), nullable=False, server_default=text("3.0")
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))

    bookings: Mapped[list["Booking"]] = relationship(back_populates="creator")
    participations: Mapped[list["MatchParticipant"]] = relationship(
        back_populates="player"
    )
