"""Tests for REST API endpoints."""

import pytest
from fastapi.testclient import TestClient


# Note: Import will fail until main.py is properly set up
# from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    from src.main import app
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_projects_empty(client):
    """Test listing projects when empty."""
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_project(client, sample_project_config):
    """Test creating a new project."""
    response = client.post("/api/projects", json=sample_project_config)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == sample_project_config["name"]


def test_search_endpoint(client):
    """Test search endpoint."""
    response = client.post("/api/search", json={"query": "test"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


def test_mcp_endpoint_list_tools(client):
    """Test MCP endpoint with list tools request."""
    response = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    })
    assert response.status_code == 200
    data = response.json()
    assert "result" in data or "error" in data
