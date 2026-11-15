from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env se nalazi u glavnoj mapi projekta (3 razine iznad core/config.py)
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Postavke aplikacije učitane iz varijabli okoline ili .env datoteke."""

    APP_NAME: str = "PadelHub API"
    ENV: str = "dev"
    DATABASE_URL: str
    JWT_SECRET: str = "change-me"
    JWT_ISSUER: str = "padel-hub"

    # Ako varijabla postoji u okolini (npr. na serveru), ima prednost nad .env
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()
