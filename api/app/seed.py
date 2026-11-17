"""Početni podatci za lokalni razvoj i obranu projekta.

Pokreće se iz mape api/, nakon alembic upgrade head:
    python -m app.seed

Skripta je idempotentna: može se pokrenuti više puta bez dupliranja zapisa.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models import Booking, Court, MatchParticipant, User

CET = timezone(timedelta(hours=1))

DEMO_USERS = [
    # (username, full_name, password, role, skill_level)
    ("admin@padel.hr", "Voditelj Centra", "admin123", "admin", 5.0),
    ("ivan@padel.hr", "Ivan Horvat", "player123", "player", 3.5),
    ("ana@padel.hr", "Ana Anić", "player123", "player", 4.0),
    ("marko@padel.hr", "Marko Marić", "player123", "player", 3.0),
    ("petra@padel.hr", "Petra Kovač", "player123", "player", 4.5),
    ("luka@padel.hr", "Luka Babić", "player123", "player", 2.5),
]

DEMO_COURTS = [
    # (name, surface, hourly_rate)
    ("Teren 1 (Panoramic)", "indoor", 36),
    ("Teren 2 (Indoor)", "indoor", 32),
    ("Teren 3 (Outdoor)", "outdoor", 28),
    ("Teren 4 (Pro)", "indoor", 40),
]


async def get_or_create_user(
    session: AsyncSession,
    username: str,
    full_name: str,
    password: str,
    role: str,
    skill_level: float,
) -> User:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
            skill_level=skill_level,
        )
        session.add(user)
        await session.flush()
    return user


async def get_or_create_court(
    session: AsyncSession,
    name: str,
    surface: str,
    hourly_rate: int,
) -> Court:
    result = await session.execute(select(Court).where(Court.name == name))
    court = result.scalar_one_or_none()
    if court is None:
        court = Court(name=name, surface=surface, hourly_rate=hourly_rate)
        session.add(court)
        await session.flush()
    return court


async def get_or_create_booking(
    session: AsyncSession,
    court_id: int,
    creator_id: int,
    booking_type: str,
    starts_at: datetime,
    ends_at: datetime,
    min_level: float = 1.0,
    max_level: float = 7.0,
) -> Booking:
    result = await session.execute(
        select(Booking).where(
            Booking.court_id == court_id,
            Booking.starts_at == starts_at,
        )
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        booking = Booking(
            court_id=court_id,
            creator_id=creator_id,
            booking_type=booking_type,
            starts_at=starts_at,
            ends_at=ends_at,
            cancellation_deadline=starts_at - timedelta(hours=24),
            max_players=4,
            min_level=min_level,
            max_level=max_level,
        )
        session.add(booking)
        await session.flush()
    return booking


async def ensure_participant(
    session: AsyncSession, booking_id: int, player_id: int
) -> None:
    result = await session.execute(
        select(MatchParticipant).where(
            MatchParticipant.booking_id == booking_id,
            MatchParticipant.player_id == player_id,
        )
    )
    if result.scalar_one_or_none() is None:
        session.add(
            MatchParticipant(
                booking_id=booking_id, player_id=player_id, status="active"
            )
        )
        await session.flush()


async def seed() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        users: dict[str, User] = {}
        for username, full_name, password, role, skill_level in DEMO_USERS:
            users[username] = await get_or_create_user(
                session, username, full_name, password, role, skill_level
            )

        courts: dict[str, Court] = {}
        for name, surface, hourly_rate in DEMO_COURTS:
            courts[name] = await get_or_create_court(
                session, name, surface, hourly_rate
            )

        # 1) Privatni termin (Teren 1, Ivan)
        s1 = datetime(2027, 3, 14, 17, 0, tzinfo=CET)
        await get_or_create_booking(
            session,
            court_id=courts["Teren 1 (Panoramic)"].id,
            creator_id=users["ivan@padel.hr"].id,
            booking_type="private",
            starts_at=s1,
            ends_at=s1 + timedelta(minutes=90),
        )

        # 2) Otvoreni meč 2/4 igrača za razinu 3.0 - 5.0 (Teren 2, Ana + Ivan)
        s2 = datetime(2027, 3, 14, 18, 0, tzinfo=CET)
        open_match = await get_or_create_booking(
            session,
            court_id=courts["Teren 2 (Indoor)"].id,
            creator_id=users["ana@padel.hr"].id,
            booking_type="open_match",
            starts_at=s2,
            ends_at=s2 + timedelta(minutes=90),
            min_level=3.0,
            max_level=5.0,
        )
        for uname in ("ana@padel.hr", "ivan@padel.hr"):
            await ensure_participant(session, open_match.id, users[uname].id)

        # 3) Popunjeni otvoreni meč 4/4 igrača (Teren 3)
        s3 = datetime(2027, 3, 14, 19, 0, tzinfo=CET)
        full_match = await get_or_create_booking(
            session,
            court_id=courts["Teren 3 (Outdoor)"].id,
            creator_id=users["marko@padel.hr"].id,
            booking_type="open_match",
            starts_at=s3,
            ends_at=s3 + timedelta(minutes=90),
            min_level=2.0,
            max_level=5.5,
        )
        for uname in (
            "marko@padel.hr",
            "ivan@padel.hr",
            "ana@padel.hr",
            "petra@padel.hr",
        ):
            await ensure_participant(session, full_match.id, users[uname].id)


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
