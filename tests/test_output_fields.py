"""Quick test to verify keywords, dates, and raw data are working."""

import asyncio
import json
import sys

sys.path.insert(0, "src")

from swiss_jobs_scraper.core.models import JobSearchRequest
from swiss_jobs_scraper.core.session import ExecutionMode
from swiss_jobs_scraper.providers import JobRoomProvider


async def test_multiple_keywords():
    """Test multiple keywords search."""
    print("=" * 60)
    print("Testing Multiple Keywords: ['developer', 'c#', 'english']")
    print("=" * 60)

    request = JobSearchRequest(
        keywords=["developer", "c#", "english"],
        page_size=5,
    )

    # Include raw data
    async with JobRoomProvider(
        mode=ExecutionMode.STEALTH, include_raw_data=True
    ) as provider:
        result = await provider.search(request)

    print(f"✓ Found {result.total_count} jobs")

    for job in result.items[:3]:
        print(f"\n📋 {job.title}")
        print(f"   ID: {job.id}")
        print(f"   Created: {job.created_at}")
        print(f"   Updated: {job.updated_at}")
        print(f"   Has raw_data: {job.raw_data is not None}")
        if job.raw_data:
            print(f"   Raw keys: {list(job.raw_data.keys())[:5]}...")

    return result


async def test_output_fields():
    """Test that all required output fields are present."""
    print("\n" + "=" * 60)
    print("Testing Output Fields (ID, dates, raw data)")
    print("=" * 60)

    request = JobSearchRequest(
        query="Software Engineer",
        page_size=1,
    )

    async with JobRoomProvider(
        mode=ExecutionMode.STEALTH, include_raw_data=True
    ) as provider:
        result = await provider.search(request)

    if result.items:
        job = result.items[0]
        print(f"\n✓ Job ID: {job.id}")
        print(f"✓ Source: {job.source}")
        print(f"✓ Created At: {job.created_at}")
        print(f"✓ Updated At: {job.updated_at}")
        print(f"✓ Status: {job.status}")
        print(f"✓ External Reference: {job.external_reference}")
        print(f"✓ Raw Data Present: {job.raw_data is not None}")

        if job.raw_data:
            print("\n📦 Raw Data Sample (first 500 chars):")
            raw_str = json.dumps(job.raw_data, indent=2, default=str)
            print(raw_str[:500] + "..." if len(raw_str) > 500 else raw_str)

    return True


async def main():
    await test_multiple_keywords()
    await test_output_fields()
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
