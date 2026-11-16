from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings

__all__ = [
    "ExpiredSignatureError",
    "InvalidTokenError",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
]

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: int, role: str) -> str:
    """Kratkotrajan pristupni token (15 min) koji se šalje uz svaki zahtjev."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Dugotrajan token (7 dana) koji služi samo za dobivanje novog para tokena."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Provjerava potpis, rok trajanja i izdavatelja pa vraća podatke iz tokena.

    Istekli token baca ExpiredSignatureError, a svaki drugi neispravan token
    InvalidTokenError. Prvi nasljeđuje drugi, pa se u obradi hvata prvi.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM],
        issuer=settings.JWT_ISSUER,
        options={"require": ["exp", "sub", "iss", "type"]},
    )
