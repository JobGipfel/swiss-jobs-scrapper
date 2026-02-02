"""
AI feature flags.

Defines the available AI processing features that can be selectively enabled.
"""

from enum import Enum


class AIFeature(str, Enum):
    """
    Available AI processing features.

    Allows atomic selection of which AI tasks to perform.
    """

    TRANSLATION = "translation"
    EXPERIENCE = "experience"
    LANGUAGES = "languages"
    EDUCATION = "education"
    KEYWORDS = "keywords"
