"""
AI processing output models.

Defines the data structures for AI-enriched job data.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ExperienceLevel(str, Enum):
    """
    Experience level classification.

    Based on typical years of experience requirements:
    - ENTRY: 0 years (internships, graduates)
    - JUNIOR: 0-2 years
    - MID: 2-5 years
    - SENIOR: 5-8 years
    - LEAD: 8+ years (team lead, tech lead)
    - PRINCIPAL: 10+ years (staff, principal, architect)
    """

    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"

    @classmethod
    def from_years(cls, years: int | None) -> "ExperienceLevel":
        """
        Determine experience level from years of experience.

        Args:
            years: Minimum years of experience required

        Returns:
            Appropriate experience level
        """
        if years is None or years == 0:
            return cls.ENTRY
        if years <= 2:
            return cls.JUNIOR
        if years <= 5:
            return cls.MID
        if years <= 8:
            return cls.SENIOR
        if years <= 10:
            return cls.LEAD
        return cls.PRINCIPAL


class ProcessedJob(BaseModel):
    """
    AI-processed job data.

    Contains translations and extracted information from job descriptions.
    All fields are populated by AI analysis of the original job listing.
    """

    # Reference to original job
    original_id: str = Field(..., description="ID of the processed job")

    # Translations (all 4 Swiss languages)
    title_de: str | None = Field(None, description="German translation of title")
    title_fr: str | None = Field(None, description="French translation of title")
    title_it: str | None = Field(None, description="Italian translation of title")
    title_en: str | None = Field(None, description="English translation of title")

    description_de: str | None = Field(
        None, description="German translation of description"
    )
    description_fr: str | None = Field(
        None, description="French translation of description"
    )
    description_it: str | None = Field(
        None, description="Italian translation of description"
    )
    description_en: str | None = Field(
        None, description="English translation of description"
    )

    # Extracted requirements
    required_languages: list[str] = Field(
        default_factory=list,
        description="Language codes extracted from job requirements (e.g., ['de', 'en'])",
    )

    # Experience analysis (based on requirements, not job title)
    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.MID,
        description="Inferred experience level based on job requirements",
    )
    years_experience_min: int | None = Field(
        None, description="Minimum years of experience mentioned"
    )
    years_experience_max: int | None = Field(
        None, description="Maximum years of experience mentioned"
    )

    # Education
    education: str | None = Field(
        None, description="Required education level (e.g., 'University', 'No degree')"
    )

    # Semantic Search Keywords
    semantic_keywords: list[str] = Field(
        default_factory=list,
        description="Extracted skills, technologies, and concepts for semantic search",
    )

    class Config:
        use_enum_values = False
