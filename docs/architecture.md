# Architecture

Technical overview of DocsMCP's design and data flow.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DocsMCP Server                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Web UI  │    │ REST API │    │   MCP    │    │   CLI    │ │
│  │ (Jinja2) │    │(FastAPI) │    │(JSON-RPC)│    │ (Click)  │ │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘ │
│       │               │               │               │        │
│       └───────────────┴───────┬───────┴───────────────┘        │
│                               │                                 │
│                        ┌──────▼──────┐                         │
│                        │   Core API   │                         │
│                        │  (services)  │                         │
│                        └──────┬──────┘                         │
│                               │                                 │
│       ┌───────────────────────┼───────────────────────┐        │
│       │                       │                       │        │
│  ┌────▼────┐            ┌─────▼─────┐           ┌────▼────┐   │
│  │ Scraper │            │  Indexer  │           │ Storage │   │
│  │ (httpx) │            │(FTS/FAISS)│           │ (files) │   │
│  └────┬────┘            └─────┬─────┘           └────┬────┘   │
│       │                       │                       │        │
└───────┴───────────────────────┴───────────────────────┴────────┘
                                │
                    ┌───────────▼───────────┐
                    │     File System       │
                    │    data/projects/     │
                    │   └── {project_id}/   │
                    │       ├── config.json │
                    │       ├── index.json  │
                    │       ├── fts.db      │
                    │       └── docs/*.md   │
                    └───────────────────────┘
```

---

## Components

### Web UI (`src/web/`)

Minimal, responsive dashboard built with:
- **Jinja2** templates (server-side rendering)
- **Vanilla CSS** (no frameworks, black & white design)
- **HTMX** for dynamic updates without JavaScript frameworks

Features:
- Project management (add, delete, rescrape)
- Search interface
- Configuration viewer
- MCP config generator

### REST API (`src/main.py`)

FastAPI-based HTTP API providing:
- Project CRUD operations
- Scrape triggering
- Search endpoints
- Health checks
- Static file serving

### MCP Server (`src/mcp_server.py`)

JSON-RPC 2.0 implementation of Model Context Protocol:
- `list_projects` — Enumerate available docs
- `search_docs` — Query documentation
- `get_document` — Retrieve full content

Supports two transports:
- **HTTP** — Via `/mcp` endpoint
- **STDIO** — Via `mcp_stdio.py` for direct spawning

### CLI (`src/cli.py`)

Command-line interface using Click:
- `docsmcp add <id> <url>` — Add project
- `docsmcp scrape <id>` — Trigger scrape
- `docsmcp search <id> <query>` — Search
- `docsmcp list` — List projects
- `docsmcp delete <id>` — Remove project
- `docsmcp export <id> <path>` — Export data

### Scraper (`src/scraper.py`)

Async web crawler with:
- **httpx** for HTTP requests
- **trafilatura** for content extraction
- **markdownify** for HTML → Markdown
- **BeautifulSoup** fallback parsing

Features:
- Respect robots.txt (configurable)
- Rate limiting with backoff
- URL filtering (include/exclude patterns)
- Depth limiting
- Custom CSS selectors

### Indexer (`src/fts_indexer.py`, `src/indexer.py`)

Two search backends:

**FTS (Default):**
- SQLite FTS5 full-text search
- Zero dependencies
- <10ms query time
- Keyword-based matching

**Vector (Optional):**
- sentence-transformers embeddings
- FAISS vector index
- Semantic search
- Requires +300MB dependencies

### Storage (`src/storage.py`)

File-based storage:
- Markdown files with YAML frontmatter
- JSON metadata files
- SQLite databases (FTS)
- FAISS indexes (optional)

---

## Data Flow

### Scraping Flow

```
1. User triggers scrape (UI/API/CLI)
           │
           ▼
2. Load project config
           │
           ▼
3. Fetch robots.txt (if enabled)
           │
           ▼
4. BFS crawl from base_url
           │
   ┌───────┴───────┐
   │               │
   ▼               ▼
5a. Fetch page   5b. Queue discovered URLs
           │
           ▼
6. Extract content (trafilatura)
           │
           ▼
7. Convert to Markdown
           │
           ▼
8. Add YAML frontmatter
           │
           ▼
9. Save to docs/{slug}.md
           │
           ▼
10. Update index.json
           │
           ▼
11. Build FTS index
           │
           ▼
12. (Optional) Build vector index
           │
           ▼
13. Webhook notification (if configured)
```

### Search Flow

```
1. Query arrives (MCP/REST)
           │
           ▼
2. Parse query & options
           │
           ▼
3. Select search backend
           │
   ┌───────┴───────┐
   │               │
   ▼               ▼
4a. FTS Query    4b. Vector Query
   (SQLite)      (FAISS + embeddings)
           │
           └───────┬───────┘
                   │
                   ▼
5. Rank & deduplicate results
           │
           ▼
6. Load snippets from Markdown
           │
           ▼
7. Return formatted response
```

---

## File Structure

### Project Directory

```
data/projects/{project_id}/
├── config.json      # Project configuration
├── index.json       # Document index
├── fts.db           # SQLite FTS database
├── vectors.index    # FAISS index (optional)
├── vectors.pkl      # Document mappings (optional)
└── docs/
    ├── page-slug-1.md
    ├── page-slug-2.md
    └── ...
```

### Markdown Format

```markdown
---
title: useState
url: https://react.dev/reference/react/useState
scraped_at: 2026-02-05T10:30:00Z
word_count: 1500
---

# useState

`useState` is a React Hook that lets you add a state variable to your component.

## Reference

### `useState(initialState)`

...
```

### Index Format

```json
{
  "project_id": "react",
  "base_url": "https://react.dev",
  "scraped_at": "2026-02-05T10:30:00Z",
  "total_pages": 150,
  "documents": [
    {
      "path": "reference-react-useState.md",
      "url": "https://react.dev/reference/react/useState",
      "title": "useState",
      "word_count": 1500
    }
  ]
}
```

---

## Security Model

### Authentication

- Single `API_TOKEN` for all requests
- Token passed via `Authorization: Bearer <token>` header
- Web UI uses session cookies (backed by same token)

### Authorization

- All authenticated requests have full access
- No role-based permissions (single-user design)
- Multi-tenancy not currently supported

### Network Security

- Designed for local/VPN access
- Use reverse proxy (nginx/Caddy) with SSL for public exposure
- Recommend firewall rules restricting access

---

## Performance Characteristics

### Resource Usage

| Mode | RAM | Disk | CPU |
|------|-----|------|-----|
| FTS only | ~100MB | ~50KB/page | Low |
| With Vector | ~500MB | ~100KB/page | Medium |

### Benchmarks (typical VPS)

| Operation | Time |
|-----------|------|
| FTS query (1K docs) | <10ms |
| Vector query (1K docs) | <50ms |
| Scrape page | ~2s (with delays) |
| Index 1K docs (FTS) | ~5s |
| Index 1K docs (Vector) | ~60s |

---

## Extension Points

### Custom Content Extractors

Override content extraction per-project:

```json
{
  "custom_selectors": {
    "title": "h1.page-title",
    "content": "main.content",
    "remove": [".nav", ".footer", ".ads"]
  }
}
```

### Webhooks

Receive notifications on scrape events:

```json
{
  "event": "scrape_complete",
  "project_id": "react",
  "status": "success",
  "pages_scraped": 150,
  "duration_seconds": 300,
  "timestamp": "2026-02-05T10:30:00Z"
}
```

### Custom Search Backends

Implement the `SearchBackend` protocol:

```python
class SearchBackend(Protocol):
    def index(self, project_id: str, documents: list[Document]) -> None: ...
    def search(self, project_id: str, query: str, limit: int) -> list[SearchResult]: ...
```

---

## Design Decisions

### Why SQLite FTS over Elasticsearch?

- Zero dependencies
- Embedded (no separate service)
- Good enough for <100K documents
- Runs on $5 VPS

### Why File-based Storage?

- Simple backup (just copy directory)
- Human-readable (grep-able)
- No database to corrupt
- Easy debugging

### Why Not Use LangChain/LlamaIndex?

- Massive dependencies
- Over-abstracted for this use case
- We control the entire pipeline
- Simpler = more maintainable

### Why Jinja2 over React/Vue?

- Server-side rendering is simpler
- No build step
- Faster initial load
- HTMX for interactivity where needed

---

## Next Steps

- [API Reference](api-reference.md) — Endpoint documentation
- [Configuration Guide](configuration.md) — All settings
- [Self-Hosting Guide](self-hosting.md) — Production deployment
