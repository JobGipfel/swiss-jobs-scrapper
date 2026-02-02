"""
Job search and retrieval endpoints.
"""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from swiss_jobs_scraper.core.exceptions import (
    LocationNotFoundError,
    ProviderError,
    RateLimitError,
)
from swiss_jobs_scraper.core.models import (
    ContractType,
    GeoPoint,
    JobListing,
    JobSearchRequest,
    JobSearchResponse,
    LanguageSkillFilter,
    RadiusSearchRequest,
    SortOrder,
    WorkForm,
)
from swiss_jobs_scraper.core.session import ExecutionMode
from swiss_jobs_scraper.providers import get_provider, list_providers

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# =============================================================================
# Request/Response Models for API
# =============================================================================


class APISearchRequest(BaseModel):
    """
    API search request model.

    Supports all Job-Room filters with proper documentation.
    """

    # Primary search
    query: str | None = Field(
        default=None,
        description="Keywords or job title",
        examples=["Software Engineer", "Data Scientist"],
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Multiple keywords",
    )

    # Location filters
    location: str | None = Field(
        default=None,
        description="City name or postal code (resolved to BFS codes)",
        examples=["Zürich", "8000", "Geneva"],
    )
    communal_codes: list[str] = Field(
        default_factory=list,
        description="BFS communal codes (Gemeindenummern)",
        examples=[["261", "351"]],
    )
    canton_codes: list[str] = Field(
        default_factory=list,
        description="Canton codes",
        examples=[["ZH", "BE", "GE"]],
    )
    region_codes: list[str] = Field(
        default_factory=list,
        description="Region codes",
    )

    # Radius search
    radius_lat: float | None = Field(
        default=None,
        description="Latitude for radius search",
        ge=-90,
        le=90,
    )
    radius_lon: float | None = Field(
        default=None,
        description="Longitude for radius search",
        ge=-180,
        le=180,
    )
    radius_km: int = Field(
        default=50,
        description="Search radius in kilometers",
        ge=1,
        le=200,
    )

    # Workload
    workload_min: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Minimum workload percentage",
    )
    workload_max: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Maximum workload percentage",
    )

    # Contract
    contract_type: ContractType = Field(
        default=ContractType.ANY,
        description="Contract type filter",
    )
    work_forms: list[WorkForm] = Field(
        default_factory=list,
        description="Work arrangement filters",
    )

    # Profession
    profession_codes: list[str] = Field(
        default_factory=list,
        description="AVAM profession codes",
    )

    # Company
    company_name: str | None = Field(
        default=None,
        description="Filter by company name",
    )

    # Time
    posted_within_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Jobs posted within N days",
    )

    # Visibility
    display_restricted: bool = Field(
        default=False,
        description="Include restricted visibility jobs",
    )

    # Language skills
    language_skills: list[LanguageSkillFilter] = Field(
        default_factory=list,
        description="Required language skills",
    )

    # Pagination
    page: int = Field(default=0, ge=0)
    page_size: int = Field(default=20, ge=1, le=100)
    sort: SortOrder = Field(default=SortOrder.DATE_DESC)

    # Response language
    language: Literal["en", "de", "fr", "it"] = Field(default="en")

    def to_search_request(self) -> JobSearchRequest:
        """Convert to internal JobSearchRequest."""
        # Build radius search if coordinates provided
        radius_search = None
        if self.radius_lat is not None and self.radius_lon is not None:
            radius_search = RadiusSearchRequest(
                geo_point=GeoPoint(lat=self.radius_lat, lon=self.radius_lon),
                distance=self.radius_km,
            )

        return JobSearchRequest(
            query=self.query,
            keywords=self.keywords,
            location=self.location,
            communal_codes=self.communal_codes,
            canton_codes=self.canton_codes,
            region_codes=self.region_codes,
            radius_search=radius_search,
            workload_min=self.workload_min,
            workload_max=self.workload_max,
            contract_type=self.contract_type,
            work_forms=self.work_forms,
            profession_codes=self.profession_codes,
            company_name=self.company_name,
            posted_within_days=self.posted_within_days,
            display_restricted=self.display_restricted,
            language_skills=self.language_skills,
            page=self.page,
            page_size=self.page_size,
            sort=self.sort,
            language=self.language,
        )


