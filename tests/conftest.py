"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_documents() -> list[dict]:
    """Sample documents for testing."""
    return [
        {
            "id": "doc1",
            "title": "Getting Started with FastAPI",
            "content": "FastAPI is a modern, fast web framework for building APIs with Python.",
            "url": "https://example.com/docs/getting-started",
        },
        {
            "id": "doc2",
            "title": "Authentication Guide",
            "content": "Learn how to implement OAuth2 and JWT authentication in your API.",
            "url": "https://example.com/docs/auth",
        },
        {
            "id": "doc3",
            "title": "Database Integration",
            "content": "Connect your FastAPI application to PostgreSQL or SQLite databases.",
            "url": "https://example.com/docs/database",
        },
    ]


@pytest.fixture
def sample_project_config() -> dict:
    """Sample project configuration."""
    return {
        "name": "test-project",
        "base_url": "https://docs.example.com",
        "max_pages": 10,
        "allowed_patterns": ["/docs/*"],
        "excluded_patterns": ["/api/*"],
    }
