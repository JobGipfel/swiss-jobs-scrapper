"""Exception hierarchy for the Swiss Jobs Scraper."""

from typing import Any


class ScraperError(Exception):
    """Base exception for all scraper errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProviderError(ScraperError):
    """Error originating from a specific provider."""

    def __init__(
        self, provider: str, message: str, details: dict[str, Any] | None = None
    ):
        super().__init__(f"[{provider}] {message}", details)
        self.provider = provider


class AuthenticationError(ProviderError):
    """Authentication or CSRF token error."""

    pass


class RateLimitError(ProviderError):
    """Rate limit exceeded (HTTP 429)."""

    def __init__(
        self,
        provider: str,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        super().__init__(provider, message, {"retry_after": retry_after})
        self.retry_after = retry_after


class ValidationError(ScraperError):
    """Request validation error."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, {"field": field})
        self.field = field


class LocationNotFoundError(ScraperError):
    """Location could not be resolved to BFS codes."""

    def __init__(self, location: str):
        super().__init__(
            f"Location '{location}' could not be resolved to BFS codes",
            {"location": location},
        )
        self.location = location


class NetworkError(ScraperError):
    """Network connectivity error."""

    pass


class ResponseParseError(ProviderError):
    """Failed to parse provider response."""

    pass
