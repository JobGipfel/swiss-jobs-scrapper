"""
End-to-end tests for Swiss Jobs Scraper.

These tests perform actual API calls to job-room.ch to verify the scraper works.
Run with: pytest tests/e2e/ -v --run-live

Note: These tests require network access and may be slow or fail due to rate limiting.
"""

import asyncio

import pytest

from swiss_jobs_scraper.core.models import (
    ContractType,
    GeoPoint,
    JobSearchRequest,
    RadiusSearchRequest,
)
from swiss_jobs_scraper.core.session import ExecutionMode
from swiss_jobs_scraper.providers import JobRoomProvider

# Mark all tests in this module as requiring --run-live flag
pytestmark = pytest.mark.live


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestBasicSearch:
    """Tests for basic search functionality."""

    @pytest.mark.asyncio
    async def test_keyword_search(self):
        """Test basic keyword search."""
        request = JobSearchRequest(
            query="Software Engineer",
            page_size=5,
        )

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            result = await provider.search(request)

        assert result.total_count > 0
        assert len(result.items) > 0
        assert result.items[0].title is not None

    @pytest.mark.asyncio
    async def test_multiple_keywords(self):
        """Test search with multiple keywords."""
        request = JobSearchRequest(
            keywords=["developer", "python"],
            page_size=5,
        )

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            result = await provider.search(request)

        assert result.total_count > 0


class TestLocationFilter:
    """Tests for location-based filtering."""

    @pytest.mark.asyncio
    async def test_city_filter(self):
        """Test filter by city name."""
        request = JobSearchRequest(
            query="Engineer",
            location="Zürich",
            page_size=5,
        )

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            result = await provider.search(request)

        assert result.total_count > 0

    @pytest.mark.asyncio
    async def test_canton_filter(self):
        """Test filter by canton."""
        request = JobSearchRequest(
            query="Developer",
            canton_codes=["ZH", "BE"],
            page_size=5,
        )

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            result = await provider.search(request)

        assert result.total_count > 0

    @pytest.mark.asyncio
    async def test_radius_search(self):
        """Test geo-location radius search."""
        request = JobSearchRequest(
            radius_search=RadiusSearchRequest(
                geo_point=GeoPoint(lat=47.3769, lon=8.5417),  # Zurich
                distance=25,
            ),
            page_size=5,
        )

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            result = await provider.search(request)

        assert result.total_count > 0


class TestWorkloadFilter:
    """Tests for workload filtering."""

    @pytest.mark.asyncio
    async def test_workload_filter(self):
        """Test filter by workload percentage."""
        request = JobSearchRequest(
            query="Developer",
            workload_min=80,
            workload_max=100,
            page_size=5,
        )

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            result = await provider.search(request)

        assert result.total_count > 0
        # Verify workload range
        for job in result.items:
            if job.employment:
                assert (
                    job.employment.workload_min >= 80
                    or job.employment.workload_max >= 80
                )


class TestContractFilter:
    """Tests for contract type filtering."""

    @pytest.mark.asyncio
    async def test_permanent_contract(self):
        """Test filter for permanent positions."""
        request = JobSearchRequest(
            query="Engineer",
            contract_type=ContractType.PERMANENT,
            page_size=5,
        )

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            result = await provider.search(request)

        assert result.total_count > 0


class TestJobDetails:
    """Tests for job detail retrieval."""

    @pytest.mark.asyncio
    async def test_get_job_details(self):
        """Test getting full job details."""
        # First, search for a job
        request = JobSearchRequest(query="Developer", page_size=1)

        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            search_result = await provider.search(request)

            if search_result.items:
                job_id = search_result.items[0].id

                # Get details
                details = await provider.get_details(job_id)

                assert details.id == job_id
                assert details.title is not None


class TestProviderHealth:
    """Tests for provider health check."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test provider health check."""
        async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
            health = await provider.health_check()

        assert health.provider == "job_room"
        assert health.status is not None


class TestRawData:
    """Tests for raw data inclusion."""

    @pytest.mark.asyncio
    async def test_include_raw_data(self):
        """Test that raw data is included when requested."""
        request = JobSearchRequest(query="Developer", page_size=1)

        async with JobRoomProvider(
            mode=ExecutionMode.STEALTH, include_raw_data=True
        ) as provider:
            result = await provider.search(request)

        if result.items:
            assert result.items[0].raw_data is not None
            assert isinstance(result.items[0].raw_data, dict)
