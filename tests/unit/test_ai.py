"""
Unit tests for AI module configuration and models.

These tests verify AI configuration and model behavior.
"""


class TestAISettings:
    """Tests for AISettings configuration."""

    def test_is_enabled_with_provider_and_key(self):
        """Test that is_enabled returns True when provider and key are set."""
        from swiss_jobs_scraper.ai.config import AISettings

        settings = AISettings(ai_provider="gemini", ai_api_key="test_key")
        assert settings.is_enabled is True

    def test_is_disabled_without_provider(self):
        """Test that is_enabled returns False without provider."""
        from swiss_jobs_scraper.ai.config import AISettings

        settings = AISettings(ai_api_key="test_key")
        assert settings.is_enabled is False

    def test_is_disabled_without_key(self):
        """Test that is_enabled returns False without key."""
        from swiss_jobs_scraper.ai.config import AISettings

        settings = AISettings(ai_provider="gemini")
        assert settings.is_enabled is False

    def test_effective_model_gemini_default(self):
        """Test default model for Gemini provider."""
        from swiss_jobs_scraper.ai.config import AISettings

        settings = AISettings(ai_provider="gemini", ai_api_key="test")
        assert settings.effective_model == "gemini-1.5-flash"

    def test_effective_model_groq_default(self):
        """Test default model for Groq provider."""
        from swiss_jobs_scraper.ai.config import AISettings

        settings = AISettings(ai_provider="groq", ai_api_key="test")
        assert settings.effective_model == "llama-3.3-70b-versatile"

    def test_effective_model_custom(self):
        """Test custom model override."""
        from swiss_jobs_scraper.ai.config import AISettings

        settings = AISettings(
            ai_provider="gemini", ai_api_key="test", ai_model="gemini-pro"
        )
        assert settings.effective_model == "gemini-pro"


class TestExperienceLevel:
    """Tests for ExperienceLevel enum."""

    def test_experience_level_values(self):
        """Test ExperienceLevel enum has correct values."""
        from swiss_jobs_scraper.ai.models import ExperienceLevel

        assert ExperienceLevel.ENTRY.value == "entry"
        assert ExperienceLevel.JUNIOR.value == "junior"
        assert ExperienceLevel.MID.value == "mid"
        assert ExperienceLevel.SENIOR.value == "senior"
        assert ExperienceLevel.LEAD.value == "lead"
        assert ExperienceLevel.PRINCIPAL.value == "principal"


class TestProcessedJob:
    """Tests for ProcessedJob model."""

    def test_minimal_processed_job(self):
        """Test ProcessedJob with minimal data."""
        from swiss_jobs_scraper.ai.models import ExperienceLevel, ProcessedJob

        processed = ProcessedJob(
            original_id="test-123",
            title_en="Software Engineer",
            experience_level=ExperienceLevel.MID,
        )

        assert processed.original_id == "test-123"
        assert processed.title_en == "Software Engineer"
        assert processed.experience_level == ExperienceLevel.MID
        assert processed.title_de is None
        assert processed.required_languages == []

    def test_full_processed_job(self):
        """Test ProcessedJob with all fields."""
        from swiss_jobs_scraper.ai.models import ExperienceLevel, ProcessedJob

        processed = ProcessedJob(
            original_id="test-456",
            title_de="Softwareingenieur",
            title_fr="Ingénieur logiciel",
            title_it="Ingegnere del software",
            title_en="Software Engineer",
            description_de="Beschreibung...",
            description_fr="Description...",
            description_it="Descrizione...",
            description_en="Description...",
            required_languages=["de", "en"],
            experience_level=ExperienceLevel.SENIOR,
            years_experience_min=5,
            years_experience_max=8,
            education="Master in CS",
            semantic_keywords=["Python", "Cloud"],
        )

        assert processed.title_de == "Softwareingenieur"
        assert processed.required_languages == ["de", "en"]
        assert processed.years_experience_min == 5
        assert processed.years_experience_max == 8
        assert processed.education == "Master in CS"
        assert processed.semantic_keywords == ["Python", "Cloud"]


class TestPrompts:
    """Tests for AI prompts."""

    def test_system_prompt_exists(self):
        """Test system prompt is defined."""
        from swiss_jobs_scraper.ai.prompts import SYSTEM_PROMPT

        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 50

    def test_get_processing_prompt_all_features(self):
        """Test prompt generation with all features."""
        from swiss_jobs_scraper.ai.features import AIFeature
        from swiss_jobs_scraper.ai.prompts import get_processing_prompt

        all_features = set(AIFeature)
        prompt = get_processing_prompt(
            title="Test Job",
            description="Description...",
            features=all_features,
            language="de",
        )

        assert "Test Job" in prompt
        assert "Description..." in prompt
        assert "Translate the title" in prompt  # Translation feature
        assert "Extract any language" in prompt  # Languages feature
        assert "experience level" in prompt  # Experience feature
        assert "required education" in prompt  # Education feature
        assert "semantic search keywords" in prompt  # Keywords feature

    def test_get_processing_prompt_single_feature(self):
        """Test prompt generation with single feature."""
        from swiss_jobs_scraper.ai.features import AIFeature
        from swiss_jobs_scraper.ai.prompts import get_processing_prompt

        features = {AIFeature.KEYWORDS}
        prompt = get_processing_prompt(
            title="Test Job",
            description="Description...",
            features=features,
            language="en",
        )

        assert "semantic search keywords" in prompt
        assert "Translate the title" not in prompt
        assert "experience level" not in prompt

    def test_description_truncation(self):
        """Test that long descriptions are truncated."""
        from swiss_jobs_scraper.ai.features import AIFeature
        from swiss_jobs_scraper.ai.prompts import get_processing_prompt

        long_description = "x" * 10000
        prompt = get_processing_prompt(
            title="Test",
            description=long_description,
            features={AIFeature.KEYWORDS},
            language="en",
        )

        # Should be truncated to 4000 chars
        assert len(prompt) < len(long_description)


class TestAIFeatures:
    """Tests for AI features."""

    def test_feature_enum(self):
        """Test AIFeature enum values."""
        from swiss_jobs_scraper.ai.features import AIFeature

        assert AIFeature.TRANSLATION == "translation"
        assert AIFeature.EXPERIENCE == "experience"
        assert AIFeature.LANGUAGES == "languages"
        assert AIFeature.EDUCATION == "education"
        assert AIFeature.KEYWORDS == "keywords"
