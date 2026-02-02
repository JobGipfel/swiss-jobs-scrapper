"""
Unit tests for core models.

These tests verify Pydantic model validation and serialization.
"""

import pytest
from pydantic import ValidationError

from swiss_jobs_scraper.core.models import (
    ContractType,
    GeoPoint,
    JobLocation,
    JobSearchRequest,
    RadiusSearchRequest,
    SortOrder,
    WorkForm,
)


class TestJobSearchRequest:
    """Tests for JobSearchRequest model."""

    def test_default_values(self):
        """Test default values match Job-Room.ch platform defaults."""
        request = JobSearchRequest()

        assert request.query is None
        assert request.keywords == []
        assert request.location is None
        assert request.workload_min == 10  # Platform default
        assert request.workload_max == 100
        assert request.contract_type == ContractType.ANY
        assert request.posted_within_days == 60  # Platform default
        assert request.display_restricted is False  # Platform default
        assert request.page == 0
        assert request.page_size == 20
        assert request.sort == SortOrder.DATE_DESC
        assert request.language == "en"

    def test_with_query(self):
        """Test request with query."""
        request = JobSearchRequest(
            query="Software Engineer",
            location="Zürich",
        )

        assert request.query == "Software Engineer"
        assert request.location == "Zürich"

    def test_with_all_filters(self):
        """Test request with all filters."""
        request = JobSearchRequest(
            query="Python Developer",
            keywords=["Django", "FastAPI"],
            location="Bern",
            canton_codes=["BE", "ZH"],
            workload_min=80,
            workload_max=100,
            contract_type=ContractType.PERMANENT,
            work_forms=[WorkForm.HOME_WORK],
            company_name="Example AG",
            posted_within_days=14,
            profession_codes=["12345"],
            page=1,
            page_size=50,
            sort=SortOrder.DATE_ASC,
            language="de",
        )

        assert request.query == "Python Developer"
        assert request.keywords == ["Django", "FastAPI"]
        assert request.canton_codes == ["BE", "ZH"]
        assert request.workload_min == 80
        assert request.contract_type == ContractType.PERMANENT
        assert WorkForm.HOME_WORK in request.work_forms

    def test_workload_validation(self):
        """Test workload percentage validation."""
        # Valid range
        request = JobSearchRequest(workload_min=50, workload_max=80)
        assert request.workload_min == 50
        assert request.workload_max == 80

        # Out of range
        with pytest.raises(ValidationError):
            JobSearchRequest(workload_min=-10)

        with pytest.raises(ValidationError):
            JobSearchRequest(workload_max=150)

    def test_radius_search(self):
        """Test radius search configuration."""
        request = JobSearchRequest(
            radius_search=RadiusSearchRequest(
                geo_point=GeoPoint(lat=47.3769, lon=8.5417),
                distance=25,
            )
        )

        assert request.radius_search is not None
        assert request.radius_search.geo_point.lat == 47.3769
        assert request.radius_search.geo_point.lon == 8.5417
        assert request.radius_search.distance == 25

    def test_geo_point_validation(self):
        """Test GeoPoint coordinate validation."""
        # Valid coordinates
        point = GeoPoint(lat=47.3769, lon=8.5417)
        assert point.lat == 47.3769

        # Invalid latitude
        with pytest.raises(ValidationError):
            GeoPoint(lat=100, lon=8.5417)

        # Invalid longitude
        with pytest.raises(ValidationError):
            GeoPoint(lat=47.3769, lon=200)


class TestJobLocation:
    """Tests for JobLocation model."""

    def test_minimal_location(self):
        """Test location with minimal data."""
        location = JobLocation(city="Zürich")

        assert location.city == "Zürich"
        assert location.country_code == "CH"  # Default
        assert location.postal_code is None

    def test_full_location(self):
        """Test location with all fields."""
        location = JobLocation(
            city="Zürich",
            postal_code="8000",
            canton_code="ZH",
            region_code="ZH01",
            communal_code="261",
            country_code="CH",
        )

        assert location.city == "Zürich"
        assert location.postal_code == "8000"
        assert location.canton_code == "ZH"
        assert location.communal_code == "261"


class TestEnums:
    """Tests for enum types."""

    def test_contract_type_values(self):
        """Test ContractType enum values."""
        assert ContractType.PERMANENT.value == "permanent"
        assert ContractType.TEMPORARY.value == "temporary"
        assert ContractType.ANY.value == "any"

    def test_work_form_values(self):
        """Test WorkForm enum values."""
        assert WorkForm.HOME_WORK.value == "HOME_WORK"
        assert WorkForm.SHIFT_WORK.value == "SHIFT_WORK"
        assert WorkForm.NIGHT_WORK.value == "NIGHT_WORK"

    def test_sort_order_values(self):
        """Test SortOrder enum values."""
        assert SortOrder.DATE_DESC.value == "date_desc"
        assert SortOrder.DATE_ASC.value == "date_asc"
        assert SortOrder.RELEVANCE.value == "relevance"
