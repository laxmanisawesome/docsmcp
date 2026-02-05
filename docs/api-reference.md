# API Reference

Complete reference for DocsMCP REST API and MCP methods.

---

## Authentication

All API requests require authentication via Bearer token:

```
Authorization: Bearer your-api-token
```

---

## REST API

Base URL: `http://localhost:8090/api`

### Health Check

Check server status.

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

### Projects

#### List Projects

```
GET /api/projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": "react",
      "base_url": "https://react.dev",
      "page_count": 150,
      "status": "ready",
      "last_scraped": "2026-02-05T10:30:00Z",
      "created_at": "2026-02-01T08:00:00Z"
    }
  ],
  "total": 1
}
```

#### Get Project

```
GET /api/projects/{project_id}
```

**Response:**
```json
{
  "id": "react",
  "base_url": "https://react.dev",
  "config": {
    "max_depth": 5,
    "max_pages": 1000,
    "include_patterns": ["/reference/*"],
    "exclude_patterns": ["/blog/*"]
  },
  "stats": {
    "page_count": 150,
    "total_words": 250000,
    "index_size_bytes": 5242880
  },
  "status": "ready",
  "last_scraped": "2026-02-05T10:30:00Z",
  "scrape_duration_seconds": 300,
  "created_at": "2026-02-01T08:00:00Z"
}
```

#### Create Project

```
POST /api/projects
Content-Type: application/json
```

**Request:**
```json
{
  "id": "react",
  "base_url": "https://react.dev/reference",
  "config": {
    "max_depth": 3,
    "max_pages": 500,
    "include_patterns": ["/reference/*"],
    "exclude_patterns": ["/blog/*"]
  }
}
```

**Response:**
```json
{
  "id": "react",
  "base_url": "https://react.dev/reference",
  "status": "created",
  "message": "Project created. Run POST /api/projects/react/scrape to start scraping."
}
```

#### Update Project

```
PATCH /api/projects/{project_id}
Content-Type: application/json
```

**Request:**
```json
{
  "config": {
    "max_pages": 1000
  }
}
```

**Response:**
```json
{
  "id": "react",
  "status": "updated",
  "config": { ... }
}
```

#### Delete Project

```
DELETE /api/projects/{project_id}
```

**Response:**
```json
{
  "id": "react",
  "status": "deleted",
  "message": "Project and all associated data deleted."
}
```

---

### Scraping

#### Start Scrape

```
POST /api/projects/{project_id}/scrape
```

**Request (optional):**
```json
{
  "full_rescrape": true
}
```

**Response:**
```json
{
  "id": "react",
  "status": "scraping",
  "message": "Scrape started. Check status at GET /api/projects/react/status"
}
```

#### Get Scrape Status

```
GET /api/projects/{project_id}/status
```

**Response (in progress):**
```json
{
  "id": "react",
  "status": "scraping",
  "progress": {
    "pages_scraped": 45,
    "pages_queued": 120,
    "errors": 2,
    "started_at": "2026-02-05T10:00:00Z",
    "elapsed_seconds": 120
  }
}
```

**Response (complete):**
```json
{
  "id": "react",
  "status": "ready",
  "last_scrape": {
    "pages_scraped": 150,
    "errors": 3,
    "started_at": "2026-02-05T10:00:00Z",
    "completed_at": "2026-02-05T10:05:00Z",
    "duration_seconds": 300
  }
}
```

#### Cancel Scrape

```
POST /api/projects/{project_id}/cancel
```

**Response:**
```json
{
  "id": "react",
  "status": "cancelled",
  "message": "Scrape cancelled. Partial data retained."
}
```

---

### Search

#### Search All Projects

```
POST /api/search
Content-Type: application/json
```

**Request:**
```json
{
  "query": "useState hook",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "project": "react",
      "title": "useState",
      "url": "https://react.dev/reference/react/useState",
      "snippet": "useState is a React Hook that lets you add a state variable to your component...",
      "score": 0.95
    }
  ],
  "total": 1,
  "query_time_ms": 12
}
```

#### Search Specific Project

```
POST /api/projects/{project_id}/search
Content-Type: application/json
```

