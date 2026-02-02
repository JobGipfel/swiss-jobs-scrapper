# Swiss Jobs Scraper

A production-grade, extensible job scraper for Swiss job markets. Currently supports **job-room.ch** (the official Swiss federal job portal) with an architecture designed for easy addition of future job sources.

## Features

- **🔍 Comprehensive Search**: All filters supported including location, workload, contract type, work forms, language skills, profession codes
- **🇨🇭 Swiss-Optimized**: BFS communal code resolution, canton filtering, multilingual support (DE/FR/IT/EN)
- **🛡️ Security Bypass**: Browser fingerprint simulation, CSRF handling, TLS fingerprint evasion
- **⚡ Multiple Modes**: Fast, Stealth, or Aggressive execution modes
- **🔌 Dual Interface**: Both CLI and REST API
- **📊 Multiple Output Formats**: JSON, JSONL, CSV, or pretty tables
- **🧩 Extensible**: Abstract provider interface for adding new job sources
- **💾 Database Storage**: Optional PostgreSQL integration for job persistence *(NEW)*
- **🤖 AI Processing**: Optional AI-powered translation and experience level extraction *(NEW)*

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourrepo/swiss-jobs-scrapper.git
cd swiss-jobs-scrapper

# Install with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Using pip

```bash
pip install -e .
```

### Optional Features

```bash
# Install with PostgreSQL support
pip install -e ".[database]"

# Install with AI processing support
pip install -e ".[ai]"

# Install with all optional features
pip install -e ".[all]"
```

## Quick Start

### CLI Usage

```bash
# Basic search
swiss-jobs search "Software Engineer" --location Zurich

# Advanced search with filters
swiss-jobs search "Data Scientist" \
    --canton ZH \
    --canton BE \
    --workload-min 80 \
    --contract permanent \
    --work-form HOME_WORK \
    --days 14 \
    --format json

# Search and save to database
swiss-jobs search "Engineer" --save

# Search with AI processing
swiss-jobs search "Engineer" --ai

# Get job details
swiss-jobs detail <job-uuid>

# List providers
swiss-jobs providers

# Check provider health
swiss-jobs health

# Start API server
swiss-jobs serve --port 8000

# Process stored jobs with AI
swiss-jobs process --limit 100

# View database statistics
swiss-jobs stats
```

### API Usage

Start the server:
```bash
swiss-jobs serve --port 8000
```

Then make requests:

```bash
# Search for jobs
curl -X POST http://localhost:8000/jobs/search \
    -H "Content-Type: application/json" \
    -d '{
        "query": "Software Engineer",
        "location": "Zürich",
        "workload_min": 80,
        "contract_type": "permanent"
    }'

# Search with persistence and AI processing
curl -X POST "http://localhost:8000/jobs/search?persist=true&ai_process=true" \
    -H "Content-Type: application/json" \
    -d '{"query": "Python Developer"}'

# Process stored jobs with AI
curl -X POST "http://localhost:8000/jobs/process?limit=100"

# Get database stats
curl http://localhost:8000/jobs/stats

# Get job details
curl http://localhost:8000/jobs/job_room/{job-uuid}

# Check available providers
curl http://localhost:8000/jobs/providers

# Health check
curl http://localhost:8000/health
```

### Python Library Usage

```python
import asyncio
from swiss_jobs_scraper.core.models import JobSearchRequest, ContractType
from swiss_jobs_scraper.providers import JobRoomProvider
from swiss_jobs_scraper.core.session import ExecutionMode

async def main():
    # Create search request
    request = JobSearchRequest(
        query="Python Developer",
        location="Zürich",
        workload_min=80,
        workload_max=100,
        contract_type=ContractType.PERMANENT,
        posted_within_days=30,
    )
    
    # Search using the provider
    async with JobRoomProvider(mode=ExecutionMode.STEALTH) as provider:
        response = await provider.search(request)
        
        print(f"Found {response.total_count} jobs")
        
        for job in response.items:
            print(f"- {job.title} at {job.company.name}")
            print(f"  Location: {job.location.city}")
            print(f"  Workload: {job.employment.workload_min}-{job.employment.workload_max}%")
            print()

asyncio.run(main())
```

## Database Storage (Optional)

Persist job listings to PostgreSQL with automatic deduplication and change detection.

### Configuration

```bash
# Option 1: Full connection URL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/swiss_jobs

# Option 2: Individual components
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=swiss_jobs
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
```

