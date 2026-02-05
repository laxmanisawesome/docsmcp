"""MCP JSON-RPC server implementation."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from models import MCPRequest, MCPResponse, MCPError
from storage import (
    list_projects, project_exists, read_json, config_path,
    get_project_stats, read_document, docs_dir
)
from fts_indexer import query_fts
from config import settings


# MCP method handlers
_handlers: Dict[str, callable] = {}


def mcp_method(name: str):
    """Decorator to register MCP method handlers."""
    def decorator(func):
        _handlers[name] = func
        return func
    return decorator


async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Process an MCP JSON-RPC request."""
    
    if request.method not in _handlers:
        return MCPResponse(
            id=request.id,
            error=MCPError(
                code=-32601,
                message=f"Method not found: {request.method}"
            )
        )
    
    try:
        result = await _handlers[request.method](request.params)
        return MCPResponse(id=request.id, result=result)
    except ValueError as e:
        return MCPResponse(
            id=request.id,
            error=MCPError(code=-32602, message=str(e))
        )
    except FileNotFoundError as e:
        return MCPResponse(
            id=request.id,
            error=MCPError(code=-32000, message=str(e))
        )
    except Exception as e:
        return MCPResponse(
            id=request.id,
            error=MCPError(code=-32603, message=str(e))
        )


@mcp_method("list_projects")
async def list_projects_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all indexed documentation projects."""
    
    projects = []
    for project_id in list_projects():
        config = read_json(config_path(project_id))
        stats = get_project_stats(project_id)
        
        projects.append({
            "id": project_id,
            "name": config.get("name", project_id),
            "base_url": config.get("baseUrl", ""),
            "page_count": stats["page_count"],
            "last_updated": config.get("updatedAt"),
        })
    
    return {"projects": projects}


@mcp_method("search_docs")
async def search_docs_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search documentation across all or specific projects."""
    
    query = params.get("query")
    if not query:
        raise ValueError("'query' parameter is required")
    
    project_id = params.get("project")
    limit = min(params.get("limit", 10), 100)
    
    start_time = time.time()
    
    # Determine which projects to search
    if project_id:
        if not project_exists(project_id):
            raise FileNotFoundError(f"Project '{project_id}' not found")
        project_ids = [project_id]
    else:
        project_ids = list_projects()
    
    # Search each project
    all_results = []
    
    for pid in project_ids:
        try:
            # Try vector search first if enabled
            if settings.enable_vector_index:
                try:
                    from indexer import query_vectors
                    results = query_vectors(pid, query, limit)
                    if results:
                        for r in results:
                            r["project"] = pid
                            # Get URL from document if not in result
                            if not r.get("url"):
                                doc = read_document(pid, r["path"])
                                if doc:
                                    r["url"] = doc.get("url", "")
                        all_results.extend(results)
                        continue
                except ImportError:
                    pass
            
            # Fallback to FTS
            results = query_fts(pid, query, limit)
            for r in results:
                r["project"] = pid
                # Get URL from document if not in result
                if not r.get("url"):
                    doc = read_document(pid, r["path"])
                    if doc:
                        r["url"] = doc.get("url", "")
            all_results.extend(results)
            
        except Exception:
            continue
    
    # Sort by score and limit
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    all_results = all_results[:limit]
    
    query_time_ms = int((time.time() - start_time) * 1000)
    
    return {
        "results": all_results,
        "total": len(all_results),
        "query_time_ms": query_time_ms,
    }


@mcp_method("get_document")
async def get_document_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve full content of a specific document."""
    
    project_id = params.get("project")
    path = params.get("path")
    
    if not project_id:
        raise ValueError("'project' parameter is required")
    if not path:
        raise ValueError("'path' parameter is required")
    
    if not project_exists(project_id):
        raise FileNotFoundError(f"Project '{project_id}' not found")
    
    doc = read_document(project_id, path)
    if not doc:
        raise FileNotFoundError(f"Document '{path}' not found in project '{project_id}'")
    
    return {
        "title": doc["title"],
        "url": doc["url"],
        "content": doc["content"],
        "metadata": doc["metadata"],
    }


# MCP capability discovery
MCP_CAPABILITIES = {
    "methods": [
        {
            "name": "list_projects",
            "description": "List all indexed documentation projects",
            "parameters": {},
        },
        {
            "name": "search_docs",
            "description": "Search documentation across all or specific projects",
            "parameters": {
                "query": {"type": "string", "required": True, "description": "Search query"},
                "project": {"type": "string", "required": False, "description": "Project ID to search"},
                "limit": {"type": "integer", "required": False, "description": "Max results (default: 10)"},
            },
        },
        {
            "name": "get_document",
            "description": "Retrieve full content of a specific document",
            "parameters": {
                "project": {"type": "string", "required": True, "description": "Project ID"},
                "path": {"type": "string", "required": True, "description": "Document path"},
            },
        },
    ],
}
