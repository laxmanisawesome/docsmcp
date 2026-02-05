"""Pydantic models for API request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Project Models ---

class ProjectConfig(BaseModel):
    """Project-specific configuration."""
    max_depth: int = Field(default=5, ge=1, le=20)
    max_pages: int = Field(default=1000, ge=1, le=100000)
    include_patterns: List[str] = Field(default_factory=list)
    exclude_patterns: List[str] = Field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression
    custom_selectors: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    rate_limit_delay: Optional[float] = None


class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    base_url: str = Field(..., min_length=10)
    config: Optional[ProjectConfig] = None


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    config: Optional[ProjectConfig] = None


class ProjectStats(BaseModel):
    """Project statistics."""
    page_count: int = 0
    total_words: int = 0
    index_size_bytes: int = 0


class ScrapeProgress(BaseModel):
    """Scrape progress information."""
    pages_scraped: int = 0
    pages_queued: int = 0
    errors: int = 0
    started_at: Optional[datetime] = None
    elapsed_seconds: int = 0


class LastScrape(BaseModel):
    """Information about the last completed scrape."""
    pages_scraped: int = 0
    errors: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0


class Project(BaseModel):
    """Full project model."""
    id: str
    base_url: str
    config: ProjectConfig = Field(default_factory=ProjectConfig)
    stats: ProjectStats = Field(default_factory=ProjectStats)
    status: str = "created"  # created, scraping, ready, error
    last_scraped: Optional[datetime] = None
    scrape_duration_seconds: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_error: Optional[str] = None


class ProjectListResponse(BaseModel):
    """Response for listing projects."""
    projects: List[Project]
    total: int


class ProjectResponse(BaseModel):
    """Response for a single project."""
    id: str
    base_url: str
    status: str
    message: Optional[str] = None
    config: Optional[ProjectConfig] = None


# --- Search Models ---

class SearchRequest(BaseModel):
    """Request model for search."""
    query: str = Field(..., min_length=1)
    project: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    """Single search result."""
    project: str
    title: str
    url: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    """Response for search."""
    results: List[SearchResult]
    total: int
    query_time_ms: int


# --- Document Models ---

class DocumentMeta(BaseModel):
    """Document metadata."""
    path: str
    title: str
    url: str
    word_count: int
    scraped_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: List[DocumentMeta]
    total: int
    page: int
    limit: int
    pages: int


class Document(BaseModel):
    """Full document with content."""
    path: str
    title: str
    url: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- MCP Models ---

class MCPRequest(BaseModel):
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: int | str | None = None


class MCPError(BaseModel):
    """JSON-RPC 2.0 error."""
    code: int
    message: str
    data: Optional[Any] = None


class MCPResponse(BaseModel):
    """JSON-RPC 2.0 response."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[MCPError] = None
    id: int | str | None = None


# --- Health & Status ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: Optional[int] = None


class ScrapeStatusResponse(BaseModel):
    """Scrape status response."""
    id: str
    status: str
    progress: Optional[ScrapeProgress] = None
    last_scrape: Optional[LastScrape] = None


# --- Webhook Payloads ---

class WebhookPayload(BaseModel):
    """Webhook event payload."""
    event: str  # scrape_complete, scrape_error
    project_id: str
    status: str
    pages_scraped: int = 0
    errors: int = 0
    duration_seconds: int = 0
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
