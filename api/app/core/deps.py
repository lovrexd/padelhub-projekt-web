from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Otvara jednu transakciju baze po HTTP zahtjevu.

    Ako zahtjev prođe bez iznimke, promjene se potvrđuju (commit);
    ako dođe do greške, sve se vraća unatrag (rollback).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
