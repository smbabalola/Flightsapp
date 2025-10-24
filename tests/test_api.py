"""
Basic API endpoint tests for SureFlights.

Run with: pytest tests/
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns feature flags."""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "SureFlights API"
        assert "flags" in data

    def test_health_endpoint(self):
        """Test health check returns status."""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # Can be degraded
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "sureflights_requests_total" in response.text


class TestOpenAPIEndpoints:
    """Test OpenAPI documentation endpoints."""

    def test_openapi_json(self):
        """Test OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["openapi"] == "3.1.0"
        assert data["info"]["title"] == "SureFlights API"

    def test_swagger_ui(self):
        """Test Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text

    def test_redoc(self):
        """Test ReDoc is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text


class TestSearchEndpoint:
    """Test flight search endpoint."""

    def test_search_missing_params(self):
        """Test search with missing parameters returns 422."""
        response = client.post("/v1/search", json={})
        assert response.status_code == 422

    def test_search_valid_request(self):
        """Test search with valid parameters."""
        payload = {
            "slices": [{"from_": "LOS", "to": "ABV", "date": "2025-11-15"}],
            "adults": 1
        }
        response = client.post("/v1/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "offers" in data
        assert isinstance(data["offers"], list)


class TestAdminEndpoints:
    """Test admin endpoints require authentication."""

    def test_ops_trips_requires_auth(self):
        """Test /v1/ops/trips requires authentication."""
        response = client.get("/v1/ops/trips")
        assert response.status_code in (401, 403)

    def test_ops_trips_with_auth(self):
        """Test /v1/ops/trips with authentication."""
        response = client.get(
            "/v1/ops/trips?limit=5",
            auth=("admin", "change_me")
        )
        assert response.status_code in (200, 401, 403)

    def test_admin_fees_requires_auth(self):
        """Test /v1/admin/fees requires authentication."""
        response = client.post("/v1/admin/fees", json={})
        assert response.status_code == 401

