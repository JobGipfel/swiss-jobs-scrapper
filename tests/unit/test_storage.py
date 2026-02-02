"""
Unit tests for storage module configuration and models.

These tests verify storage configuration and ORM model behavior.
"""


class TestDatabaseSettings:
    """Tests for DatabaseSettings configuration."""

    def test_is_enabled_with_url(self):
        """Test that is_enabled returns True when DATABASE_URL is set."""
        from swiss_jobs_scraper.storage.config import DatabaseSettings

        settings = DatabaseSettings(
            database_url="postgresql+asyncpg://user:pass@localhost/db"
        )
        assert settings.is_enabled is True

    def test_is_enabled_with_password(self):
        """Test that is_enabled returns True when password is set."""
        from swiss_jobs_scraper.storage.config import DatabaseSettings

        settings = DatabaseSettings(
            database_password="secret",
            database_host="localhost",
            database_name="swiss_jobs",
            database_user="postgres",
        )
        assert settings.is_enabled is True

    def test_is_disabled_without_config(self):
        """Test that is_enabled returns False without config."""
        from swiss_jobs_scraper.storage.config import DatabaseSettings

        settings = DatabaseSettings()
        assert settings.is_enabled is False

    def test_connection_url_from_explicit_url(self):
        """Test connection URL is returned when explicitly set."""
        from swiss_jobs_scraper.storage.config import DatabaseSettings

        url = "postgresql+asyncpg://user:pass@localhost/db"
        settings = DatabaseSettings(database_url=url)
        assert settings.connection_url == url

    def test_connection_url_built_from_components(self):
        """Test connection URL is built from components."""
        from swiss_jobs_scraper.storage.config import DatabaseSettings

        settings = DatabaseSettings(
            database_host="db.example.com",
            database_port=5433,
            database_name="jobs",
            database_user="admin",
            database_password="secret123",
        )
        url = settings.connection_url
        assert url is not None
        assert "db.example.com:5433" in url
        assert "admin:secret123" in url
        assert "jobs" in url

    def test_defaults(self):
        """Test default values."""
        from swiss_jobs_scraper.storage.config import DatabaseSettings

        settings = DatabaseSettings()
        assert settings.database_host == "localhost"
        assert settings.database_port == 5432
        assert settings.database_name == "swiss_jobs"
        assert settings.database_user == "postgres"


class TestStoredJobModel:
    """Tests for StoredJob SQLAlchemy model."""

    def test_model_has_required_columns(self):
        """Test StoredJob model has all required columns."""
        from swiss_jobs_scraper.storage.models import StoredJob

        # Check core columns exist
        columns = list(StoredJob.__table__.columns.keys())

        assert "id" in columns
        assert "source_platform" in columns
        assert "title" in columns
        assert "description" in columns
        assert "job_link" in columns
        assert "external_link" in columns
        assert "email" in columns

        # Timestamps
        assert "date_added" in columns
        assert "date_updated" in columns

        # AI fields
        assert "title_de" in columns
        assert "title_fr" in columns
        assert "title_it" in columns
        assert "title_en" in columns
        assert "experience_level" in columns
        assert "ai_processed_at" in columns
        assert "education" in columns
        assert "semantic_keywords" in columns

        # Raw data
        assert "raw_data" in columns
        assert "content_hash" in columns

    def test_table_name(self):
        """Test table name is correct."""
        from swiss_jobs_scraper.storage.models import StoredJob

        assert StoredJob.__tablename__ == "jobs"
