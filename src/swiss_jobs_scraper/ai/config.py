"""
AI configuration settings.

Unified configuration for all AI providers using single API key and model settings.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    """
    AI configuration loaded from environment variables.

    Provides unified configuration for all AI providers.
    Set AI_PROVIDER, AI_API_KEY, and optionally AI_MODEL to enable.
    """

    # Provider selection
    ai_provider: Literal["gemini", "groq"] | None = None

    # Unified API credentials (works for both providers)
    ai_api_key: str | None = None

    # Model selection (optional - defaults based on provider)
    ai_model: str | None = None

    class Config:
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"

    @property
    def is_enabled(self) -> bool:
        """Check if AI processing is configured and should be used."""
        return bool(self.ai_provider and self.ai_api_key)

    @property
    def effective_model(self) -> str:
        """
        Get the model to use.

        Returns configured model or provider-specific default.
        """
        if self.ai_model:
            return self.ai_model

        # Default models per provider
        defaults = {
            "gemini": "gemini-1.5-flash",
            "groq": "llama-3.3-70b-versatile",
        }
        return defaults.get(self.ai_provider or "", "")


@lru_cache
def get_ai_settings() -> AISettings:
    """Get cached AI settings instance."""
    return AISettings()
