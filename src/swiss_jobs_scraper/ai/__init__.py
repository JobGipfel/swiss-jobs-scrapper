"""
Optional AI post-processing layer for job enrichment.

This module provides AI-powered features:
- Translation to Swiss languages (DE, FR, IT, EN)
- Language requirement extraction
- Experience level detection

Usage:
    from swiss_jobs_scraper.ai import get_processor, AISettings

    settings = AISettings()
    if settings.is_enabled:
        processor = get_processor()
        processed = await processor.process_job(job_listing)
"""

from swiss_jobs_scraper.ai.config import AISettings, get_ai_settings
from swiss_jobs_scraper.ai.models import ExperienceLevel, ProcessedJob
from swiss_jobs_scraper.ai.processor import AIProcessor, get_processor

__all__ = [
    "AISettings",
    "get_ai_settings",
    "ExperienceLevel",
    "ProcessedJob",
    "AIProcessor",
    "get_processor",
]
