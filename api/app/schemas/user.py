from pydantic import BaseModel


class UserResponse(BaseModel):
    """Javni podatci korisničkog računa; password_hash ovdje namjerno ne postoji."""

    id: int
    username: str
    full_name: str
    role: str
    skill_level: float
    is_active: bool

    model_config = {"from_attributes": True}
