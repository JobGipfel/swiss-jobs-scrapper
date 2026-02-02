"""
AI processor orchestrator.

Routes job processing to the configured AI provider.
"""

import logging
from typing import TYPE_CHECKING

from swiss_jobs_scraper.ai.config import AISettings, get_ai_settings
from swiss_jobs_scraper.ai.models import ProcessedJob
from swiss_jobs_scraper.ai.providers.base import AIProvider

if TYPE_CHECKING:
    from swiss_jobs_scraper.ai.features import AIFeature
    from swiss_jobs_scraper.core.models import JobListing

logger = logging.getLogger(__name__)


class AIProcessor:
    """
    Main AI processor that routes to configured provider.

    Usage:
        processor = AIProcessor()
        if processor.is_enabled:
            result = await processor.process_job(job)
    """

    def __init__(self, settings: AISettings | None = None) -> None:
        """
        Initialize AI processor.

        Args:
            settings: AI settings. If None, loads from environment.
        """
        self.settings = settings or get_ai_settings()
        self._provider: AIProvider | None = None

    @property
    def is_enabled(self) -> bool:
        """Check if AI processing is configured."""
        return self.settings.is_enabled

    def _get_provider(self) -> AIProvider:
        """Get or create the AI provider based on settings."""
        if self._provider is not None:
            return self._provider

        if not self.settings.is_enabled:
            raise RuntimeError("AI processing not configured")

        provider_name = self.settings.ai_provider
        api_key = self.settings.ai_api_key or ""
        model = self.settings.effective_model

        if provider_name == "gemini":
            from swiss_jobs_scraper.ai.providers.gemini import GeminiProvider

            self._provider = GeminiProvider(api_key, model)
        elif provider_name == "groq":
            from swiss_jobs_scraper.ai.providers.groq import GroqProvider

            self._provider = GroqProvider(api_key, model)
        else:
            raise ValueError(f"Unknown AI provider: {provider_name}")

        logger.info(f"Initialized AI provider: {provider_name} with model {model}")
        return self._provider

    async def process_job(
        self, job: "JobListing", features: set["AIFeature"] | None = None
    ) -> ProcessedJob:
        """
        Process a single job with AI.

        Args:
            job: Job listing to process
            features: Set of enabled AI features. If None, enables all.

        Returns:
            ProcessedJob with translations and analysis
        """
        provider = self._get_provider()
        logger.debug(f"Processing job {job.id} with {provider.name}")
        return await provider.process_job(job, features=features)

    async def process_jobs(
        self, jobs: list["JobListing"], features: set["AIFeature"] | None = None
    ) -> list[ProcessedJob]:
        """
        Process multiple jobs with AI.

        Args:
            jobs: List of jobs to process
            features: Set of enabled AI features. If None, enables all.

        Returns:
            List of processed jobs
        """
        if not jobs:
            return []

        provider = self._get_provider()
        logger.info(f"Processing {len(jobs)} jobs with {provider.name}")
        return await provider.process_batch(jobs, features=features)


# Global processor instance
_processor: AIProcessor | None = None


def get_processor() -> AIProcessor:
    """
    Get the global AI processor.

    Returns:
        AIProcessor instance
    """
    global _processor

    if _processor is None:
        _processor = AIProcessor()

    return _processor
