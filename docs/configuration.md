# Configuration Guide

Complete reference for all DocsMCP configuration options.

---

## Environment Variables

All configuration is done via environment variables. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

---

## Core Settings

### `API_TOKEN` (Required)

Authentication token for API and Web UI access.

```bash
API_TOKEN=your-secret-token-here
```

- **Required:** Yes
- **Default:** None (must be set)
- **Security:** Use a strong, random string (32+ characters recommended)

Generate a secure token:
```bash
openssl rand -hex 32
```

### `HOST`

Server bind address.

```bash
HOST=0.0.0.0
```

- **Default:** `0.0.0.0` (all interfaces)
- **Options:**
  - `0.0.0.0` — Accept connections from any IP
  - `127.0.0.1` — Localhost only (more secure)

### `PORT`

Server port number.

```bash
PORT=8090
```

- **Default:** `8090`
- **Range:** 1-65535

### `DATA_DIR`

Directory for storing scraped documentation and indexes.

```bash
DATA_DIR=/app/data
```

- **Default:** `./data` (relative to project root)
- **Docker:** `/app/data` (mounted volume)

---

## Search Settings

### `ENABLE_VECTOR_INDEX`

Enable local vector search (semantic queries).

```bash
ENABLE_VECTOR_INDEX=0
```

- **Default:** `0` (disabled)
- **Options:**
  - `0` — FTS only (faster, lower resource usage)
  - `1` — Enable vector search (requires +300MB disk, +500MB RAM)

### `SEARCH_RESULTS_LIMIT`

Maximum number of search results to return.

```bash
SEARCH_RESULTS_LIMIT=10
```

- **Default:** `10`
- **Range:** 1-100

### `EMBEDDING_MODEL`

Model for vector embeddings (only if vector search enabled).

