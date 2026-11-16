from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


def _bcrypt_limit(value: str) -> str:
    # bcrypt u obradu uzima najviše 72 bajta; duže lozinke bi tiho skratio
    if len(value.encode()) > 72:
        raise ValueError("Lozinka smije imati najviše 72 bajta")
    return value


Password = Annotated[str, Field(min_length=1), AfterValidator(_bcrypt_limit)]
NewPassword = Annotated[str, Field(min_length=8), AfterValidator(_bcrypt_limit)]


class LoginRequest(BaseModel):
    """Podatci potrebni za prijavu korisnika."""

    username: str = Field(min_length=1, max_length=255)
    password: Password


class RefreshRequest(BaseModel):
    """Zahtjev za izdavanje novog para tokena pomoću refresh tokena."""

    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Odgovor nakon uspješne prijave ili obnove tokena."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