**Request:**
```json
{
  "query": "useEffect cleanup",
  "limit": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "useEffect",
      "url": "https://react.dev/reference/react/useEffect",
      "snippet": "Return a cleanup function from your Effect...",
      "score": 0.89
    }
  ],
  "total": 1,
  "query_time_ms": 8
}
```

---

### Documents

#### List Documents

```
GET /api/projects/{project_id}/documents
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 50, max: 100)

**Response:**
```json
{
  "documents": [
    {
      "path": "reference-react-useState.md",
      "title": "useState",
      "url": "https://react.dev/reference/react/useState",
      "word_count": 1500,
      "scraped_at": "2026-02-05T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "pages": 3
}
```

#### Get Document

```
GET /api/projects/{project_id}/documents/{document_path}
```

**Response:**
```json
{
  "path": "reference-react-useState.md",
  "title": "useState",
  "url": "https://react.dev/reference/react/useState",
  "content": "# useState\n\n`useState` is a React Hook...",
  "metadata": {
    "word_count": 1500,
    "scraped_at": "2026-02-05T10:30:00Z"
  }
}
```

---

## MCP Protocol

Endpoint: `POST /mcp`

All MCP methods use JSON-RPC 2.0 format.

### list_projects

List all indexed documentation projects.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "list_projects",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "projects": [
      {
        "id": "react",
        "name": "React Documentation",
        "base_url": "https://react.dev",
        "page_count": 150,
        "last_updated": "2026-02-05T10:30:00Z"
      }
    ]
  },
  "id": 1
}
```

### search_docs

Search documentation.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "search_docs",
  "params": {
    "query": "useState hook",
    "project": "react",
    "limit": 5
  },
  "id": 2
}
```

**Parameters:**
- `query` (string, required): Search query
- `project` (string, optional): Limit to specific project
- `limit` (int, optional): Max results (default: 10)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "results": [
      {
        "title": "useState",
        "url": "https://react.dev/reference/react/useState",
        "snippet": "useState is a React Hook that lets you add a state variable...",
        "score": 0.95,
        "project": "react"
      }
    ],
    "total": 1,
    "query_time_ms": 12
  },
  "id": 2
}
```

### get_document

Retrieve full document content.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_document",
  "params": {
    "project": "react",
    "path": "reference-react-useState.md"
  },
  "id": 3
}
```

**Parameters:**
- `project` (string, required): Project ID
- `path` (string, required): Document path (from search results)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "title": "useState",
    "url": "https://react.dev/reference/react/useState",
    "content": "# useState\n\n`useState` is a React Hook that lets you add a state variable to your component.\n\n## Reference\n\n...",
    "metadata": {
      "scraped_at": "2026-02-05T10:30:00Z",
      "word_count": 1500
    }
  },
  "id": 3
}
```

### Error Responses

**Invalid method:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found"
  },
  "id": 1
}
```

**Invalid params:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params: 'query' is required"
  },
  "id": 1
}
```

**Project not found:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Project 'unknown' not found"
  },
  "id": 1
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Not Found |
| 409 | Conflict (e.g., project already exists) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

### MCP Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error |
| -32600 | Invalid Request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32000 | Application error (see message) |

---

## Rate Limiting

Default: 100 requests/minute per IP

Headers returned:
- `X-RateLimit-Limit`: Max requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Seconds until reset

When rate limited, returns `429 Too Many Requests`:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 30
}
```

---

## Webhooks

Configure `WEBHOOK_URL` in `.env` to receive events:

### scrape_complete

```json
{
  "event": "scrape_complete",
  "project_id": "react",
  "status": "success",
  "pages_scraped": 150,
  "errors": 3,
  "duration_seconds": 300,
  "timestamp": "2026-02-05T10:30:00Z"
}
```

### scrape_error

```json
{
  "event": "scrape_error",
  "project_id": "react",
  "status": "failed",
  "error": "Connection timeout",
  "pages_scraped": 45,
  "timestamp": "2026-02-05T10:15:00Z"
}
```

---

## Next Steps

- [Configuration Guide](configuration.md) — All settings
- [MCP Setup](mcp-setup.md) — Connect to Claude Desktop
- [Architecture](architecture.md) — System design
