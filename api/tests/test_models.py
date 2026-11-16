from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Booking, Court, MatchParticipant, User


async def test_unique_username_constraint(db):
    db.add(
        User(
            username="ana@padel.hr",
            full_name="Ana Anić",
            password_hash="hash1",
            role="player",
            skill_level=3.5,
        )
    )
    await db.commit()

    db.add(
        User(
            username="ana@padel.hr",
            full_name="Druga Ana",
            password_hash="hash2",
            role="player",
            skill_level=4.0,
        )
    )
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_invalid_role_rejected_by_db_check(db):
    db.add(
        User(
            username="uljez@padel.hr",
            full_name="Uljez",
            password_hash="hash",
            role="superadmin",
            skill_level=3.0,
        )
    )
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_booking_and_unique_participant_constraints(db):
    user = User(
        username="marko@padel.hr",
        full_name="Marko Marić",
        password_hash="hash",
        role="player",
        skill_level=4.0,
    )
    court = Court(name="Teren 1", surface="indoor", hourly_rate=32)
    db.add_all([user, court])
    await db.commit()

    start = datetime(2026, 12, 1, 18, 0, tzinfo=timezone.utc)
    booking = Booking(
        court_id=court.id,
        creator_id=user.id,
        booking_type="open_match",
        starts_at=start,
        ends_at=start + timedelta(minutes=90),
        cancellation_deadline=start - timedelta(hours=24),
        max_players=4,
    )
    db.add(booking)
    await db.commit()

    db.add(MatchParticipant(booking_id=booking.id, player_id=user.id))
    await db.commit()

    # Isti igrač ne smije imati dva reda u istom meču
    db.add(MatchParticipant(booking_id=booking.id, player_id=user.id))
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()
