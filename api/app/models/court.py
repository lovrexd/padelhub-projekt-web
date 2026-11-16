from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Court(Base):
    """Padel teren koji se može rezervirati po satnici."""

    __tablename__ = "courts"
    __table_args__ = (
        CheckConstraint("surface IN ('indoor', 'outdoor')", name="ck_court_surface"),
        CheckConstraint("hourly_rate > 0", name="ck_court_hourly_rate"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    surface: Mapped[str] = mapped_column(String(20), nullable=False)
    hourly_rate: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))

    bookings: Mapped[list["Booking"]] = relationship(back_populates="court")