### Features

- **Auto-migration**: Tables are created automatically on first connection
- **Upsert logic**: Uses content hashing to detect new vs. updated jobs
- **Change tracking**: `date_updated` timestamp tracks when jobs change

### Usage

```bash
# CLI: Save search results to database
swiss-jobs search "Engineer" --save

# API: Include persist flag
curl -X POST "http://localhost:8000/jobs/search?persist=true" ...
```

### Python Example

```python
from swiss_jobs_scraper.storage import get_repository

async def save_jobs(jobs):
    repo = await get_repository()
    result = await repo.upsert_jobs(jobs)
    print(f"Inserted: {result['inserted']}, Updated: {result['updated']}")
```

## AI Post-Processing (Optional)

Enhance job listings with AI-powered translation and analysis.

### Configuration

```bash
# Choose provider: gemini or groq
AI_PROVIDER=gemini

# API key
AI_API_KEY=your_api_key_here

# Optional: Override default model
AI_MODEL=gemini-1.5-flash
```

### Supported Providers

| Provider | Default Model | Cost |
|----------|---------------|------|
| `gemini` | `gemini-1.5-flash` | Free tier available |
| `groq` | `llama-3.3-70b-versatile` | Very fast, free tier |

### AI Features

- **Translation**: Translates title and description to DE, FR, IT, EN
- **Language Extraction**: Identifies required languages from job text
- **Experience Level**: Determines level based on actual requirements, not job titles
  - Levels: `entry`, `junior`, `mid`, `senior`, `lead`, `principal`

### Usage

```bash
# CLI: Apply AI processing to search results
swiss-jobs search "Developer" --ai

# CLI: Process stored jobs in database
swiss-jobs process --limit 100

# API: Include ai_process flag
curl -X POST "http://localhost:8000/jobs/search?ai_process=true" ...

# API: Process stored jobs
curl -X POST "http://localhost:8000/jobs/process?limit=100"
```

### Python Example

```python
from swiss_jobs_scraper.ai import get_processor

async def process_jobs(jobs):
    processor = get_processor()
    if processor.is_enabled:
        results = await processor.process_jobs(jobs)
        for job, result in zip(jobs, results):
            print(f"Title (EN): {result.title_en}")
            print(f"Experience: {result.experience_level}")
```

## Search Filters

The scraper matches the exact payload format of job-room.ch:

| Filter | CLI Option | API Field | Default | Description |
|--------|------------|-----------|---------|-------------|
| Keywords | `--keyword` | `keywords` | `[]` | Multiple search keywords |
| Location | `--location` | `location` | `null` | City name or postal code (resolved to BFS codes) |
| Canton | `--canton` | `canton_codes` | `[]` | Canton codes (ZH, BE, GE, etc.) |
| Communal Codes | - | `communal_codes` | `[]` | BFS Gemeindenummern |
| Workload Min | `--workload-min` | `workload_min` | `10` | Minimum workload % (0-100) |
| Workload Max | `--workload-max` | `workload_max` | `100` | Maximum workload % (0-100) |
| Contract Type | `--contract` | `contract_type` | `any` | permanent, temporary, or any |
| Company | `--company` | `company_name` | `null` | Filter by company name |
| Posted Days | `--days` | `posted_within_days` | `60` | Jobs posted within N days |
| Display Restricted | - | `display_restricted` | `false` | Include restricted visibility jobs |
| Profession Codes | `--profession-code` | `profession_codes` | `[]` | AVAM profession codes |
| Geo Radius | - | `radius_search` | `null` | Geo-based search (lat, lon, distance) |

## Docker Deployment

### Quick Start

```bash
# Production (builds optimized image)
docker compose up -d

# Development (with hot reload)
docker compose -f docker-compose.dev.yml up
```

### Building Images

```bash
# Production build
docker build --target production -t swiss-jobs-scraper .

# Development build
docker build --target development -t swiss-jobs-scraper:dev .
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
APP_ENV=production
API_PORT=8000
WORKERS=4
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=100

# Optional: Proxy configuration
# PROXY_URL=socks5://proxy:1080

# Optional: Database
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/swiss_jobs

# Optional: AI Processing
# AI_PROVIDER=gemini
# AI_API_KEY=your_key
```

## Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `fast` | Minimal headers, no delays | Local testing, low volume |
| `stealth` | Full browser fingerprint simulation | Production use (default) |
| `aggressive` | Stealth + proxy rotation | High volume scraping |

