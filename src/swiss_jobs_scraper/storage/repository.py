"""
Job repository for database operations.

Provides CRUD operations with upsert logic and AI processing tracking.
"""

import hashlib
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from swiss_jobs_scraper.storage.connection import DatabaseConnection, get_connection
from swiss_jobs_scraper.storage.models import StoredJob

if TYPE_CHECKING:
    from swiss_jobs_scraper.ai.models import ProcessedJob
    from swiss_jobs_scraper.core.models import JobListing

logger = logging.getLogger(__name__)


def _compute_content_hash(job: "JobListing") -> str:
    """
    Compute a hash of job content for change detection.

    Uses title + description + company to detect meaningful changes.
    """
    content = f"{job.title}|{job.descriptions}|{job.company.name}"
    return hashlib.sha256(content.encode()).hexdigest()[:64]


class JobRepository:
    """
    Repository for job storage operations.

    Provides:
    - upsert_job: Insert new or update changed jobs
    - get_unprocessed_jobs: Get jobs needing AI processing
    - mark_ai_processed: Update job with AI-enriched data
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        """
        Initialize repository with database connection.

        Args:
            connection: Active database connection
        """
        self._connection = connection

    async def upsert_job(self, job: "JobListing") -> tuple[bool, bool]:
        """
        Insert a new job or update if content has changed.

        Args:
            job: Job listing to persist

        Returns:
            Tuple of (is_new, is_updated):
            - (True, False) = New job inserted
            - (False, True) = Existing job updated
            - (False, False) = No change, skipped
        """
        content_hash = _compute_content_hash(job)

        # Get first description for storage
        description = ""
        if job.descriptions:
            description = job.descriptions[0].description

        # Get email from application channel
        email = None
        if job.application:
            email = job.application.email

        # Prepare job data
        job_data = {
            "id": job.id,
            "source_platform": job.source,
            "title": job.title,
            "description": description,
            "job_link": f"/jobs/{job.id}",
            "external_link": job.external_url,
            "email": email,
            "raw_data": job.model_dump(mode="json"),
            "content_hash": content_hash,
            "date_updated": datetime.utcnow(),
        }

        async with self._connection.session() as session:
            # Check if job exists and if content changed
            result = await session.execute(
                select(StoredJob.id, StoredJob.content_hash).where(
                    StoredJob.id == job.id
                )
            )
            existing = result.first()

            if existing is None:
                # New job - insert
                job_data["date_added"] = datetime.utcnow()
                stmt = insert(StoredJob).values(**job_data)
                await session.execute(stmt)
                logger.debug(f"Inserted new job: {job.id}")
                return (True, False)

            if existing.content_hash != content_hash:
                # Content changed - update
                update_stmt = (
                    update(StoredJob).where(StoredJob.id == job.id).values(**job_data)
                )
                await session.execute(update_stmt)
                logger.debug(f"Updated job: {job.id}")
                return (False, True)

            # No change
            logger.debug(f"Job unchanged, skipping: {job.id}")
            return (False, False)

    async def upsert_jobs(self, jobs: list["JobListing"]) -> dict[str, int]:
        """
        Upsert multiple jobs.

        Args:
            jobs: List of job listings

        Returns:
            Dict with counts: {"inserted": N, "updated": N, "unchanged": N}
        """
        counts = {"inserted": 0, "updated": 0, "unchanged": 0}

        for job in jobs:
            is_new, is_updated = await self.upsert_job(job)
            if is_new:
                counts["inserted"] += 1
            elif is_updated:
                counts["updated"] += 1
            else:
                counts["unchanged"] += 1

        logger.info(
            f"Upserted {len(jobs)} jobs: "
            f"{counts['inserted']} new, {counts['updated']} updated, "
            f"{counts['unchanged']} unchanged"
        )
        return counts

    async def get_job(self, job_id: str) -> StoredJob | None:
        """
        Get a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            StoredJob or None if not found
        """
        async with self._connection.session() as session:
            result = await session.execute(
                select(StoredJob).where(StoredJob.id == job_id)
            )
            return result.scalar_one_or_none()

    async def get_unprocessed_jobs(self, limit: int = 100) -> list[StoredJob]:
        """
        Get jobs that need AI processing.

        Returns jobs where:
        - ai_processed_at is NULL (never processed), OR
        - date_updated > ai_processed_at (updated since last processing)

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of jobs needing processing
        """
        async with self._connection.session() as session:
            result = await session.execute(
                select(StoredJob)
                .where(
                    (StoredJob.ai_processed_at.is_(None))
                    | (StoredJob.date_updated > StoredJob.ai_processed_at)
                )
                .order_by(StoredJob.date_added.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def mark_ai_processed(
        self, job_id: str, processed_data: "ProcessedJob"
    ) -> None:
        """
        Update job with AI-processed data.

        Stores translations and experience info in both dedicated columns
        and within the raw_data JSONB field.

        Args:
            job_id: Job to update
            processed_data: AI processing results
        """
        async with self._connection.session() as session:
            # Get current raw_data to merge AI results
            result = await session.execute(
                select(StoredJob.raw_data).where(StoredJob.id == job_id)
            )
            row = result.first()
            raw_data = dict(row.raw_data) if row and row.raw_data else {}

            # Add AI data to raw_data
            raw_data["ai_processed"] = processed_data.model_dump(mode="json")

            # Update both columns and raw_data
            stmt = (
                update(StoredJob)
                .where(StoredJob.id == job_id)
                .values(
                    title_de=processed_data.title_de,
                    title_fr=processed_data.title_fr,
                    title_it=processed_data.title_it,
                    title_en=processed_data.title_en,
                    description_de=processed_data.description_de,
                    description_fr=processed_data.description_fr,
                    description_it=processed_data.description_it,
                    description_en=processed_data.description_en,
                    required_languages=processed_data.required_languages,
                    experience_level=processed_data.experience_level.value,
                    years_experience_min=processed_data.years_experience_min,
                    years_experience_max=processed_data.years_experience_max,
                    education=processed_data.education,
                    semantic_keywords=processed_data.semantic_keywords,
                    ai_processed_at=datetime.utcnow(),
                    raw_data=raw_data,
                )
            )
            await session.execute(stmt)
            logger.debug(f"Marked job as AI processed: {job_id}")

    async def get_jobs_count(self) -> int:
        """Get total number of stored jobs."""
        async with self._connection.session() as session:
            from sqlalchemy import func

            result = await session.execute(select(func.count(StoredJob.id)))
            return result.scalar() or 0

    async def get_unprocessed_count(self) -> int:
        """Get count of jobs needing AI processing."""
        async with self._connection.session() as session:
            from sqlalchemy import func

            result = await session.execute(
                select(func.count(StoredJob.id)).where(
                    (StoredJob.ai_processed_at.is_(None))
                    | (StoredJob.date_updated > StoredJob.ai_processed_at)
                )
            )
            return result.scalar() or 0


# Global repository instance
_repository: JobRepository | None = None


async def get_repository() -> JobRepository:
    """
    Get the global job repository.

    Creates connection and repository if not already done.

    Returns:
        JobRepository: Connected repository instance
    """
    global _repository

    if _repository is None:
        connection = await get_connection()
        _repository = JobRepository(connection)

    return _repository
