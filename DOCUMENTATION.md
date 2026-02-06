# System Reference Manual - Swiss Jobs Scraper 🇨🇭

> **Version**: 2.0.0
> **Target Audience**: Developers, System Architects, AI Agents
> **Purpose**: Definitive source of truth for schema, API, and internal logic.

This document describes the Swiss Jobs Scraper system. It is structured to be parsed by LLMs or developers requiring exact specifications.

---

## 1. System Architecture

The system follows a **2-Layer Architecture** designed for resilience and separation of concerns:

1.  **Ingestion Layer (Providers)**
    *   Fetches raw data from external sources (currently `job_room`).
    *   Handles platform-specific pagination and payload mapping.
    *   Detects API limits and reports stop reasons.
2.  **Processing Layer (Core)**
    *   Normalizes data into a unified `Job` model.
    *   **Stealth Engine**: Simulates browser fingerprints (Chrome 120+), Client Hints, and handles complex CSRF tokens for SPA backends.
    *   **BFS Resolver**: Maps city names ("Zürich") to BFS Communal Codes ("261") for accurate Swiss geo-filtering.

---

## 2. Configuration (`.env`)

Configure the application via environment variables.

### Core Settings
| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `production` | Environment: `production` or `development`. |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG` for tracing requests). |
| `API_PORT` | `8000` | Port for the FastAPI server. |
| `WORKERS` | `4` | Number of Uvicorn workers. |
---

## 3. API Reference

**Base URL**: `http://localhost:8000`
**Interactive Docs**: `/docs` (Swagger UI)

### Endpoints

#### `POST /jobs/search`
Execute a live search against external providers.

**Body**:
```json
{
  "query": "Frontend Developer",
  "location": "Bern",
  "canton_codes": ["BE", "SO"],
  "workload_min": 80,
  "contract_type": "permanent",
  "language": "en"
}
```

#### `GET /jobs/search/quick`
Simplified GET search for minimal use cases.
`GET /jobs/search/quick?query=Python&location=Zurich`

---

## 4. CLI Reference

The system provides a robust CLI via `swiss-jobs`.

### Commands

| Command | Usage | Description |
|---|---|---|
| `search` | `swiss-jobs search "Query" [flags]` | Main search interface. |
| `serve` | `swiss-jobs serve --port 8000` | Start the API server. |
| `health` | `swiss-jobs health` | Check provider connectivity. |

### Search Flags

| Flag | Category | Description |
|---|---|---|
| `-l` `--location` | Filter | City, Zip, or Canton name. |
| `-c` `--canton` | Filter | Specific Canton Code (e.g. `ZH`). |
| `--workload-min` | Filter | Minimum percentage (0-100). |
| `--mode` | System | `fast` (no delay), `stealth` (fingerprinted), `aggressive` (proxied). |

---

## 5. Technical Specifications


### Stealth & Anti-Bot
The scraper is designed to mimic a legitimate user:
1.  **TLS Fingerprinting**: Uses HTTP/2 to match browser signatures.
2.  **Client Hints**: Injects `sec-ch-ua` headers corresponding to Chrome 120+.
3.  **CSRF Handling**: For `job_room` (Angular app), the scraper autonomously performs the handshake to acquire the `XSRF-TOKEN` cookie and replays it in the `X-XSRF-TOKEN` header.

### Pagination Limit Detection
The scraper detects when APIs impose limits on results:
- Tracks empty pages and repeated content
- Reports stop reasons via `pagination_stopped_early` and `stop_reason` fields
- Possible stop reasons: `max_pages_reached`, `empty_page`, `rate_limited`, `repeated_content`

