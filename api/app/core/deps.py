from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.errors import AppError
from app.core.jwt import ExpiredSignatureError, InvalidTokenError, decode_token
from app.models.user import User
from app.repositories import user_repo

# auto_error=False da neautenticirane zahtjeve vratimo u našem 401 JSON obliku
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
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

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise AppError("forbidden", "Nemate ovlasti za ovu radnju", 403)
        return user

    return _check