```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

- **Default:** `sentence-transformers/all-MiniLM-L6-v2`
- **Options:** Any sentence-transformers compatible model

---

## Scraping Settings

### `MAX_PAGES_PER_PROJECT`

Maximum pages to scrape per project.

```bash
MAX_PAGES_PER_PROJECT=10000
```

- **Default:** `10000`
- **Note:** Large sites may have thousands of pages; adjust based on your needs and disk space

### `RATE_LIMIT_DELAY`

Seconds to wait between HTTP requests.

```bash
RATE_LIMIT_DELAY=1.0
```

- **Default:** `1.0`
- **Range:** 0.1-60.0
- **Note:** Lower values = faster scraping but may trigger rate limits

### `RESPECT_ROBOTS_TXT`

How to handle robots.txt rules.

```bash
RESPECT_ROBOTS_TXT=permissive
```

- **Default:** `permissive`
- **Options:**
  - `strict` — Fully respect robots.txt (may block some pages)
  - `permissive` — Respect crawl-delay, ignore disallow rules
  - `ignore` — Ignore robots.txt entirely (use responsibly)

### `USER_AGENT`

HTTP User-Agent string for requests.

```bash
USER_AGENT=DocsMCP/1.0 (+https://github.com/laxmanisawesome/docsmcp)
```

- **Default:** `DocsMCP/1.0`
- **Note:** Some sites block non-browser user agents

### `REQUEST_TIMEOUT`

HTTP request timeout in seconds.

```bash
REQUEST_TIMEOUT=30
```

- **Default:** `30`
- **Range:** 5-120

### `MAX_CONCURRENT_SCRAPES`

Maximum number of projects scraping simultaneously.

```bash
MAX_CONCURRENT_SCRAPES=3
```

- **Default:** `3`
- **Note:** Higher values use more RAM and bandwidth

### `MAX_DEPTH`

Default maximum crawl depth from base URL.

```bash
MAX_DEPTH=5
```

- **Default:** `5`
- **Note:** Can be overridden per-project in config.json

---

## Webhook Settings

### `WEBHOOK_URL`

URL to POST scrape completion events.

```bash
WEBHOOK_URL=https://your-server.com/webhook
```

- **Default:** Empty (disabled)
- **Payload:** JSON with project ID, status, page count, errors

### `WEBHOOK_ON_SUCCESS`

Send webhook when scrape completes successfully.

```bash
WEBHOOK_ON_SUCCESS=true
```

- **Default:** `true`

### `WEBHOOK_ON_ERROR`

Send webhook when scrape fails.

```bash
WEBHOOK_ON_ERROR=true
```

- **Default:** `true`

---

## Logging Settings

### `LOG_LEVEL`

Logging verbosity level.

```bash
LOG_LEVEL=INFO
```

- **Default:** `INFO`
- **Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### `LOG_FORMAT`

Log output format.

```bash
LOG_FORMAT=json
```

- **Default:** `text`
- **Options:**
  - `text` — Human-readable
  - `json` — Structured JSON (better for log aggregation)

### `SENTRY_DSN`

Sentry error tracking DSN (optional).

```bash
SENTRY_DSN=https://xxx@sentry.io/yyy
```

- **Default:** Empty (disabled)

---

## Security Settings

### `ALLOWED_ORIGINS`

CORS allowed origins.

```bash
ALLOWED_ORIGINS=*
```

- **Default:** `*` (all origins)
- **Production:** Set to specific origins: `https://yourdomain.com,http://localhost:3000`

### `ENABLE_AUTH`

Require authentication for all requests.

```bash
ENABLE_AUTH=true
```

- **Default:** `true`
- **Warning:** Setting to `false` exposes your API without authentication

### `RATE_LIMIT_REQUESTS`

Maximum API requests per minute per IP.

```bash
RATE_LIMIT_REQUESTS=100
```

- **Default:** `100`
- **Note:** Set to `0` to disable rate limiting

---

## Project Configuration

Each project can have its own configuration file at `data/projects/{project_id}/config.json`:

```json
{
  "id": "react-docs",
  "base_url": "https://react.dev",
  "max_depth": 3,
  "max_pages": 500,
  "include_patterns": [
    "/learn/*",
    "/reference/*"
  ],
  "exclude_patterns": [
    "/blog/*",
    "/_next/*",
    "*.pdf"
  ],
  "schedule": "0 2 * * *",
  "custom_selectors": {
    "title": "h1.title",
    "content": "article.main",
    "remove": [".sidebar", ".nav", ".footer"]
  },
  "headers": {
    "Accept-Language": "en-US"
  },
  "rate_limit_delay": 2.0
}
```

### Project Config Options

| Option | Type | Description |
|--------|------|-------------|
| `id` | string | Unique project identifier |
| `base_url` | string | Starting URL for scrape |
| `max_depth` | int | Maximum crawl depth |
| `max_pages` | int | Maximum pages to scrape |
| `include_patterns` | array | URL patterns to include (glob) |
| `exclude_patterns` | array | URL patterns to exclude (glob) |
| `schedule` | string | Cron expression for auto-scrape |
| `custom_selectors` | object | CSS selectors for content extraction |
| `headers` | object | Custom HTTP headers |
| `rate_limit_delay` | float | Override global rate limit |

---

## Example Configurations

### Minimal (FTS Only)

```bash
API_TOKEN=changeme
PORT=8090
ENABLE_VECTOR_INDEX=0
```

### Production (VPS)

```bash
API_TOKEN=your-32-char-secure-token-here
HOST=127.0.0.1
PORT=8090
DATA_DIR=/var/lib/docsmcp
ENABLE_VECTOR_INDEX=0
LOG_LEVEL=INFO
LOG_FORMAT=json
ALLOWED_ORIGINS=https://yourdomain.com
RATE_LIMIT_REQUESTS=60
MAX_PAGES_PER_PROJECT=5000
```

### Development

```bash
API_TOKEN=devtoken
HOST=127.0.0.1
PORT=8090
LOG_LEVEL=DEBUG
ENABLE_AUTH=false
RATE_LIMIT_REQUESTS=0
```

### With Vector Search

```bash
API_TOKEN=changeme
PORT=8090
ENABLE_VECTOR_INDEX=1
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Validating Configuration

Run config validation:

```bash
python src/main.py --validate-config
```

Or via Docker:

```bash
docker-compose run --rm docsmcp python src/main.py --validate-config
```

---

## Next Steps

- [Installation Guide](installation.md) — Set up DocsMCP
- [MCP Setup](mcp-setup.md) — Connect to Claude Desktop
- [Self-Hosting Guide](self-hosting.md) — Production deployment
