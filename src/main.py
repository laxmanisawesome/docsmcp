"""DocsMCP - Main FastAPI application.

Provides REST API, MCP endpoint, and Web UI for documentation management.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from models import (
    ProjectCreate, ProjectUpdate, ProjectListResponse, ProjectResponse,
    SearchRequest, SearchResponse, SearchResult,
    DocumentListResponse, Document,
    MCPRequest, MCPResponse,
    HealthResponse, ScrapeStatusResponse,
)
from storage import (
    list_projects, project_exists, read_json, write_json,
    config_path, docs_dir, delete_project, get_project_stats,
    list_documents, read_document,
)
from scraper import scrape_project
from fts_indexer import query_fts, build_fts_index, get_fts_stats
from mcp_server import handle_mcp_request, MCP_CAPABILITIES


# --- Application Setup ---

app = FastAPI(
    title="DocsMCP",
    description="Self-hosted documentation search with MCP support",
    version="1.0.0",
)

# CORS
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates and static files
TEMPLATES_DIR = Path(__file__).parent / "web" / "templates"
STATIC_DIR = Path(__file__).parent / "web" / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR)) if TEMPLATES_DIR.exists() else None

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Rate limiting
rate_limit_buckets: Dict[str, Dict[str, Any]] = defaultdict(
    lambda: {"tokens": settings.rate_limit_requests, "last_refill": time.time()}
)

# Scrape semaphore
SCRAPE_SEMAPHORE = asyncio.Semaphore(settings.max_concurrent_scrapes)

# Metrics
metrics = {
    "scrapes_started": 0,
    "scrapes_completed": 0,
    "scrapes_failed": 0,
    "requests_total": 0,
    "requests_rate_limited": 0,
    "start_time": time.time(),
}


# --- Authentication ---

async def verify_token(request: Request) -> None:
    """Verify API token if authentication is enabled."""
    if not settings.enable_auth:
        return
    
    if not settings.api_token:
        return
    
    # Check multiple header formats
    token = (
        request.headers.get("Authorization", "").replace("Bearer ", "") or
        request.headers.get("x-api-key") or
        request.query_params.get("token")
    )
    
    if token != settings.api_token:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


# --- Middleware ---

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to requests."""
    metrics["requests_total"] += 1
    
    # Skip rate limit for health endpoints
    if request.url.path in ["/health", "/healthz", "/readyz", "/metrics"]:
        return await call_next(request)
    
    if settings.rate_limit_requests <= 0:
        return await call_next(request)
    
    # Get identifier
    identifier = (
        request.headers.get("x-api-key") or
        request.headers.get("Authorization", "").replace("Bearer ", "") or
        (request.client.host if request.client else "unknown")
    )
    
    bucket = rate_limit_buckets[identifier]
    now = time.time()
    
    # Refill tokens
    elapsed = now - bucket["last_refill"]
    refill = (elapsed / settings.rate_limit_window) * settings.rate_limit_requests
    bucket["tokens"] = min(settings.rate_limit_requests, bucket["tokens"] + refill)
    bucket["last_refill"] = now
    
    if bucket["tokens"] < 1:
        metrics["requests_rate_limited"] += 1
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "retry_after": settings.rate_limit_window},
            headers={
                "X-RateLimit-Limit": str(settings.rate_limit_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(settings.rate_limit_window)),
            }
        )
    
    bucket["tokens"] -= 1
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(int(bucket["tokens"]))
    
    return response


# --- Health Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - metrics["start_time"]),
    }


@app.get("/healthz")
async def healthz():
    """Kubernetes liveness probe."""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    """Kubernetes readiness probe."""
    try:
        projects_dir = settings.projects_dir
        if not projects_dir.exists():
            projects_dir.mkdir(parents=True, exist_ok=True)
        return {"status": "ready", "projects": len(list_projects())}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})


