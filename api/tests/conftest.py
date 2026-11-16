"""Zajednička testna infrastruktura.

Testovi rade nad zasebnom bazom padel_hub_test na istom PostgreSQL
poslužitelju, tako da razvojni podatci u padel_hub ostaju netaknuti.
Prije pokretanja testova: docker compose up -d db
"""

import asyncio
import os
from collections.abc import AsyncGenerator

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.deps import get_db
from app.main import create_app
from app.models import Base, Court, User


def _test_database_url() -> str:
    if url := os.environ.get("TEST_DATABASE_URL"):
        return url
    url = make_url(settings.DATABASE_URL)
    url = url.set(database=f"{url.database}_test")
    return url.render_as_string(hide_password=False)


TEST_DATABASE_URL = _test_database_url()

# NullPool: svaki test ima svoju petlju događaja, pa veze ne smiju preživjeti test
engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def _prepare_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    server = create_async_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with server.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": url.database},
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    await server.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """Priprema čistu testnu bazu jednom na početku pokretanja testova."""
    asyncio.run(_prepare_database())


@pytest.fixture(autouse=True)
async def clean_tables():
    """Prazni sve tablice prije svakog testa da testovi budu potpuno neovisni."""
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP klijent nad aplikacijom, bez pokretanja poslužitelja."""
    app = create_app()
    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Sesija za pripremu i provjeru zapisa izravno u testnoj bazi."""
    async with TestSessionLocal() as session:
        yield session


def fast_hash(plain: str) -> str:
    """Brzi bcrypt za testove (4 kruga umjesto uobičajenih 12)."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=4)).decode()


async def auth_header(
    client: AsyncClient, username: str, password: str
) -> dict[str, str]:
    """Prijavljuje korisnika i vraća Authorization zaglavlje za daljnje zahtjeve."""
    resp = await client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(
        username="testadmin",
        full_name="Test Admin",
        password_hash=fast_hash("admin123"),
        role="admin",
        skill_level=5.0,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def player_user(db: AsyncSession) -> User:
    user = User(
        username="player1",
        full_name="Prvi Igrač",
        password_hash=fast_hash("player123"),
        role="player",
        skill_level=3.5,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def other_player_user(db: AsyncSession) -> User:
    user = User(
        username="player2",
        full_name="Drugi Igrač",
        password_hash=fast_hash("player123"),
        role="player",
        skill_level=4.0,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def inactive_user(db: AsyncSession) -> User:
    user = User(
        username="inactive",
        full_name="Neaktivan Igrač",
        password_hash=fast_hash("pass123"),
        role="player",
        skill_level=3.0,
        is_active=False,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def court(db: AsyncSession) -> Court:
    c = Court(name="Teren 1", surface="indoor", hourly_rate=34)
    db.add(c)
    await db.commit()
    return c
