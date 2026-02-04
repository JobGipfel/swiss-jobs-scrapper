# System Reference Manual - Swiss Jobs Scraper 🇨🇭

> **Version**: 2.0.0
> **Target Audience**: Developers, System Architects, AI Agents
> **Purpose**: Definitive source of truth for schema, API, and internal logic.

This document describes the Swiss Jobs Scraper system. It is structured to be parsed by LLMs or developers requiring exact specifications.

---

## 1. System Architecture

The system follows a **4-Layer Architecture** designed for resilience and separation of concerns:

1.  **Ingestion Layer (Providers)**
    *   Fetches raw data from external sources (currently `job_room`).
    *   Handles platform-specific pagination and payload mapping.
2.  **Processing Layer (Core)**
    *   Normalizes data into a unified `Job` model.
    *   **Stealth Engine**: Simulates browser fingerprints (Chrome 120+), Client Hints, and handles complex CSRF tokens for SPA backends.
    *   **BFS Resolver**: Maps city names ("Zürich") to BFS Communal Codes ("261") for accurate Swiss geo-filtering.
3.  **Enrichment Layer (AI)**
    *   Uses LLMs (Gemini/Groq) to enrich raw data.
    *   **Atomic Features**: Translation, Experience Extraction, Keyword Generation.
4.  **Persistence Layer (Storage)**
    *   PostgreSQL with SQLAlchemy.
    *   Handles deduplication via content hashing and tracks update history.

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

### Database (Optional)
Required only if persistence is enabled.
| Variable | Description |
|---|---|
| `DATABASE_URL` | Full connection string: `postgresql+asyncpg://user:pass@host:5432/db` |

### AI Integration (Optional)
Required for enrichment features.
| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `gemini` | Provider: `gemini` or `groq`. |
| `AI_API_KEY` | - | **Required**. Your API Secret Key. |
| `AI_MODEL` | `gemini-1.5-flash` | Specific model identifier. |

---

## 3. Database Schema

**Table**: `jobs`
**ORM**: SQLAlchemy `StoredJob`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | `VARCHAR` | NO | Unique Job UUID from provider. **PK**. |
| `source_platform` | `VARCHAR` | NO | Origin (e.g., `job_room`). |
| `title` | `VARCHAR` | NO | Original job title. |
| `description` | `TEXT` | YES | Full HTML/Text description. |
| `job_link` | `VARCHAR` | YES | Direct link to posting. |
| `email` | `VARCHAR` | YES | Contact email if found. |
| `date_added` | `TIMESTAMP` | NO | UTC insertion time. |
| `date_updated` | `TIMESTAMP` | YES | UTC time of last content change. |
| `content_hash` | `VARCHAR` | YES | SHA256(`title`+`desc`+`company`) for change detection. |

### AI Enrichment Columns
Populated asynchronously after ingestion.

| Column | Type | Description |
|---|---|---|
| `title_en/de/fr/it` | `VARCHAR` | Translated titles. |
| `description_en/...` | `TEXT` | Translated descriptions. |
| `required_languages` | `ARRAY` | ISO codes (e.g., `['en', 'de']`). |
| `experience_level` | `VARCHAR` | `entry`, `junior`, `mid`, `senior`, `lead`. |
| `semantic_keywords` | `ARRAY` | Generated tags for vector search/indexing. |

---

## 4. API Reference

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

#### `POST /jobs/process`
Trigger batch AI processing for jobs already in the database.
**Params**: `limit` (max 1000).

---

## 5. CLI Reference

The system provides a robust CLI via `swiss-jobs`.

### Commands

| Command | Usage | Description |
|---|---|---|
| `search` | `swiss-jobs search "Query" [flags]` | Main search interface. |
| `serve` | `swiss-jobs serve --port 8000` | Start the API server. |
| `process`| `swiss-jobs process --limit 50` | Run AI enrichment on DB records. |
| `health` | `swiss-jobs health` | Check provider connectivity. |

### Search Flags

| Flag | Category | Description |
|---|---|---|
| `-l` `--location` | Filter | City, Zip, or Canton name. |
| `-c` `--canton` | Filter | Specific Canton Code (e.g. `ZH`). |
| `--workload-min` | Filter | Minimum percentage (0-100). |
| `--save` | Action | Persist results to database. |
| `--ai` | Action | Run AI enrichment immediately. |
| `--mode` | System | `fast` (no delay), `stealth` (fingerprinted), `aggressive` (proxied).. |

---

## 6. Technical Specifications

### Stealth & Anti-Bot
The scraper is designed to mimic a legitimate user:
1.  **TLS Fingerprinting**: Uses HTTP/2 to match browser signatures.
2.  **Client Hints**: Injects `sec-ch-ua` headers corresponding to Chrome 120+.
3.  **CSRF Handling**: For `job_room` (Angular app), the scraper autonomously performs the handshake to acquire the `XSRF-TOKEN` cookie and replays it in the `X-XSRF-TOKEN` header.

### Identity & Deduplication
Jobs are identified by the provider's native ID. However, to detect content updates without duplication:
-   A **Content Hash** (SHA256) is generated from critical fields.
-   On upsert, if the ID matches but the hash differs, `date_updated` is refreshed and content is overwritten.
-   If hash matches, the write is a no-op (idempotent).
