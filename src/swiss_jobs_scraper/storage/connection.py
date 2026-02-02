"""
Async database connection management.

Provides a connection pool with automatic migration on first connect.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (  # type: ignore
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from swiss_jobs_scraper.storage.config import DatabaseSettings, get_database_settings
from swiss_jobs_scraper.storage.migrations import run_migrations

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages async database connection pool with auto-migration.

    Usage:
        connection = DatabaseConnection()
        await connection.connect()

        async with connection.session() as session:
            # Use session for queries
            pass

        await connection.disconnect()
    """

    def __init__(self, settings: DatabaseSettings | None = None) -> None:
        """
        Initialize database connection manager.

        Args:
            settings: Database settings. If None, loads from environment.
        """
        self.settings = settings or get_database_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connected

    async def connect(self) -> None:
        """
        Connect to database and run migrations.

        Creates the connection pool and ensures all tables exist.
        Safe to call multiple times - subsequent calls are no-ops.
        """
        if self._connected:
            return

        if not self.settings.is_enabled:
            logger.warning("Database not configured, skipping connection")
            return

        logger.info(f"Connecting to database at {self.settings.database_host}")

        self._engine = create_async_engine(
            self.settings.connection_url,
            pool_size=self.settings.pool_size,
            max_overflow=self.settings.pool_max_overflow,
            pool_timeout=self.settings.pool_timeout,
            echo=False,
        )

        # Run migrations to ensure tables exist
        logger.info("Running database migrations...")
        await run_migrations(self._engine)
        logger.info("Database migrations completed")

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._connected = True
        logger.info("Database connection established")

    async def disconnect(self) -> None:
        """
        Close database connection pool.

        Safe to call multiple times.
        """
        if self._engine:
            await self._engine.dispose()  # type: ignore
            self._engine = None
            self._session_factory = None
            self._connected = False
            logger.info("Database connection closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.

        Usage:
            async with connection.session() as session:
                result = await session.execute(query)

        Yields:
            AsyncSession: Database session

        Raises:
            RuntimeError: If not connected to database
        """
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Global connection instance
_connection: DatabaseConnection | None = None


async def get_connection() -> DatabaseConnection:
    """
    Get the global database connection.

    Creates and connects if not already done.

    Returns:
        DatabaseConnection: Connected database connection
    """
    global _connection

    if _connection is None:
        _connection = DatabaseConnection()

    if not _connection.is_connected:
        await _connection.connect()

    return _connection


async def close_connection() -> None:
    """Close the global database connection."""
    global _connection

    if _connection:
        await _connection.disconnect()
        _connection = None
