from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    RUNTIME CONFIGURATION FOR api-fastapi, LOADED FROM ENVIRONMENT VARIABLES.
    JWT_SIGNING_KEY AND JWT_ALGORITHM MUST MATCH core-django's SIMPLE_JWT
    SETTINGS EXACTLY SINCE THIS SERVICE VALIDATES TOKENS ISSUED BY DJANGO
    RATHER THAN ISSUING ITS OWN.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://devtracker:devtracker@localhost:5432/devtracker"
    redis_url: str = "redis://localhost:6379/0"
    jwt_signing_key: str = "insecure-dev-only-key"
    jwt_algorithm: str = "HS256"
    fastapi_port: int = 8001

    @property
    def async_database_url(self) -> str:
        """THE APP QUERIES THROUGH asyncpg; ALEMBIC MIGRATIONS USE THE SYNC psycopg URL INSTEAD."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
