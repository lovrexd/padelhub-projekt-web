from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.errors import AppError
from app.core.jwt import ExpiredSignatureError, InvalidTokenError, decode_token
from app.models.user import User
from app.repositories import user_repo

# auto_error=False da bismo sami vratili naš JSON format 401 umjesto defaultnog
_bearer_scheme = HTTPBearer(auto_error=False)


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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Provjerava Bearer access token i dohvaća aktivnog korisnika iz baze."""
    if not credentials:
        raise AppError("invalid_credentials", "Nedostaje pristupni token", 401)
    try:
        payload = decode_token(credentials.credentials)
    except ExpiredSignatureError:
        raise AppError("token_expired", "Token je istekao", 401)
    except InvalidTokenError:
        raise AppError("invalid_credentials", "Neispravan token", 401)

    if payload.get("type") != "access":
        raise AppError("invalid_credentials", "Neispravan token", 401)

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise AppError("invalid_credentials", "Neispravan token", 401)

    user = await user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise AppError("invalid_credentials", "Neispravan token", 401)
    return user


def require_role(*allowed_roles: str):
    """Vraća ovisnost koja provjerava pripada li korisnik jednoj od dopuštenih uloga."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise AppError("forbidden", "Nemate ovlasti za ovu radnju", 403)
        return user

    return _check
