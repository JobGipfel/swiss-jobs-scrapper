"""Providers package - all job data source implementations."""

from swiss_jobs_scraper.providers.job_room import JobRoomProvider

# Registry of all available providers
PROVIDERS = {
    "job_room": JobRoomProvider,
}


def get_provider(name: str):
    """
    Get a provider class by name.

    Args:
        name: Provider name (e.g., 'job_room')

    Returns:
        Provider class

    Raises:
        KeyError: If provider not found
    """
    if name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise KeyError(f"Provider '{name}' not found. Available: {available}")
    return PROVIDERS[name]


def list_providers() -> list[str]:
    """Get list of available provider names."""
    return list(PROVIDERS.keys())


__all__ = ["JobRoomProvider", "PROVIDERS", "get_provider", "list_providers"]
