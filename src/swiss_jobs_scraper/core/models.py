"""
Generalized input/output models for Swiss Jobs Scraper.

These models provide a standardized interface that works across all job providers.
Each provider transforms their specific data format into these generalized schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Enums
# =============================================================================


class ContractType(str, Enum):
    """Employment contract type."""

    PERMANENT = "permanent"
    TEMPORARY = "temporary"
    ANY = "any"


class WorkForm(str, Enum):
    """Work arrangement type."""

    HOME_WORK = "HOME_WORK"
    SHIFT_WORK = "SHIFT_WORK"
    NIGHT_WORK = "NIGHT_WORK"
    SUNDAY_AND_HOLIDAYS = "SUNDAY_AND_HOLIDAYS"


class LanguageLevel(str, Enum):
    """Language proficiency level."""

    NONE = "NONE"
    BASIC = "BASIC"
    GOOD = "GOOD"
    VERY_GOOD = "VERY_GOOD"
    FLUENT = "FLUENT"
    NATIVE = "NATIVE"


class WorkExperience(str, Enum):
    """Required work experience."""

    NONE = "NONE"
    LESS_THAN_1_YEAR = "LESS_THAN_1_YEAR"
    MORE_THAN_1_YEAR = "MORE_THAN_1_YEAR"
    MORE_THAN_3_YEARS = "MORE_THAN_3_YEARS"


class SortOrder(str, Enum):
    """Search results sort order."""

    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    RELEVANCE = "relevance"


# =============================================================================
# Input Models - Search Request
# =============================================================================


class GeoPoint(BaseModel):
    """Geographic coordinates."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class RadiusSearchRequest(BaseModel):
    """Radius-based location search."""

    geo_point: GeoPoint = Field(..., alias="geoPoint")
    distance: int = Field(
        default=50, ge=1, le=200, description="Search radius in kilometers"
    )

    class Config:
        populate_by_name = True


class LanguageSkillFilter(BaseModel):
    """Filter by required language skills."""

    language_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 639-1 language code (e.g., 'de', 'fr')",
    )
    spoken_level: LanguageLevel | None = None
    written_level: LanguageLevel | None = None


class JobSearchRequest(BaseModel):
    """
    Generalized job search request - works with any provider.

    This model supports ALL filters available in job-room.ch:
    - Keywords/query
    - Location (city, postal code, canton codes, communal codes)
    - Radius search with geo coordinates
    - Workload percentage range
    - Contract type (permanent/temporary)
    - Work forms (home work, shift work, etc.)
    - Profession codes (AVAM codes)
    - Company name
    - Posted within N days
    - Display restricted jobs
    - Language skills
    """

    # === Primary Search Criteria ===
    query: str | None = Field(
        default=None,
        description="Keywords or job title (e.g., 'Software Engineer')",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Multiple keywords for search",
    )

    # === Location Filters ===
    location: str | None = Field(
        default=None,
        description="City name or postal code - will be resolved to BFS codes",
    )
    communal_codes: list[str] = Field(
        default_factory=list,
        description="BFS communal codes (Gemeindenummern)",
    )
    canton_codes: list[str] = Field(
        default_factory=list,
        description="Canton codes (e.g., ['ZH', 'BE'])",
    )
    region_codes: list[str] = Field(
        default_factory=list,
        description="Region codes",
    )
    radius_search: RadiusSearchRequest | None = Field(
        default=None,
        description="Radius search from a geographic point",
    )

    # === Workload Filters ===
    workload_min: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Minimum workload percentage (0-100)",
    )
    workload_max: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Maximum workload percentage (0-100)",
    )

    # === Contract & Employment Filters ===
    contract_type: ContractType = Field(
        default=ContractType.ANY,
        description="Contract type filter",
    )
    work_forms: list[WorkForm] = Field(
        default_factory=list,
        description="Work arrangement filters (home work, shift work, etc.)",
    )

    # === Profession Filters ===
    profession_codes: list[str] = Field(
        default_factory=list,
        description="AVAM profession codes for precise filtering",
    )

    # === Company Filter ===
    company_name: str | None = Field(
        default=None,
        description="Filter by company name",
    )

    # === Time Filters ===
    posted_within_days: int = Field(
        default=60,
        ge=1,
        le=365,
        description="Jobs posted within the last N days",
    )

    # === Display Filters ===
    display_restricted: bool = Field(
        default=False,
        description="Include jobs with restricted visibility",
    )

    # === Language Skills ===
    language_skills: list[LanguageSkillFilter] = Field(
        default_factory=list,
        description="Required language skills",
    )

    # === Pagination & Sorting ===
    page: int = Field(default=0, ge=0, description="Page number (0-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")
    sort: SortOrder = Field(default=SortOrder.DATE_DESC, description="Sort order")

    # === Response Language ===
    language: Literal["en", "de", "fr", "it"] = Field(
        default="en",
        description="Response language (en, de, fr, it)",
    )

    @field_validator("workload_max")
    @classmethod
    def validate_workload_range(cls, v: int, info) -> int:
        """Ensure workload_max >= workload_min."""
        if "workload_min" in info.data and v < info.data["workload_min"]:
            raise ValueError("workload_max must be >= workload_min")
        return v


