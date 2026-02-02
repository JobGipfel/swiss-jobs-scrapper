"""
Abstract base provider interface.

All job data sources (job-room.ch, LinkedIn, etc.) must implement this interface
to ensure consistent behavior across the scraper system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from swiss_jobs_scraper.core.models import (
    JobListing,
    JobSearchRequest,
    JobSearchResponse,
)


class ProviderStatus(str, Enum):
    """Provider operational status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ProviderHealth(BaseModel):
    """Health check response for a provider."""

    provider: str
    status: ProviderStatus
    latency_ms: int | None = None
    last_check: datetime = Field(default_factory=datetime.now)
    message: str | None = None
    details: dict[str, Any] | None = None


class ProviderCapabilities(BaseModel):
    """Describes what features a provider supports."""

    supports_radius_search: bool = False
    supports_canton_filter: bool = False
    supports_profession_codes: bool = False
    supports_language_skills: bool = False
    supports_company_filter: bool = False
    supports_work_forms: bool = False
    max_page_size: int = 100
    supported_languages: list[str] = Field(default_factory=lambda: ["en"])
    supported_sort_orders: list[str] = Field(default_factory=lambda: ["date_desc"])


class BaseJobProvider(ABC):
    """
    Abstract base class for job data providers.

    Each provider (job-room.ch, LinkedIn, Indeed, etc.) implements this interface
    to provide a consistent API for job searching and retrieval.



    Usage:
        class JobRoomProvider(BaseJobProvider):
            name = "job_room"

            async def search(self, request: JobSearchRequest) -> JobSearchResponse:
                # Implementation...
    """

    def __init__(self, mode: Any = "stealth", include_raw_data: bool = False):
        """
        Initialize the provider.

        Args:
            mode: Scraper execution mode (fast, stealth, aggressive)
            include_raw_data: Whether to include original API response in results
        """
        self.mode = mode
        self.include_raw_data = include_raw_data

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique provider identifier.

        Returns:
            str: Provider name (e.g., 'job_room', 'linkedin')
        """
        ...

    @property
    def display_name(self) -> str:
        """Human-readable provider name."""
        return self.name.replace("_", " ").title()

    @property
    def capabilities(self) -> ProviderCapabilities:
        """
        Returns the capabilities/features supported by this provider.

        Override in subclass to specify provider-specific capabilities.
        """
        return ProviderCapabilities()

    @abstractmethod
    async def search(self, request: JobSearchRequest) -> JobSearchResponse:
        """
        Search for jobs matching the given criteria.

        Args:
            request: Search criteria including keywords, location, filters

        Returns:
            JobSearchResponse with matching jobs and pagination info

        Raises:
            ProviderError: If the provider encounters an error
            RateLimitError: If rate limit is exceeded
            ValidationError: If the request is invalid
        """
        ...

    @abstractmethod
    async def get_details(self, job_id: str, language: str = "en") -> JobListing:
        """
        Get full details for a specific job.

        Args:
            job_id: Unique job identifier (usually UUID)
            language: Preferred response language

        Returns:
            Complete JobListing with all available details

        Raises:
            ProviderError: If job not found or provider error
        """
        ...

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """
        Check if the provider is operational.

        Returns:
            ProviderHealth with status and latency info
        """
        ...

    async def __aenter__(self) -> "BaseJobProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - cleanup resources."""
        await self.close()

    async def close(self) -> None:
        """
        Close provider resources (HTTP sessions, etc.).

        Override in subclass if cleanup is needed.
        """
        return
