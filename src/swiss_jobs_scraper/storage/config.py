"""
Database configuration settings.

Reads from environment variables to configure PostgreSQL connection.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Database configuration loaded from environment variables.

    Supports either a full DATABASE_URL or individual connection parameters.
    The database layer is completely optional - if no credentials are set,
    is_enabled returns False and no database operations will occur.
    """

    # Full connection URL (takes precedence if set)
    database_url: str | None = None

    # Individual connection parameters
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "swiss_jobs"
    database_user: str = "postgres"
    database_password: str = ""

    # Connection pool settings
    pool_size: int = 5
    pool_max_overflow: int = 10
    pool_timeout: int = 30

    class Config:
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"

    @property
    def is_enabled(self) -> bool:
        """Check if database is configured and should be used."""
        return bool(self.database_url or self.database_password)

    @property
    def connection_url(self) -> str:
        """Get the SQLAlchemy async connection URL."""
        if self.database_url:
            # Ensure it uses asyncpg driver
            url = self.database_url
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_database_settings() -> DatabaseSettings:
    """Get cached database settings instance."""
    return DatabaseSettings()