# =============================================================================
# Output Models - Job Listing Components
# =============================================================================


class Coordinates(BaseModel):
    """Geographic coordinates."""

    lat: float
    lon: float


class JobLocation(BaseModel):
    """Job location details."""

    city: str
    postal_code: str | None = None
    canton_code: str | None = None
    region_code: str | None = None
    communal_code: str | None = None
    country_code: str = "CH"
    coordinates: Coordinates | None = None
    remarks: str | None = None


class CompanyInfo(BaseModel):
    """Company information."""

    name: str = "Anonymous / Chiffre"
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country_code: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    is_agency: bool = False  # 'surrogate' field from API

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_company_name(cls, v: str | None) -> str:
        """Handle anonymous company listings."""
        return v if v else "Anonymous / Chiffre"


class EmploymentDetails(BaseModel):
    """Employment details."""

    start_date: str | None = None
    end_date: str | None = None
    is_permanent: bool = True
    is_immediate: bool = False
    is_short_employment: bool = False
    workload_min: int = 100
    workload_max: int = 100
    work_forms: list[str] = Field(default_factory=list)


class LanguageSkill(BaseModel):
    """Language skill requirement."""

    language_code: str
    spoken_level: str | None = None
    written_level: str | None = None


class Occupation(BaseModel):
    """Occupation/profession details."""

    avam_code: str
    work_experience: str | None = None
    education_code: str | None = None
    qualification_code: str | None = None


class ContactInfo(BaseModel):
    """Public contact information."""

    salutation: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None


class ApplicationChannel(BaseModel):
    """How to apply for the job."""

    email: str | None = None
    phone: str | None = None
    form_url: str | None = None
    post_address: str | None = None
    additional_info: str | None = None


class PublicationInfo(BaseModel):
    """Publication metadata."""

    start_date: str
    end_date: str
    public_display: bool = True
    eures_display: bool = False
    company_anonymous: bool = False
    restricted_display: bool = False


# =============================================================================
# Output Models - Main Job Listing
# =============================================================================


class JobDescription(BaseModel):
    """Job description in a specific language."""

    language_code: str
    title: str
    description: str


class JobListing(BaseModel):
    """
    Standardized job listing - returned by all providers.

    This is the normalized output format that transforms provider-specific
    data into a consistent schema.
    """

    # === Identifiers ===
    id: str = Field(..., description="Unique job identifier (UUID)")
    source: str = Field(..., description="Provider name (e.g., 'job_room')")
    external_reference: str | None = Field(
        default=None, description="External reference number"
    )
    stellennummer_egov: str | None = None
    stellennummer_avam: str | None = None

    # === Core Content ===
    title: str
    descriptions: list[JobDescription] = Field(default_factory=list)
    external_url: str | None = None

    # === Company & Location ===
    company: CompanyInfo
    location: JobLocation
    number_of_positions: int = 1

    # === Employment Details ===
    employment: EmploymentDetails

    # === Requirements ===
    occupations: list[Occupation] = Field(default_factory=list)
    language_skills: list[LanguageSkill] = Field(default_factory=list)

    # === Application ===
    contact: ContactInfo | None = None
    application: ApplicationChannel | None = None

    # === Metadata ===
    publication: PublicationInfo | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str | None = None

    # === Reporting Obligation (Swiss-specific) ===
    reporting_obligation: bool = False
    reporting_obligation_end_date: str | None = None

    # === Raw Data ===
    raw_data: dict[str, Any] | None = Field(
        default=None,
        description="Original provider response for debugging",
    )


# =============================================================================
# Output Models - Search Response
# =============================================================================


class JobSearchResponse(BaseModel):
    """Paginated search response with metadata."""

    items: list[JobListing] = Field(default_factory=list)
    total_count: int = 0
    page: int = 0
    page_size: int = 20
    total_pages: int = 0
    source: str
    search_time_ms: int = 0
    request: JobSearchRequest | None = None

    @property
    def has_more(self) -> bool:
        """Check if there are more pages available."""
        return self.page < self.total_pages - 1
