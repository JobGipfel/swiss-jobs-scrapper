"""
FastAPI application for Swiss Jobs Scraper.

Provides REST API endpoints for job searching and retrieval.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from swiss_jobs_scraper import __version__
from swiss_jobs_scraper.api.routes import health, jobs

# =============================================================================
# Application Lifecycle
# =============================================================================


from typing import AsyncGenerator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    # Startup
    yield
    # Shutdown (cleanup if needed)


# =============================================================================
# Application Setup
# =============================================================================


app = FastAPI(
    title="Swiss Jobs Scraper API",
    description="""
# Swiss Jobs Scraper API

A production-grade API for accessing Swiss job market data.

## Features

- **Multiple Providers**: Currently supports job-room.ch, extensible to other sources
- **Full Filter Support**: All filters including location, workload, contract type
- **Swiss-Optimized**: BFS communal code resolution, canton filtering, multilingual support
- **Flexible Execution Modes**: Fast, Stealth, or Aggressive modes for different use cases

## Quick Start

1. **Search for jobs**:
   ```
   POST /jobs/search
   {
       "query": "Software Engineer",
       "location": "Zürich",
       "workload_min": 80
   }
   ```

2. **Get job details**:
   ```
   GET /jobs/job_room/{job_id}
   ```

## Execution Modes

- `fast`: Minimal stealth, maximum speed (for testing)
- `stealth`: Full browser simulation (recommended for production)
- `aggressive`: Stealth + proxy rotation (for high volume)

## Rate Limiting

The API respects upstream rate limits. If you receive a 429 response,
wait for the specified `Retry-After` duration before retrying.
""",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# =============================================================================
# Middleware
# =============================================================================


# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Routes
# =============================================================================


app.include_router(health.router)
app.include_router(jobs.router)


# =============================================================================
# Root Endpoint
# =============================================================================


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """API root - basic information."""
    return {
        "name": "Swiss Jobs Scraper API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