class ProvidersResponse(BaseModel):
    """Response listing available providers."""

    providers: list[dict[str, Any]]


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    code: str | None = None


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers() -> dict[str, list[dict[str, Any]]]:
    """
    List all available job providers.

    Returns information about each provider including capabilities.
    """
    providers_info = []

    for name in list_providers():
        provider_cls = get_provider(name)
        provider = provider_cls()
        caps = provider.capabilities

        providers_info.append(
            {
                "name": name,
                "display_name": provider.display_name,
                "capabilities": {
                    "radius_search": caps.supports_radius_search,
                    "canton_filter": caps.supports_canton_filter,
                    "profession_codes": caps.supports_profession_codes,
                    "language_skills": caps.supports_language_skills,
                    "company_filter": caps.supports_company_filter,
                    "work_forms": caps.supports_work_forms,
                    "max_page_size": caps.max_page_size,
                    "supported_languages": caps.supported_languages,
                },
            }
        )

    return {"providers": providers_info}


@router.post(
    "/search",
    response_model=JobSearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Provider error"},
    },
)
async def search_jobs(
    request: APISearchRequest,
    provider: str = Query(default="job_room", description="Provider to use"),
    mode: str = Query(default="stealth", description="Execution mode"),
    include_raw: bool = Query(default=False, description="Include raw API data"),
) -> JobSearchResponse:
    """
    Search for jobs matching the given criteria.

    Supports all available filters for the selected provider.

    ## Examples

    **Basic search:**
    ```json
    {
        "query": "Software Engineer",
        "location": "Zürich"
    }
    ```

    **Advanced search:**
    ```json
    {
        "query": "Python Developer",
        "canton_codes": ["ZH", "BE"],
        "workload_min": 80,
        "contract_type": "permanent",
        "work_forms": ["HOME_WORK"],
        "posted_within_days": 14
    }
    ```

    **Radius search:**
    ```json
    {
        "query": "Engineer",
        "radius_lat": 47.3769,
        "radius_lon": 8.5417,
        "radius_km": 25
    }
    ```
    """
    try:
        # Validate provider
        try:
            provider_cls = get_provider(provider)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        # Validate mode
        try:
            exec_mode = ExecutionMode(mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid mode. Choose from: fast, stealth, aggressive",
            ) from None

        # Convert to internal request
        search_request = request.to_search_request()

        # Execute search
        async with provider_cls(mode=exec_mode, include_raw_data=include_raw) as p:
            result = await p.search(search_request)

        return result

    except LocationNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Location not found: {e.location}",
        ) from e
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e),
            headers={"Retry-After": str(e.retry_after or 60)},
        ) from e
    except ProviderError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/search/quick")
async def quick_search(
    query: str = Query(..., description="Search query"),
    location: str | None = Query(default=None, description="Location"),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=10, ge=1, le=50),
) -> JobSearchResponse:
    """
    Quick search endpoint with minimal parameters.

    For simple searches without complex filters.

    Example:
        GET /jobs/search/quick?query=Developer&location=Zurich
    """
    request = APISearchRequest(
        query=query,
        location=location,
        page=page,
        page_size=page_size,
    )

    return await search_jobs(
        request, provider="job_room", mode="stealth", include_raw=False
    )


@router.get(
    "/{provider}/{job_id}",
    response_model=JobListing,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Provider error"},
    },
)
async def get_job_details(
    provider: str,
    job_id: str,
    language: Literal["en", "de", "fr", "it"] = Query(default="en"),
    mode: str = Query(default="stealth", description="Execution mode"),
    include_raw: bool = Query(default=False, description="Include raw API data"),
) -> JobListing:
    """
    Get full details for a specific job.

    Args:
        provider: Provider name (e.g., "job_room")
        job_id: Job UUID
        language: Preferred language for response
        mode: Execution mode
        include_raw: Include raw API response

    Returns:
        Complete job listing with all details
    """
    try:
        provider_cls = get_provider(provider)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        exec_mode = ExecutionMode(mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode",
        ) from None

    try:
        async with provider_cls(mode=exec_mode, include_raw_data=include_raw) as p:
            result = await p.get_details(job_id, language=language)

        return result

    except ProviderError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404, detail=f"Job not found: {job_id}"
            ) from e
        raise HTTPException(status_code=500, detail=str(e)) from e
