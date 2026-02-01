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

# Get job details
swiss-jobs detail <job-uuid>

# List providers
swiss-jobs providers

# Check provider health
swiss-jobs health

# Start API server
swiss-jobs serve --port 8000
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

### API Payload Format

The scraper sends the **exact payload format** used by job-room.ch:

```json
{
  "workloadPercentageMin": 10,
  "workloadPercentageMax": 100,
  "permanent": null,
  "companyName": null,
  "onlineSince": 60,
  "displayRestricted": false,
  "professionCodes": [],
  "keywords": [],
  "communalCodes": [],
  "cantonCodes": []
}
```

With location set (e.g., Basel):

```json
{
  "workloadPercentageMin": 10,
  "workloadPercentageMax": 100,
  "permanent": null,
  "companyName": null,
  "onlineSince": 60,
  "displayRestricted": false,
  "professionCodes": [],
  "keywords": [],
  "communalCodes": ["243"],
  "cantonCodes": [],
  "radiusSearchRequest": {
    "geoPoint": {"lat": 47.405, "lon": 8.404},
    "distance": 30
  }
}
```

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
# PROXY_URL=socks5://proxy:1080
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
            ...
        }
    ],
    "total_count": 245,
    "page": 0,
    "page_size": 20,
    "source": "job_room",
    "search_time_ms": 342
}
```

## Configuration

### Environment Variables

```bash
# Optional proxy configuration
SWISS_JOBS_PROXY_URL=socks5://user:pass@proxy:1080

# Execution mode default
SWISS_JOBS_MODE=stealth

# Rate limiting
SWISS_JOBS_REQUESTS_PER_MINUTE=30
```

### Proxy Configuration

For high-volume scraping, use Swiss residential proxies:

```python
from swiss_jobs_scraper.core.session import ProxyPool, ExecutionMode
from swiss_jobs_scraper.providers import JobRoomProvider

proxy_pool = ProxyPool([
    "socks5://user:pass@swiss-proxy-1:1080",
    "socks5://user:pass@swiss-proxy-2:1080",
])

async with JobRoomProvider(
    mode=ExecutionMode.AGGRESSIVE,
    proxy_pool=proxy_pool
) as provider:
    result = await provider.search(request)
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
│   ├── cli/
│   │   └── main.py         # Click-based CLI
│   └── api/
│       ├── main.py         # FastAPI application
│       └── routes/
│           ├── jobs.py     # Job endpoints
│           └── health.py   # Health endpoints
├── tests/
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
pytest tests/ -v

# Run linting
ruff check src/

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