@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Prometheus-compatible metrics."""
    lines = [
        "# HELP docsmcp_scrapes_total Total scrapes",
        "# TYPE docsmcp_scrapes_total counter",
        f'docsmcp_scrapes_total{{status="started"}} {metrics["scrapes_started"]}',
        f'docsmcp_scrapes_total{{status="completed"}} {metrics["scrapes_completed"]}',
        f'docsmcp_scrapes_total{{status="failed"}} {metrics["scrapes_failed"]}',
        "",
        "# HELP docsmcp_requests_total Total HTTP requests",
        "# TYPE docsmcp_requests_total counter",
        f'docsmcp_requests_total{{status="ok"}} {metrics["requests_total"] - metrics["requests_rate_limited"]}',
        f'docsmcp_requests_total{{status="rate_limited"}} {metrics["requests_rate_limited"]}',
        "",
        "# HELP docsmcp_projects_total Total projects",
        "# TYPE docsmcp_projects_total gauge",
        f"docsmcp_projects_total {len(list_projects())}",
    ]
    return "\n".join(lines)


# --- Project Endpoints ---

@app.get("/api/projects", response_model=ProjectListResponse, dependencies=[Depends(verify_token)])
async def get_projects():
    """List all projects."""
    projects = []
    for project_id in list_projects():
        config = read_json(config_path(project_id))
        stats = get_project_stats(project_id)
        projects.append({
            "id": project_id,
            "base_url": config.get("baseUrl", ""),
            "page_count": stats["page_count"],
            "status": config.get("status", "unknown"),
            "last_scraped": config.get("completedAt"),
            "created_at": config.get("createdAt"),
        })
    return {"projects": projects, "total": len(projects)}


@app.get("/api/projects/{project_id}", dependencies=[Depends(verify_token)])
async def get_project(project_id: str):
    """Get project details."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    config = read_json(config_path(project_id))
    stats = get_project_stats(project_id)
    fts_stats = get_fts_stats(project_id)
    
    return {
        "id": project_id,
        "base_url": config.get("baseUrl", ""),
        "config": config.get("config", {}),
        "stats": {**stats, "fts": fts_stats},
        "status": config.get("status", "unknown"),
        "last_scraped": config.get("completedAt"),
        "last_error": config.get("lastError"),
        "created_at": config.get("createdAt"),
    }


@app.post("/api/projects", response_model=ProjectResponse, dependencies=[Depends(verify_token)])
async def create_project(data: ProjectCreate):
    """Create a new project."""
    if project_exists(data.id):
        raise HTTPException(status_code=409, detail=f"Project '{data.id}' already exists")
    
    config = {
        "id": data.id,
        "baseUrl": data.base_url,
        "config": data.config.model_dump() if data.config else {},
        "status": "created",
        "createdAt": datetime.utcnow().isoformat(),
    }
    write_json(config_path(data.id), config)
    
    return {
        "id": data.id,
        "base_url": data.base_url,
        "status": "created",
        "message": f"Project created. POST /api/projects/{data.id}/scrape to start scraping.",
    }


@app.patch("/api/projects/{project_id}", dependencies=[Depends(verify_token)])
async def update_project(project_id: str, data: ProjectUpdate):
    """Update project configuration."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    config = read_json(config_path(project_id))
    if data.config:
        config["config"] = {**config.get("config", {}), **data.config.model_dump(exclude_unset=True)}
    config["updatedAt"] = datetime.utcnow().isoformat()
    write_json(config_path(project_id), config)
    
    return {"id": project_id, "status": "updated", "config": config.get("config")}


@app.delete("/api/projects/{project_id}", dependencies=[Depends(verify_token)])
async def remove_project(project_id: str):
    """Delete a project and all its data."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    delete_project(project_id)
    return {"id": project_id, "status": "deleted", "message": "Project and all data deleted."}


# --- Scrape Endpoints ---

@app.post("/api/projects/{project_id}/scrape", dependencies=[Depends(verify_token)])
async def start_scrape(project_id: str, background_tasks: BackgroundTasks, full_rescrape: bool = False):
    """Start scraping a project."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    config = read_json(config_path(project_id))
    if config.get("status") == "scraping":
        raise HTTPException(status_code=409, detail="Scrape already in progress")
    
    async def do_scrape():
        async with SCRAPE_SEMAPHORE:
            metrics["scrapes_started"] += 1
            try:
                cfg = config.get("config", {})
                await scrape_project(
                    project_id,
                    config["baseUrl"],
                    max_depth=cfg.get("max_depth", settings.max_depth),
                    max_pages=cfg.get("max_pages", settings.max_pages_per_project),
                    include=cfg.get("include_patterns", [None])[0] if cfg.get("include_patterns") else None,
                    exclude=cfg.get("exclude_patterns", [None])[0] if cfg.get("exclude_patterns") else None,
                    clear_existing=full_rescrape,
                )
                metrics["scrapes_completed"] += 1
            except Exception:
                metrics["scrapes_failed"] += 1
    
    background_tasks.add_task(do_scrape)
    
    return {
        "id": project_id,
        "status": "scraping",
        "message": f"Scrape started. GET /api/projects/{project_id}/status for progress.",
    }


@app.get("/api/projects/{project_id}/status", dependencies=[Depends(verify_token)])
async def get_scrape_status(project_id: str):
    """Get scrape status for a project."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    config = read_json(config_path(project_id))
    return {
        "id": project_id,
        "status": config.get("status", "unknown"),
        "progress": config.get("stats"),
        "last_error": config.get("lastError"),
    }


