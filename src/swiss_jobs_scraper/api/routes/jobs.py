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
    persist: bool = Query(default=False, description="Save results to database"),
    ai_process: bool = Query(
        default=False, description="Apply AI post-processing (translation + analysis)"
    ),
    features: str | None = Query(
        default=None,
        description=(
            "Comma-separated list of AI features "
            "(translation,experience,languages,education,keywords). Defaults to all."
        ),
    ),
) -> JobSearchResponse:
    """
    Search for jobs matching the given criteria.

    Supports all available filters for the selected provider.

    ## Optional Features

    - **persist**: Set to `true` to save results to PostgreSQL (requires database config)
    - **ai_process**: Set to `true` to apply AI translation and analysis (requires AI config)
    - **features**: Comma-separated list of AI features to apply (e.g., `translation,keywords`)

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
        "canton_codes": ["ZH"],
        "workload_min": 80,
        "contract_type": "permanent"
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

        # Parse features
        ai_features = None
        if features:
            try:
                from swiss_jobs_scraper.ai.features import AIFeature

                ai_features = {AIFeature(f.strip()) for f in features.split(",")}
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid feature: {str(e)}"
                ) from e

        # Convert to internal request
        search_request = request.to_search_request()

        # Execute search
        async with provider_cls(mode=exec_mode, include_raw_data=include_raw) as p:
            result = await p.search(search_request)

        # Optional: Persist to database
        if persist:
            try:
                from swiss_jobs_scraper.storage import get_repository
                from swiss_jobs_scraper.storage.config import get_database_settings

                db_settings = get_database_settings()
                if db_settings.is_enabled:
                    repo = await get_repository()
                    counts = await repo.upsert_jobs(result.items)
                    # Add persistence info to response (in raw_data if enabled)
                    if include_raw and result.request:
                        result.request = result.request.model_copy(
                            update={"raw_data": {"persistence": counts}}
                        )
            except ImportError:
                pass  # Database dependencies not installed

        # Optional: AI post-processing
        if ai_process:
            try:
                from swiss_jobs_scraper.ai import get_processor

                processor = get_processor()
                if processor.is_enabled:
                    processed_jobs = await processor.process_jobs(
                        result.items, features=ai_features
                    )
                    # Enrich items with AI data (add to raw_data)
                    for job, processed in zip(
                        result.items, processed_jobs, strict=True
                    ):
                        if job.raw_data is None:
                            job.raw_data = {}
                        job.raw_data["ai_processed"] = processed.model_dump(mode="json")
            except ImportError:
                pass  # AI dependencies not installed

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
        request,
        provider="job_room",
        mode="stealth",
        include_raw=False,
        persist=False,
        ai_process=False,
        features=None,
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


# =============================================================================
# Database & AI Processing Endpoints
# =============================================================================


class ProcessingResult(BaseModel):
    """Result of AI processing operation."""

    processed: int = Field(description="Number of jobs processed")
    errors: int = Field(description="Number of errors during processing")
    message: str = Field(description="Status message")


class DatabaseStats(BaseModel):
    """Database statistics."""

    total_jobs: int = Field(description="Total jobs in database")
    unprocessed_jobs: int = Field(description="Jobs needing AI processing")
    enabled: bool = Field(description="Whether database is enabled")


@router.post(
    "/process",
    response_model=ProcessingResult,
    responses={
        503: {"model": ErrorResponse, "description": "Database or AI not configured"},
    },
)
async def process_stored_jobs(
    limit: int = Query(default=100, ge=1, le=1000, description="Max jobs to process"),
) -> ProcessingResult:
    """
    Process unprocessed jobs from the database with AI.

    Applies AI post-processing (translation + experience analysis) to jobs
    that haven't been processed yet or have been updated since last processing.

    Requires both database and AI to be configured via environment variables.
    """
    try:
        from swiss_jobs_scraper.storage import get_repository
        from swiss_jobs_scraper.storage.config import get_database_settings
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Database dependencies not installed. "
            "Install with: pip install swiss-jobs-scraper[database]",
        ) from None

    try:
        from swiss_jobs_scraper.ai import get_processor
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="AI dependencies not installed. "
            "Install with: pip install swiss-jobs-scraper[ai]",
        ) from None

    db_settings = get_database_settings()
    if not db_settings.is_enabled:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Set DATABASE_URL or DATABASE_PASSWORD.",
        )

    processor = get_processor()
    if not processor.is_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI not configured. Set AI_PROVIDER and AI_API_KEY.",
        )

    # Get unprocessed jobs
    repo = await get_repository()
    unprocessed = await repo.get_unprocessed_jobs(limit=limit)

    if not unprocessed:
        return ProcessingResult(
            processed=0,
            errors=0,
            message="No jobs to process",
        )

    # Process each job
    processed_count = 0
    error_count = 0

    for stored_job in unprocessed:
        try:
            # Reconstruct JobListing from raw_data
            from swiss_jobs_scraper.core.models import JobListing

            if stored_job.raw_data:
                job = JobListing.model_validate(stored_job.raw_data)
                result = await processor.process_job(job)
                await repo.mark_ai_processed(stored_job.id, result)
                processed_count += 1
        except Exception:
            error_count += 1

    return ProcessingResult(
        processed=processed_count,
        errors=error_count,
        message=f"Processed {processed_count} jobs with {error_count} errors",
    )


@router.get(
    "/stats",
    response_model=DatabaseStats,
)
async def get_database_stats() -> DatabaseStats:
    """
    Get database statistics.

    Returns counts of total and unprocessed jobs.
    """
    try:
        from swiss_jobs_scraper.storage import get_repository
        from swiss_jobs_scraper.storage.config import get_database_settings
    except ImportError:
        return DatabaseStats(total_jobs=0, unprocessed_jobs=0, enabled=False)

    db_settings = get_database_settings()
    if not db_settings.is_enabled:
        return DatabaseStats(total_jobs=0, unprocessed_jobs=0, enabled=False)

    try:
        repo = await get_repository()
        total = await repo.get_jobs_count()
        unprocessed = await repo.get_unprocessed_count()
        return DatabaseStats(
            total_jobs=total,
            unprocessed_jobs=unprocessed,
            enabled=True,
        )
    except Exception:
        return DatabaseStats(total_jobs=0, unprocessed_jobs=0, enabled=False)
