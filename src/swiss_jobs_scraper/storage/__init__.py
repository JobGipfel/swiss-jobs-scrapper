"""
Optional database storage layer for job persistence.

This module provides PostgreSQL integration for storing and retrieving job listings.
It is completely optional and only activates when database credentials are configured.

Usage:
    from swiss_jobs_scraper.storage import get_repository, DatabaseSettings

    settings = DatabaseSettings()
    if settings.is_enabled:
        repo = await get_repository()
        await repo.upsert_job(job_listing)
"""

from swiss_jobs_scraper.storage.config import DatabaseSettings
from swiss_jobs_scraper.storage.repository import JobRepository, get_repository

__all__ = ["DatabaseSettings", "JobRepository", "get_repository"]
