from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from app.schemas.common import reject_nul_char


def _bcrypt_limit(value: str) -> str:
    # bcrypt uzima najviše 72 bajta; duže lozinke bi tiho skratio
    if len(value.encode()) > 72:
        raise ValueError("Lozinka smije imati najviše 72 bajta")
    return value


Username = Annotated[
    str, Field(min_length=1, max_length=255), AfterValidator(reject_nul_char)
]
Password = Annotated[
    str,
    Field(min_length=1),
    AfterValidator(reject_nul_char),
    AfterValidator(_bcrypt_limit),
]


class LoginRequest(BaseModel):
    username: Username
    password: Password


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
