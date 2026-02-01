"""Tests for Job-Room provider."""

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
        codes = self.mapper.resolve("Zurich")
        assert codes == ["261"]

        codes = self.mapper.resolve("zürich")
        assert codes == ["261"]

        # Bern
        codes = self.mapper.resolve("Bern")
        assert codes == ["351"]

        # Geneva
        codes = self.mapper.resolve("Geneva")
        assert codes == ["6621"]

        codes = self.mapper.resolve("genève")
        assert codes == ["6621"]

    def test_resolve_postal_code(self):
        """Test resolving Swiss postal codes."""
        # Zürich postal codes
        codes = self.mapper.resolve("8000")
        assert codes == ["261"]

        codes = self.mapper.resolve("8001")
        assert codes == ["261"]

        # Bern postal codes
        codes = self.mapper.resolve("3000")
        assert codes == ["351"]

        # Geneva postal codes
        codes = self.mapper.resolve("1200")
        assert codes == ["6621"]

    def test_resolve_with_whitespace(self):
        """Test that whitespace is handled."""
        codes = self.mapper.resolve("  Zurich  ")
        assert codes == ["261"]

    def test_resolve_unknown_location(self):
        """Test that unknown locations raise error."""
        with pytest.raises(LocationNotFoundError) as exc_info:
            self.mapper.resolve("UnknownCity123")

        assert "UnknownCity123" in str(exc_info.value)

    def test_resolve_safe_unknown(self):
        """Test safe resolution returns empty list."""
        codes = self.mapper.resolve_safe("UnknownCity123")
        assert codes == []

    def test_resolve_safe_known(self):
        """Test safe resolution returns codes."""
        codes = self.mapper.resolve_safe("Zurich")
        assert codes == ["261"]

    def test_resolve_empty_string(self):
        """Test that empty string returns empty list."""
        codes = self.mapper.resolve("")
        assert codes == []

    def test_get_all_cities(self):
        """Test getting all known cities."""
        cities = self.mapper.get_all_cities()

        assert isinstance(cities, list)
        assert len(cities) > 0
        assert "zurich" in cities or "zürich" in cities

    def test_case_insensitivity(self):
        """Test that city name lookup is case-insensitive."""
        codes1 = self.mapper.resolve("ZURICH")
        codes2 = self.mapper.resolve("zurich")
        codes3 = self.mapper.resolve("Zurich")

        assert codes1 == codes2 == codes3

    def test_partial_match(self):
        """Test partial matching for city names."""
        # "winter" should match "winterthur"
        codes = self.mapper.resolve("winterthur")
        assert codes == ["230"]


class TestJobRoomPayloadBuilder:
    """Tests for Job-Room API payload building."""

    def test_payload_structure(self):
        """Test that payload has correct structure matching Job-Room.ch platform."""
        from swiss_jobs_scraper.core.models import ContractType, JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        provider = JobRoomProvider()
        request = JobSearchRequest(
            query="Python Developer",
            location="Zurich",
            workload_min=80,
            workload_max=100,
            contract_type=ContractType.PERMANENT,
        )

        payload = provider._build_search_payload(request)

        # Check ALL required fields are present (matching platform format)
        assert "keywords" in payload
        assert "Python Developer" in payload["keywords"]

        assert "communalCodes" in payload
        assert "261" in payload["communalCodes"]  # Zurich

        assert "cantonCodes" in payload
        assert payload["cantonCodes"] == []

        assert payload["workloadPercentageMin"] == 80
        assert payload["workloadPercentageMax"] == 100
        assert payload["permanent"] is True  # PERMANENT contract

        # Platform always sends these fields
        assert "onlineSince" in payload
        assert "displayRestricted" in payload
        assert "professionCodes" in payload
        assert "companyName" in payload

    def test_default_payload_structure(self):
        """Test default payload matches platform defaults exactly."""
        from swiss_jobs_scraper.core.models import JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        provider = JobRoomProvider()
        request = JobSearchRequest()  # All defaults

        payload = provider._build_search_payload(request)

        # Platform defaults
        assert payload["workloadPercentageMin"] == 10  # Platform default
        assert payload["workloadPercentageMax"] == 100
        assert payload["permanent"] is None  # ANY contract type
        assert payload["companyName"] is None
        assert payload["onlineSince"] == 60  # Platform default
        assert payload["displayRestricted"] is False
        assert payload["professionCodes"] == []
        assert payload["keywords"] == []
        assert payload["communalCodes"] == []
        assert payload["cantonCodes"] == []

        # radiusSearchRequest should NOT be in payload when no location
        assert "radiusSearchRequest" not in payload

    def test_any_contract_type(self):
        """Test that 'any' contract type becomes null in payload."""
        from swiss_jobs_scraper.core.models import ContractType, JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        provider = JobRoomProvider()
        request = JobSearchRequest(
            query="Test",
            contract_type=ContractType.ANY,
        )

        payload = provider._build_search_payload(request)

        # 'any' should result in null/None for the API
        assert payload["permanent"] is None

    def test_temporary_contract(self):
        """Test temporary contract type."""
        from swiss_jobs_scraper.core.models import ContractType, JobSearchRequest
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        provider = JobRoomProvider()
        request = JobSearchRequest(
            query="Test",
            contract_type=ContractType.TEMPORARY,
        )

        payload = provider._build_search_payload(request)
        assert payload["permanent"] is False

    def test_radius_search_in_payload(self):
        """Test radius search is included when geo coordinates are provided."""
        from swiss_jobs_scraper.core.models import (
            GeoPoint,
            JobSearchRequest,
            RadiusSearchRequest,
        )
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        provider = JobRoomProvider()
        request = JobSearchRequest(
            query="Test",
            radius_search=RadiusSearchRequest(
                geo_point=GeoPoint(lat=47.405, lon=8.404),
                distance=30,
            ),
        )

        payload = provider._build_search_payload(request)

        # radiusSearchRequest should be present
        assert "radiusSearchRequest" in payload
        assert payload["radiusSearchRequest"]["geoPoint"]["lat"] == 47.405
        assert payload["radiusSearchRequest"]["geoPoint"]["lon"] == 8.404
        assert payload["radiusSearchRequest"]["distance"] == 30


class TestJobRoomURLBuilder:
    """Tests for Job-Room URL building."""

    def test_search_url(self):
        """Test search URL construction."""
        from swiss_jobs_scraper.core.models import JobSearchRequest, SortOrder
        from swiss_jobs_scraper.providers.job_room.client import JobRoomProvider

        provider = JobRoomProvider()
        request = JobSearchRequest(
            page=2,
            page_size=50,
            sort=SortOrder.DATE_DESC,
            language="de",
        )

        url = provider._build_search_url(request)

        assert "page=2" in url
        assert "size=50" in url
        assert "sort=date_desc" in url
        assert "_ng=ZGU=" in url  # base64 for "de"

    def test_language_encoding(self):
        """Test language parameter encoding."""
        from swiss_jobs_scraper.providers.job_room.constants import LANGUAGE_PARAMS

        # Verify base64 encodings
        assert LANGUAGE_PARAMS["en"] == "ZW4="
        assert LANGUAGE_PARAMS["de"] == "ZGU="
        assert LANGUAGE_PARAMS["fr"] == "ZnI="
        assert LANGUAGE_PARAMS["it"] == "aXQ="
