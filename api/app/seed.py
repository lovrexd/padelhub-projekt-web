"""Početni podatci za lokalni razvoj i obranu projekta.

Pokreće se iz mape api/, nakon alembic upgrade head:
    python -m app.seed

Skripta je idempotentna: može se pokrenuti više puta bez dupliranja zapisa.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models import Court, User

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


async def seed() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        for username, full_name, password, role, skill_level in DEMO_USERS:
            await get_or_create_user(
                session, username, full_name, password, role, skill_level
            )
        for name, surface, hourly_rate in DEMO_COURTS:
            await get_or_create_court(session, name, surface, hourly_rate)


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