@app.post("/api/projects/{project_id}/cancel", dependencies=[Depends(verify_token)])
async def cancel_scrape(project_id: str):
    """Cancel an in-progress scrape."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    config = read_json(config_path(project_id))
    if config.get("status") != "scraping":
        raise HTTPException(status_code=409, detail="No scrape in progress")
    
    config["status"] = "cancelled"
    config["updatedAt"] = datetime.utcnow().isoformat()
    write_json(config_path(project_id), config)
    
    return {"id": project_id, "status": "cancelled"}


# --- Search Endpoints ---

@app.post("/api/search", response_model=SearchResponse, dependencies=[Depends(verify_token)])
async def search_all(data: SearchRequest):
    """Search across all projects."""
    return await _do_search(data.query, data.limit, None)


@app.post("/api/projects/{project_id}/search", response_model=SearchResponse, dependencies=[Depends(verify_token)])
async def search_project(project_id: str, data: SearchRequest):
    """Search within a specific project."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return await _do_search(data.query, data.limit, project_id)


async def _do_search(query: str, limit: int, project_id: Optional[str]) -> Dict[str, Any]:
    """Internal search implementation."""
    start_time = time.time()
    
    project_ids = [project_id] if project_id else list_projects()
    all_results = []
    
    for pid in project_ids:
        try:
            # Try vector search if enabled
            if settings.enable_vector_index:
                try:
                    from indexer import query_vectors
                    results = query_vectors(pid, query, limit)
                    if results:
                        for r in results:
                            config = read_json(config_path(pid))
                            r["project"] = pid
                            if not r.get("url"):
                                doc = read_document(pid, r["path"])
                                if doc:
                                    r["url"] = doc.get("url", "")
                        all_results.extend(results)
                        continue
                except ImportError:
                    pass
            
            # FTS fallback
            results = query_fts(pid, query, limit)
            for r in results:
                r["project"] = pid
                if not r.get("url"):
                    doc = read_document(pid, r["path"])
                    if doc:
                        r["url"] = doc.get("url", "")
            all_results.extend(results)
        except Exception:
            continue
    
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    all_results = all_results[:limit]
    
    return {
        "results": all_results,
        "total": len(all_results),
        "query_time_ms": int((time.time() - start_time) * 1000),
    }


# --- Document Endpoints ---

@app.get("/api/projects/{project_id}/documents", dependencies=[Depends(verify_token)])
async def get_documents(project_id: str, page: int = 1, limit: int = 50):
    """List documents in a project."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return list_documents(project_id, page, min(limit, 100))


@app.get("/api/projects/{project_id}/documents/{doc_path:path}", dependencies=[Depends(verify_token)])
async def get_document(project_id: str, doc_path: str):
    """Get a specific document."""
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    doc = read_document(project_id, doc_path)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_path}' not found")
    
    return doc


# --- MCP Endpoint ---

@app.post("/mcp", dependencies=[Depends(verify_token)])
async def mcp_endpoint(request: MCPRequest):
    """MCP JSON-RPC endpoint."""
    response = await handle_mcp_request(request)
    return response.model_dump(exclude_none=True)


@app.get("/mcp/capabilities")
async def mcp_capabilities():
    """Get MCP capabilities."""
    return MCP_CAPABILITIES


# --- Web UI ---

@app.get("/", response_class=HTMLResponse)
async def web_ui(request: Request):
    """Serve the web dashboard."""
    if not templates:
        return HTMLResponse(
            "<html><body><h1>DocsMCP</h1><p>Web UI not available. "
            "Use the <a href='/docs'>API</a> directly.</p></body></html>"
        )
    
    projects = []
    for project_id in list_projects():
        config = read_json(config_path(project_id))
        stats = get_project_stats(project_id)
        projects.append({
            "id": project_id,
            "base_url": config.get("baseUrl", ""),
            "page_count": stats["page_count"],
            "status": config.get("status", "unknown"),
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": projects,
        "settings": {
            "enable_auth": settings.enable_auth,
            "enable_vector": settings.enable_vector_index,
        },
    })


# --- Main ---

def main():
    """Run the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DocsMCP Server")
    parser.add_argument("--host", default=settings.host, help="Host to bind")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--validate-config", action="store_true", help="Validate configuration and exit")
    
    args = parser.parse_args()
    
    if args.validate_config:
        errors = settings.validate()
        if errors:
            print("Configuration errors:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        print("Configuration valid.")
        sys.exit(0)
    
    print(f"Starting DocsMCP server on {args.host}:{args.port}")
    print(f"Data directory: {settings.data_dir}")
    print(f"Auth enabled: {settings.enable_auth}")
    print(f"Vector search: {settings.enable_vector_index}")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
