"""
Google Gemini AI provider implementation.
"""

import json
import logging
from typing import Any, cast

from swiss_jobs_scraper.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """
    Google Gemini AI provider.

    Uses the google-generativeai SDK for API calls.
    """

    @property
    def name(self) -> str:
        return "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        """
        Initialize Gemini provider.

        Args:
            api_key: Google AI API key
            model: Model to use (default: gemini-1.5-flash)
        """
        super().__init__(api_key, model)
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(
                    self.model,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.3,
                    },
                )
            except ImportError:
                raise ImportError(
                    "google-generativeai not installed. "
                    "Install with: pip install google-generativeai"
                ) from None
        return self._client

    async def _send_request(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        """
        Send request to Gemini API.

        Args:
            system_prompt: System instruction
            user_prompt: User message

        Returns:
            Parsed JSON response
        """
        client = self._get_client()

        # Combine prompts (Gemini uses content list)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            # Use sync generate_content (SDK handles async internally)
            response = client.generate_content(full_prompt)

            # Extract text and parse JSON
            text = response.text
            logger.debug(f"Gemini response: {text[:200]}...")

            # Parse JSON from response
            return cast(dict[str, Any], json.loads(text))

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
