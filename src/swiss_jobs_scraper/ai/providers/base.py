"""
Base AI provider interface.

Defines the abstract interface that all AI providers must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from swiss_jobs_scraper.ai.models import ExperienceLevel, ProcessedJob
from swiss_jobs_scraper.core.models import JobListing

if TYPE_CHECKING:
    from swiss_jobs_scraper.ai.features import AIFeature

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All AI providers (Gemini, Groq, etc.) must implement this interface.
    This enables easy addition of new providers in the future.
    """

    def __init__(self, api_key: str, model: str) -> None:
        """
        Initialize the AI provider.

        Args:
            api_key: API key for authentication
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        ...

    @abstractmethod
    async def _send_request(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        """
        Send a request to the AI provider.

        Args:
            system_prompt: System/context prompt
            user_prompt: User/task prompt

        Returns:
            Parsed JSON response from the model
        """
        ...

    async def process_job(
        self, job: "JobListing", features: set["AIFeature"] | None = None
    ) -> ProcessedJob:
        """
        Process a single job listing with AI.

        Args:
            job: Job listing to process
            features: Set of enabled AI features. If None, enables all.

        Returns:
            ProcessedJob with translations and analysis
        """
        from swiss_jobs_scraper.ai.features import AIFeature
        from swiss_jobs_scraper.ai.prompts import SYSTEM_PROMPT, get_processing_prompt

        # Default to all features if not specified
        if features is None:
            features = set(AIFeature)

        # Get description text
        description = ""
        language = "en"
        if job.descriptions:
            description = job.descriptions[0].description
            language = job.descriptions[0].language_code

        # Generate prompt
        user_prompt = get_processing_prompt(
            job.title, description, features, language=language
        )

        # Send to AI
        try:
            response = await self._send_request(SYSTEM_PROMPT, user_prompt)
            return self._parse_response(job.id, response)
        except Exception as e:
            logger.error(f"AI processing failed for job {job.id}: {e}")
            # Return minimal processed job on error
            return ProcessedJob(
                original_id=job.id,
                title_en=job.title,
                description_en=description,
                experience_level=ExperienceLevel.MID,
            )

    async def process_batch(
        self, jobs: list["JobListing"], features: set["AIFeature"] | None = None
    ) -> list[ProcessedJob]:
        """
        Process multiple jobs.

        Default implementation processes sequentially.
        Providers can override for parallel processing.

        Args:
            jobs: List of jobs to process
            features: Set of enabled AI features. If None, enables all.

        Returns:
            List of processed jobs
        """
        results = []
        for job in jobs:
            result = await self.process_job(job, features=features)
            results.append(result)
        return results

    def _parse_response(self, job_id: str, response: dict[str, Any]) -> ProcessedJob:
        """
        Parse AI response into ProcessedJob.

        Args:
            job_id: Original job ID
            response: Parsed JSON from AI

        Returns:
            ProcessedJob instance
        """
        # Handle experience level
        exp_level_str = response.get("experience_level", "mid")
        try:
            exp_level = ExperienceLevel(exp_level_str.lower())
        except ValueError:
            exp_level = ExperienceLevel.MID

        return ProcessedJob(
            original_id=job_id,
            title_de=response.get("title_de"),
            title_fr=response.get("title_fr"),
            title_it=response.get("title_it"),
            title_en=response.get("title_en"),
            description_de=response.get("description_de"),
            description_fr=response.get("description_fr"),
            description_it=response.get("description_it"),
            description_en=response.get("description_en"),
            required_languages=response.get("required_languages", []),
            experience_level=exp_level,
            years_experience_min=response.get("years_experience_min"),
            years_experience_max=response.get("years_experience_max"),
            education=response.get("education"),
            semantic_keywords=response.get("semantic_keywords", []),
        )
