# Swiss Jobs Scraper - Production Dockerfile
# ===========================================
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy dependency files
COPY pyproject.toml ./

# Export dependencies to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.12-slim as production

# Create non-root user for security
RUN groupadd -r scraper && useradd -r -g scraper scraper

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production

# Default settings
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=4
ENV LOG_LEVEL=INFO

# Switch to non-root user
USER scraper

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the API server
CMD ["sh", "-c", "uvicorn swiss_jobs_scraper.api.main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}"]

# =============================================================================
# Stage 3: Development (for local development)
# =============================================================================
FROM python:3.12-slim as development

WORKDIR /app

# Install dev dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy dependency files and install
COPY pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy source and tests
COPY src/ ./src/
COPY tests/ ./tests/

# Install in editable mode
RUN pip install -e .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=development
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose port
EXPOSE 8000

# Default command for development (with hot reload)
CMD ["uvicorn", "swiss_jobs_scraper.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
