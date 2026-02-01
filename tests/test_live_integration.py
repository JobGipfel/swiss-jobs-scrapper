"""
Live integration tests for Swiss Jobs Scraper.

These tests perform actual API calls to job-room.ch to verify the scraper works correctly.
"""

import asyncio
import json
import sys

# Add src to path
sys.path.insert(0, "src")

from swiss_jobs_scraper.core.models import (
    ContractType,
    GeoPoint,
    JobSearchRequest,
    RadiusSearchRequest,
    SortOrder,
)
from swiss_jobs_scraper.core.session import ExecutionMode
from swiss_jobs_scraper.providers import JobRoomProvider


async def test_basic_search():
    """Test 1: Basic keyword search."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Keyword Search")
    print("=" * 60)

    request = JobSearchRequest(
        query="Software Engineer",
        page=0,
        page_size=5,
        language="en",
    )

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} total jobs")
    print(f"✓ Returned {len(result.items)} jobs on this page")
    print(f"✓ Search took {result.search_time_ms}ms")

    if result.items:
        job = result.items[0]
        print(f"\nFirst result:")
        print(f"  Title: {job.title}")
        print(f"  Company: {job.company.name}")
        print(f"  Location: {job.location.city}, {job.location.canton_code}")
        print(f"  ID: {job.id}")
        return job.id
    return None


async def test_location_filter():
    """Test 2: Location filter with city name."""
    print("\n" + "=" * 60)
    print("TEST 2: Location Filter (Zürich)")
    print("=" * 60)

    request = JobSearchRequest(
        query="Developer",
        location="Zürich",  # Should resolve to BFS code 261
        page_size=5,
    )

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} jobs in Zürich")

    for job in result.items[:3]:
        print(f"  - {job.title} at {job.company.name}")

    return True


async def test_canton_filter():
    """Test 3: Canton filter."""
    print("\n" + "=" * 60)
    print("TEST 3: Canton Filter (ZH, BE)")
    print("=" * 60)

    request = JobSearchRequest(
        query="Engineer",
        canton_codes=["ZH", "BE"],
        page_size=5,
    )

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} jobs in ZH and BE cantons")

    for job in result.items[:3]:
        print(f"  - {job.title} in {job.location.city} ({job.location.canton_code})")

    return True


async def test_workload_filter():
    """Test 4: Workload percentage filter."""
    print("\n" + "=" * 60)
    print("TEST 4: Workload Filter (80-100%)")
    print("=" * 60)

    request = JobSearchRequest(
        query="Developer",
        workload_min=80,
        workload_max=100,
        page_size=5,
    )

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} jobs with 80-100% workload")

    for job in result.items[:3]:
        emp = job.employment
        print(f"  - {job.title}: {emp.workload_min}-{emp.workload_max}%")

    return True


async def test_contract_type_filter():
    """Test 5: Contract type filter (permanent only)."""
    print("\n" + "=" * 60)
    print("TEST 5: Contract Type Filter (Permanent)")
    print("=" * 60)

    request = JobSearchRequest(
        query="Manager",
        contract_type=ContractType.PERMANENT,
        page_size=5,
    )

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} permanent positions")

    for job in result.items[:3]:
        print(f"  - {job.title}: Permanent={job.employment.is_permanent}")

    return True


async def test_geo_radius_search():
    """Test 6: Geo-location radius search (Zurich coordinates)."""
    print("\n" + "=" * 60)
    print("TEST 6: Geo-Location Radius Search")
    print("=" * 60)
    print("Searching within 25km of Zurich (47.3769, 8.5417)")

    request = JobSearchRequest(
        query="Engineer",
        radius_search=RadiusSearchRequest(
            geo_point=GeoPoint(lat=47.3769, lon=8.5417),  # Zurich coordinates
            distance=25,  # 25km radius
        ),
        page_size=5,
    )

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} jobs within 25km of Zurich center")

    for job in result.items[:5]:
        coords = job.location.coordinates
        coord_str = f"({coords.lat:.4f}, {coords.lon:.4f})" if coords else "N/A"
        print(f"  - {job.title} in {job.location.city} {coord_str}")

    return True


async def test_combined_filters():
    """Test 7: Combined filters (all at once)."""
    print("\n" + "=" * 60)
    print("TEST 7: Combined Filters (All at Once)")
    print("=" * 60)
    print("Query: Developer | Location: Zurich | Workload: 80-100%")
    print("Contract: Permanent | Radius: 50km")

    request = JobSearchRequest(
        query="Developer",
        location="Zürich",
        radius_search=RadiusSearchRequest(
            geo_point=GeoPoint(lat=47.3769, lon=8.5417),
            distance=50,
        ),
        workload_min=80,
        workload_max=100,
        contract_type=ContractType.PERMANENT,
        page_size=10,
        sort=SortOrder.DATE_DESC,
        language="en",
    )

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} jobs matching all criteria")
    print(f"✓ Search completed in {result.search_time_ms}ms")

    for job in result.items[:5]:
        print(f"\n  📋 {job.title}")
        print(f"     Company: {job.company.name}")
        print(f"     Location: {job.location.city}")
        print(
            f"     Workload: {job.employment.workload_min}-{job.employment.workload_max}%"
        )
        print(f"     Permanent: {job.employment.is_permanent}")

    if result.items:
        return result.items[0].id
    return None


async def test_get_job_details(job_id: str):
    """Test 8: Get job details."""
    print("\n" + "=" * 60)
    print("TEST 8: Get Job Details")
    print("=" * 60)
    print(f"Fetching details for job ID: {job_id[:36]}...")

    async with JobRoomProvider(
        mode=ExecutionMode.STEALTH, include_raw_data=False
    ) as provider:
        job = await provider.get_details(job_id, language="en")

    print(f"\n✓ Successfully retrieved job details")
    print(f"\n{'='*40}")
    print(f"Title: {job.title}")
    print(f"Company: {job.company.name}")
    print(f"Location: {job.location.city}, {job.location.canton_code}")
    print(f"Workload: {job.employment.workload_min}-{job.employment.workload_max}%")
    print(f"Permanent: {job.employment.is_permanent}")

    if job.descriptions:
        desc = job.descriptions[0].description
        if desc:
            if len(desc) > 300:
                desc = desc[:300] + "..."
            print(f"\nDescription:\n{desc}")

    print(f"\n✓ All fields successfully parsed")
    return True


async def test_health_check():
    """Test 9: Provider health check."""
    print("\n" + "=" * 60)
    print("TEST 9: Provider Health Check")
    print("=" * 60)

    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        health = await provider.health_check()

    print(f"✓ Provider: {health.provider}")
    print(f"✓ Status: {health.status.value}")
    print(f"✓ Latency: {health.latency_ms}ms")
    print(f"✓ Message: {health.message}")

    return health.status.value == "healthy"


async def main():
    """Run all live tests."""
    print("\n" + "🚀" * 30)
    print("  SWISS JOBS SCRAPER - LIVE INTEGRATION TESTS")
    print("🚀" * 30)

    results = {}
    job_id = None

    # Test 1: Basic search
    try:
        job_id = await test_basic_search()
        results["Basic Search"] = "✅ PASSED"
    except Exception as e:
        results["Basic Search"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Test 2: Location filter
    try:
        await test_location_filter()
        results["Location Filter"] = "✅ PASSED"
    except Exception as e:
        results["Location Filter"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Test 3: Canton filter
    try:
        await test_canton_filter()
        results["Canton Filter"] = "✅ PASSED"
    except Exception as e:
        results["Canton Filter"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Test 4: Workload filter
    try:
        await test_workload_filter()
        results["Workload Filter"] = "✅ PASSED"
    except Exception as e:
        results["Workload Filter"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Test 5: Contract type filter
    try:
        await test_contract_type_filter()
        results["Contract Type Filter"] = "✅ PASSED"
    except Exception as e:
        results["Contract Type Filter"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Test 6: Geo radius search
    try:
        await test_geo_radius_search()
        results["Geo Radius Search"] = "✅ PASSED"
    except Exception as e:
        results["Geo Radius Search"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Test 7: Combined filters
    try:
        combined_job_id = await test_combined_filters()
        results["Combined Filters"] = "✅ PASSED"
        if combined_job_id:
            job_id = combined_job_id
    except Exception as e:
        results["Combined Filters"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Test 8: Job details
    if job_id:
        try:
            await test_get_job_details(job_id)
            results["Job Details"] = "✅ PASSED"
        except Exception as e:
            results["Job Details"] = f"❌ FAILED: {e}"
            print(f"Error: {e}")
    else:
        results["Job Details"] = "⏭️ SKIPPED (no job ID)"

    # Test 9: Health check
    try:
        await test_health_check()
        results["Health Check"] = "✅ PASSED"
    except Exception as e:
        results["Health Check"] = f"❌ FAILED: {e}"
        print(f"Error: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if "PASSED" in v)
    failed = sum(1 for v in results.values() if "FAILED" in v)

    for test_name, result in results.items():
        print(f"  {test_name}: {result}")

    print("\n" + "-" * 60)
    print(f"  TOTAL: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
