from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.jwt import (
    ExpiredSignatureError,
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repo

INVALID_CREDENTIALS = "Neispravno korisničko ime ili lozinka"

# Lažni hash: provjera se vrti i kad korisničko ime ne postoji, pa trajanje
# odgovora (timing attack) ne odaje postoje li računi u bazi
_DUMMY_HASH = hash_password("dummy-password-for-timing")


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    """Provjerava korisničko ime, lozinku i status računa istim 401 odgovorom."""
    user = await user_repo.get_by_username(db, username)
    password_ok = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    if not user or not password_ok or not user.is_active:
        raise AppError("invalid_credentials", INVALID_CREDENTIALS, 401)
    return user


def create_tokens(user: User) -> tuple[str, str]:
    """Stvara par (access_token, refresh_token) za prijavljenog korisnika."""
    access = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)
    return access, refresh


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    """Provjerava refresh token i vraća novi par pristupnog i refresh tokena."""
    try:
        payload = decode_token(refresh_token)
    except ExpiredSignatureError:
        raise AppError("token_expired", "Refresh token je istekao", 401)
    except InvalidTokenError:
        raise AppError("invalid_credentials", "Neispravan refresh token", 401)

    # Access token je potpisan istim ključem, pa moramo provjeriti polje type
    if payload.get("type") != "refresh":
        raise AppError("invalid_credentials", "Neispravan refresh token", 401)

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise AppError("invalid_credentials", "Neispravan refresh token", 401)

    user = await user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise AppError("invalid_credentials", "Neispravan refresh token", 401)

    return create_tokens(user)
