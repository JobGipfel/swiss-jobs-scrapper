"""Core module containing base classes and shared functionality."""

from swiss_jobs_scraper.core.models import (
    JobSearchRequest,
    JobSearchResponse,
    JobListing,
    JobLocation,
    EmploymentDetails,
    CompanyInfo,
    ContactInfo,
    ApplicationChannel,
)
from swiss_jobs_scraper.core.provider import BaseJobProvider, ProviderHealth
from swiss_jobs_scraper.core.exceptions import (
    ScraperError,
    ProviderError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    LocationNotFoundError,
)

__all__ = [
    "JobSearchRequest",
    "JobSearchResponse",
    "JobListing",
    "JobLocation",
    "EmploymentDetails",
    "CompanyInfo",
    "ContactInfo",
    "ApplicationChannel",
    "BaseJobProvider",
    "ProviderHealth",
    "ScraperError",
    "ProviderError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "LocationNotFoundError",
]
