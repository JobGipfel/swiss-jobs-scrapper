"""Core module containing base classes and shared functionality."""

from swiss_jobs_scraper.core.exceptions import (
    AuthenticationError,
    LocationNotFoundError,
    ProviderError,
    RateLimitError,
    ScraperError,
    ValidationError,
)
from swiss_jobs_scraper.core.models import (
    ApplicationChannel,
    CompanyInfo,
    ContactInfo,
    EmploymentDetails,
    JobListing,
    JobLocation,
    JobSearchRequest,
    JobSearchResponse,
)
from swiss_jobs_scraper.core.provider import BaseJobProvider, ProviderHealth

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
