# Swiss Jobs Scraper - System Reference Manual

> **Version**: 2.0.0 (AI/Machine Optimized)
> **Target Audience**: Developers, AI Agents, System Architects
> **Purpose**: Definitive source of truth for schema, API, and internal logic.

This document describes the Swiss Jobs Scraper system. It is structured to be parsed by LLMs or developers needing exact specifications.

---

## 1. System Overview

The system is an asynchronous job aggregation platform with 4 layers:

1.  **Ingestion Layer (Providers)**: Fetches raw data from external sources (currently `job_room`).
2.  **Processing Layer (Core)**: Normalizes data, simulates browser fingerprints (Stealth), and handles IO.
3.  **Enrichment Layer (AI)**: Uses LLMs (Gemini/Groq) to translate and extract structured data (Experience, Keywords).
4.  **Persistence Layer (Storage)**: Stores data in PostgreSQL with deduplication logic.

---

## 2. Database Schema

**Table**: `jobs` (SQLAlchemy: `StoredJob`)
**Primary Key**: `id`

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `VARCHAR(255)` | NO | Unique Job UUID from provider. |
| `source_platform` | `VARCHAR(100)` | NO | Origin (e.g., `job_room`). |
| `title` | `VARCHAR(500)` | NO | Original job title. |
| `description` | `TEXT` | YES | Full HTML/Text description. |
| `job_link` | `VARCHAR(1000)` | YES | URL to job posting. |
| `external_link` | `VARCHAR(1000)` | YES | URL to application form. |
| `email` | `VARCHAR(255)` | YES | Contact email. |
| `date_added` | `TIMESTAMP` | NO | UTC timestamp of insertion. |
| `date_updated` | `TIMESTAMP` | YES | UTC timestamp of last content change. |
| `content_hash` | `VARCHAR(64)` | YES | SHA256 of `title + description + company`. |
| `raw_data` | `JSONB` | YES | Full original payload from provider. |

### AI Enrichment Columns
These fields are populated only after AI processing runs.

| Column | Type | Description |
|--------|------|-------------|
| `title_en` | `VARCHAR(500)` | English translation. |
| `title_de` | `VARCHAR(500)` | German translation. |
| `title_fr` | `VARCHAR(500)` | French translation. |
| `title_it` | `VARCHAR(500)` | Italian translation. |
| `description_en` | `TEXT` | English description. |
| `description_de` | `TEXT` | German description. |
| `description_fr` | `TEXT` | French description. |
| `description_it` | `TEXT` | Italian description. |
| `required_languages` | `ARRAY(VARCHAR)` | List of ISO codes (e.g., `['en', 'de']`). |
| `experience_level` | `VARCHAR(50)` | Enum: `entry`, `junior`, `mid`, `senior`, `lead`. |
| `years_experience_min`| `INTEGER` | Min years required. |
| `years_experience_max`| `INTEGER` | Max years required. |
| `education` | `VARCHAR(500)` | Required degree/diploma. |
| `semantic_keywords` | `ARRAY(VARCHAR)` | Generated search tags. |
| `ai_processed_at` | `TIMESTAMP` | When AI last ran. |

---

## 3. API Reference

**Base URL**: `http://localhost:8000`
**Docs**: `/docs` (Swagger UI)

### 3.1 Endpoints

#### `GET /jobs/providers`
Returns list of available providers and their capabilities.

#### `POST /jobs/search`
Main search endpoint.

**Query Parameters**:
*   `provider` (str, default=`job_room`): Data source.
*   `mode` (str, default=`stealth`): `fast`, `stealth`, `aggressive`.
*   `persist` (bool, default=`false`): Save to DB.
*   `ai_process` (bool, default=`false`): Run AI enrichment.
*   `features` (str, optional): CSV of features (e.g., `translation,keywords`).

**Request Body (JSON)**:
```json
{
  "query": "string | null",
  "location": "string | null",
  "canton_codes": ["string"],
  "workload_min": "integer (0-100)",
  "workload_max": "integer (0-100)",
  "contract_type": "permanent | temporary | any",
  "posted_within_days": "integer",
  "page": "integer (0+)",
  "page_size": "integer (1-100)",
  "language": "en | de | fr | it"
}
```

#### `GET /jobs/search/quick`
Simplified GET search.
**Params**: `query` (required), `location`, `page`.

#### `GET /jobs/{provider}/{job_id}`
Fetch single job details.
**Params**: `language` (default=`en`).

#### `POST /jobs/process`
Batch process stored jobs with AI.
**Params**: `limit` (max 1000).

#### `GET /jobs/stats`
Returns DB statistics (`total_jobs`, `unprocessed_jobs`).

---

## 4. CLI Reference

**Command**: `swiss-jobs`

### 4.1 Commands

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `search` | `[QUERY]` | see below | Search external providers. |
| `detail` | `<JOB_ID>` | `--provider`, `--format` | Get full job JSON. |
| `process` | none | `--limit` | AI-enrich existing DB records. |
| `serve` | none | `--port`, `--host` | Start API server. |
| `health` | none | `--provider` | Check external connectivity. |

### 4.2 Search Options (`swiss-jobs search`)

*   **Filters**:
    *   `--location, -l`: City/Canton/Zip.
    *   `--canton, -c`: Canton Code.
    *   `--workload-min`: Int (0-100).
    *   `--contract`: `permanent`, `temporary`.
    *   `--days`: Posted in last N days.
*   **Actions**:
    *   `--save`: Write to DB.
    *   `--ai`: Run AI.
*   **System**:
    *   `--mode`: `fast` (no delay), `stealth` (fingerprinted), `aggressive` (proxied).
    *   `--format, -f`: `table`, `json`, `csv`.

---

## 5. Technical Mechanisms

### 5.1 Location Resolution (BFS)
The API accepts city names ("Zürich") but internally converts them to **BFS Communal Codes** ("261") using a dedicated mapper (`mapper.py`).
*   **Resolution Order**: Cache -> Postal Code -> Fuzzy Search.
*   **Reverse Lookup**: Used to determine Canton from raw BFS codes.

### 5.2 Stealth Session
*   **Headers**: Simulates Chrome 120+ on Windows.
*   **Client Hints**: Sends `sec-ch-ua` headers matching the User-Agent to pass WAF checks.
*   **HTTP/2**: Enabled to match browser TLS fingerprints.
*   **CSRF**: Automatically scrapes `XSRF-TOKEN` cookie and injects `X-XSRF-TOKEN` header for POST requests to Angular backends.

### 5.3 AI Enrichment
*   **Atomic Processing**: Features are modular. If only `keywords` is requested, the system constructs a minimal prompt.
*   **Model Agnostic**: Supports `Gemini` (default) and `Groq`.
*   **Output Validation**: AI output is parsed into a Pydantic model before DB insertion.

### 5.4 Deduplication
*   **Identity**: `id` from the provider is the primary key.
*   **Change Detection**: `SHA256(title + description + company)` is compared.
    *   Mismatch -> Update `content_hash` & `date_updated`.
    *   Match -> No-op.
