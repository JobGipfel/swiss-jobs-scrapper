"""
Unit tests for Job-Room provider.

These tests verify BFS location mapping and payload building.
"""

import pytest

from swiss_jobs_scraper.core.exceptions import LocationNotFoundError
from swiss_jobs_scraper.providers.job_room.mapper import BFSLocationMapper


class TestBFSLocationMapper:
    """Tests for BFS location mapping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = BFSLocationMapper()

    def test_resolve_major_city(self):
        """Test resolving major Swiss cities."""
        # Zürich
        codes = self.mapper.resolve("Zürich")
        assert len(codes) > 0
        assert "261" in codes

        # Basel
        codes = self.mapper.resolve("Basel")
        assert len(codes) > 0

        # Bern
        codes = self.mapper.resolve("Bern")
        assert len(codes) > 0

    def test_resolve_postal_code(self):
        """Test resolving Swiss postal codes."""
        # Zürich postal code
        codes = self.mapper.resolve("8000")
        assert len(codes) > 0

        # Basel postal code
        codes = self.mapper.resolve("4000")
        assert len(codes) > 0

    def test_resolve_with_whitespace(self):
        """Test that whitespace is handled."""
        codes = self.mapper.resolve("  Zürich  ")
        assert len(codes) > 0

    def test_resolve_unknown_location(self):
        """Test that unknown locations raise error."""
        with pytest.raises(LocationNotFoundError) as exc_info:
            self.mapper.resolve("Unknown City XYZ")

        assert exc_info.value.location == "Unknown City XYZ"

    def test_resolve_safe_unknown(self):
        """Test safe resolution returns empty list."""
        codes = self.mapper.resolve_safe("Unknown City XYZ")
        assert codes == []

    def test_resolve_safe_known(self):
        """Test safe resolution returns codes."""
        codes = self.mapper.resolve_safe("Zürich")
        assert len(codes) > 0

    def test_resolve_empty_string(self):
        """Test that empty string returns empty list."""
        codes = self.mapper.resolve_safe("")
        assert codes == []

    def test_get_all_cities(self):
        """Test getting all known cities."""
        cities = self.mapper.get_all_cities()
        assert len(cities) > 0
        # Keys are lowercase
        assert "zürich" in cities or "zurich" in cities

    def test_case_insensitivity(self):
        """Test that city name lookup is case-insensitive."""
        lower = self.mapper.resolve_safe("zürich")
        upper = self.mapper.resolve_safe("ZÜRICH")
        mixed = self.mapper.resolve_safe("ZüRiCh")

        assert len(lower) > 0
        assert len(upper) > 0
        assert len(mixed) > 0


class TestJobRoomPayloadBuilder:
    """Tests for Job-Room API payload building."""

    def test_payload_structure(self):
        """Test that payload has correct structure matching Job-Room.ch platform."""
        from swiss_jobs_scraper.core.models import JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        request = JobSearchRequest(
            query="Python Developer",
            workload_min=80,
            workload_max=100,
        )

        # Build payload
        provider = JobRoomProvider.__new__(JobRoomProvider)
        payload = provider._build_search_payload(request)

        # Check required keys exist
        assert "workloadPercentageMin" in payload
        assert "workloadPercentageMax" in payload
        assert "permanent" in payload
        assert "onlineSince" in payload
        assert "displayRestricted" in payload
        assert "keywords" in payload

        # Check values
        assert payload["workloadPercentageMin"] == 80
        assert payload["workloadPercentageMax"] == 100

    def test_default_payload_structure(self):
        """Test default payload matches platform defaults exactly."""
        from swiss_jobs_scraper.core.models import JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        request = JobSearchRequest()

        provider = JobRoomProvider.__new__(JobRoomProvider)
        payload = provider._build_search_payload(request)

        # Platform defaults
        assert payload["workloadPercentageMin"] == 10
        assert payload["workloadPercentageMax"] == 100
        assert payload["permanent"] is None  # 'any' becomes null
        assert payload["onlineSince"] == 60
        assert payload["displayRestricted"] is False

    def test_any_contract_type(self):
        """Test that 'any' contract type becomes null in payload."""
        from swiss_jobs_scraper.core.models import ContractType, JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        request = JobSearchRequest(contract_type=ContractType.ANY)

        provider = JobRoomProvider.__new__(JobRoomProvider)
        payload = provider._build_search_payload(request)

        assert payload["permanent"] is None

    def test_temporary_contract(self):
        """Test temporary contract type."""
        from swiss_jobs_scraper.core.models import ContractType, JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        request = JobSearchRequest(contract_type=ContractType.TEMPORARY)

        provider = JobRoomProvider.__new__(JobRoomProvider)
        payload = provider._build_search_payload(request)

        assert payload["permanent"] is False

    def test_permanent_contract(self):
        """Test permanent contract type."""
        from swiss_jobs_scraper.core.models import ContractType, JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        request = JobSearchRequest(contract_type=ContractType.PERMANENT)

        provider = JobRoomProvider.__new__(JobRoomProvider)
        payload = provider._build_search_payload(request)

        assert payload["permanent"] is True
