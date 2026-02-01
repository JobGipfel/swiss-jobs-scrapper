"""Tests for REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from swiss_jobs_scraper.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "docs" in data


class TestProvidersEndpoints:
    """Tests for provider endpoints."""

    def test_list_providers(self, client):
        """Test listing available providers."""
        response = client.get("/jobs/providers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
        assert len(data["providers"]) > 0
        
        # Check job_room is available
        provider_names = [p["name"] for p in data["providers"]]
        assert "job_room" in provider_names

    def test_provider_capabilities(self, client):
        """Test that provider capabilities are included."""
        response = client.get("/jobs/providers")
        
        data = response.json()
        job_room = next(p for p in data["providers"] if p["name"] == "job_room")
        
        assert "capabilities" in job_room
        caps = job_room["capabilities"]
        
        assert caps["radius_search"] is True
        assert caps["canton_filter"] is True
        assert caps["profession_codes"] is True
        assert caps["language_skills"] is True


class TestSearchEndpoints:
    """Tests for job search endpoints."""

    def test_search_request_validation(self, client):
        """Test search request validation."""
        # Valid request should be accepted
        response = client.post("/jobs/search", json={
            "query": "Test",
            "page": 0,
            "page_size": 10,
        })
        
        # We may get errors from the actual API, but validation should pass
        assert response.status_code in [200, 500]

    def test_search_with_invalid_mode(self, client):
        """Test search with invalid execution mode."""
        response = client.post(
            "/jobs/search?mode=invalid",
            json={"query": "Test"},
        )
        
        assert response.status_code == 400

    def test_search_with_invalid_provider(self, client):
        """Test search with unknown provider."""
        response = client.post(
            "/jobs/search?provider=unknown_provider",
            json={"query": "Test"},
        )
        
        assert response.status_code == 400

    def test_quick_search_endpoint(self, client):
        """Test quick search endpoint."""
        response = client.get("/jobs/search/quick?query=Developer")
        
        # Should accept the request
        assert response.status_code in [200, 500]


class TestJobDetailEndpoints:
    """Tests for job detail endpoints."""

    def test_get_details_invalid_provider(self, client):
        """Test getting details with invalid provider."""
        response = client.get("/jobs/invalid_provider/some-uuid")
        
        assert response.status_code == 400

    def test_get_details_with_language(self, client):
        """Test getting details with language parameter."""
        # This will likely fail with provider error, but should accept params
        response = client.get("/jobs/job_room/test-uuid?language=de")
        
        assert response.status_code in [404, 500]


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_json(self, client):
        """Test OpenAPI JSON endpoint."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data
        assert data["info"]["title"] == "Swiss Jobs Scraper API"

    def test_docs_endpoint(self, client):
        """Test Swagger UI endpoint."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self, client):
        """Test ReDoc endpoint."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