```bash
# CLI
swiss-jobs search "Engineer" --mode aggressive

# API
curl -X POST "http://localhost:8000/jobs/search?mode=aggressive" ...
```

## Output Formats

### CLI Formats

```bash
# Pretty table (default)
swiss-jobs search "Developer" --format table

# JSON (full data)
swiss-jobs search "Developer" --format json

# JSON Lines (one job per line)
swiss-jobs search "Developer" --format jsonl

# CSV
swiss-jobs search "Developer" --format csv
```

### API Response

```json
{
    "items": [
        {
            "id": "uuid-here",
            "source": "job_room",
            "title": "Software Engineer",
            "company": {
                "name": "Example AG",
                "city": "Zürich"
            },
            "location": {
                "city": "Zürich",
                "canton_code": "ZH",
                "postal_code": "8000"
            },
            "employment": {
                "workload_min": 80,
                "workload_max": 100,
                "is_permanent": true
            },
            "raw_data": {
                "ai_processed": {
                    "title_en": "Software Engineer",
                    "title_de": "Softwareingenieur",
                    "experience_level": "mid"
                }
            }
        }
    ],
    "total_count": 245,
    "page": 0,
    "page_size": 20,
    "source": "job_room",
    "search_time_ms": 342
}
```

## API Documentation

When running the API server, interactive documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Adding New Providers

The architecture supports adding new job sources by implementing the `BaseJobProvider` interface:

```python
from swiss_jobs_scraper.core.provider import BaseJobProvider, ProviderCapabilities
from swiss_jobs_scraper.core.models import JobSearchRequest, JobSearchResponse, JobListing

class LinkedInProvider(BaseJobProvider):
    @property
    def name(self) -> str:
        return "linkedin"
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_radius_search=True,
            supports_company_filter=True,
            max_page_size=50,
            supported_languages=["en", "de"],
        )
    
    async def search(self, request: JobSearchRequest) -> JobSearchResponse:
        # Implement search logic
        ...
    
    async def get_details(self, job_id: str, language: str = "en") -> JobListing:
        # Implement detail retrieval
        ...
    
    async def health_check(self) -> ProviderHealth:
        # Implement health check
        ...
```

Then register in `providers/__init__.py`:

```python
from .linkedin import LinkedInProvider

PROVIDERS = {
    "job_room": JobRoomProvider,
    "linkedin": LinkedInProvider,
}
```

## Project Structure

```
swiss-jobs-scraper/
├── src/swiss_jobs_scraper/
│   ├── core/
│   │   ├── models.py       # Generalized input/output schemas
│   │   ├── provider.py     # Abstract base provider
│   │   ├── session.py      # HTTP session with security bypass
│   │   └── exceptions.py   # Exception hierarchy
│   ├── providers/
│   │   └── job_room/
│   │       ├── client.py   # Job-Room API client
│   │       ├── mapper.py   # BFS code mapping
│   │       └── constants.py
│   ├── storage/            # Optional: Database integration
│   │   ├── config.py       # Database settings
│   │   ├── models.py       # SQLAlchemy ORM
│   │   ├── connection.py   # Async connection pool
│   │   └── repository.py   # CRUD operations
│   ├── ai/                 # Optional: AI processing
│   │   ├── config.py       # AI settings
│   │   ├── processor.py    # Main orchestrator
│   │   ├── prompts.py      # LLM prompts
│   │   └── providers/      # Gemini, Groq implementations
│   ├── cli/
│   │   └── main.py         # Click-based CLI
│   └── api/
│       ├── main.py         # FastAPI application
│       └── routes/
│           ├── jobs.py     # Job endpoints
│           └── health.py   # Health endpoints
├── tests/
│   ├── unit/               # Unit tests (no network)
│   ├── integration/        # Integration tests (mocked)
│   └── e2e/                # End-to-end tests (live API)
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=swiss_jobs_scraper --cov-report=html

# Run linting
ruff check src/

# Run formatting
black src/ tests/

# Run type checking
mypy src/
```

## Legal Disclaimer

This tool is intended for legitimate job searching and data aggregation purposes. Users are responsible for:

1. Complying with the terms of service of job-room.ch
2. Respecting rate limits and not overloading the service
3. Using the data in accordance with Swiss data protection laws
4. Not using the tool for unauthorized commercial purposes

The authors are not responsible for any misuse of this tool.

## License

MIT License - see LICENSE file for details.
