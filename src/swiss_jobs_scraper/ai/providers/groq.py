"""
Groq AI provider implementation.
"""

import json
import logging
from typing import Any

from swiss_jobs_scraper.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """
    Groq AI provider.

    Uses the Groq SDK for fast inference on open-source models.
    """

    @property
    def name(self) -> str:
        return "groq"

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key
            model: Model to use (default: llama-3.3-70b-versatile)
        """
        super().__init__(api_key, model)
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create the Groq client."""
        if self._client is None:
            try:
                from groq import Groq

                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "groq not installed. Install with: pip install groq"
                ) from None
        return self._client

    async def _send_request(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        """
        Send request to Groq API.

        Args:
            system_prompt: System instruction
            user_prompt: User message

        Returns:
            Parsed JSON response
        """
        client = self._get_client()

        try:
            # Groq uses OpenAI-compatible API
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            # Extract content
            content = response.choices[0].message.content
            logger.debug(f"Groq response: {content[:200]}...")

            # Parse JSON
            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
