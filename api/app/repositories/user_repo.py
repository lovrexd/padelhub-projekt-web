from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Dohvaća korisnika po primarnom ključu."""
    return await db.get(User, user_id)


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    """Dohvaća korisnika po korisničkom imenu."""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user: User) -> User:
    """Dodaje novog korisnika u sesiju baze."""
    db.add(user)
    await db.flush()
    return user
