from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# engine održava skup otvorenih veza prema PostgreSQL bazi
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

# expire_on_commit=False: nakon commita objekti zadržavaju učitane vrijednosti
# kako ih Pydantic shema odgovora može pročitati bez naknadnog upita u bazu
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Osnovna klasa iz koje nasljeđuju svi ORM modeli tablica."""

    pass
