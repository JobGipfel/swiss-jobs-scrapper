"""
Database migrations for job storage.

Contains SQL statements that run automatically on first database connection.
Uses CREATE TABLE IF NOT EXISTS to ensure idempotency.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

# SQL statements for table and index creation
# These use IF NOT EXISTS to be safely re-runnable
MIGRATIONS: list[str] = [
    # Main jobs table
    """
    CREATE TABLE IF NOT EXISTS jobs (
        -- Core identifiers
        id VARCHAR(255) PRIMARY KEY,
        source_platform VARCHAR(100) NOT NULL,

        -- Original content
        title VARCHAR(500) NOT NULL,
        description TEXT,
        job_link VARCHAR(1000),
        external_link VARCHAR(1000),
        email VARCHAR(255),

        -- Timestamps
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_updated TIMESTAMP,

        -- AI-processed fields (separate columns)
        title_de VARCHAR(500),
        title_fr VARCHAR(500),
        title_it VARCHAR(500),
        title_en VARCHAR(500),
        description_de TEXT,
        description_fr TEXT,
        description_it TEXT,
        description_en TEXT,
        required_languages TEXT[],
        experience_level VARCHAR(50),
        years_experience_min INT,
        years_experience_max INT,
        ai_processed_at TIMESTAMP,

        -- Raw data (includes everything)
        raw_data JSONB,
        content_hash VARCHAR(64)
    );
    """,
    # Indexes for common queries
    "CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source_platform);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_date_added ON jobs(date_added);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_date_updated ON jobs(date_updated);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_experience ON jobs(experience_level);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_ai_processed ON jobs(ai_processed_at);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_content_hash ON jobs(content_hash);",
]


async def run_migrations(engine: AsyncEngine) -> None:
    """
    Run all migrations on database startup.

    This function is idempotent - it can be safely called multiple times.
    Tables and indexes are only created if they don't already exist.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        for migration in MIGRATIONS:
            await conn.execute(text(migration))
