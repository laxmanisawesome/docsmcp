<p align="center">
  <h1 align="center">📚 DocsMCP</h1>
  <p align="center">
    <strong>Self-hosted documentation search with native MCP support</strong>
  </p>
  <p align="center">
    Query any documentation site directly from Claude Desktop, VS Code, or any MCP client.<br/>
    No APIs. No accounts. Runs on a $5/month VPS.
  </p>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="docs/installation.md">Installation</a> •
  <a href="docs/configuration.md">Configuration</a> •
  <a href="docs/api-reference.md">API Reference</a>
</p>

---

**Maintainer:** [@laxmanisawesome](https://github.com/laxmanisawesome) • [81405043+laxmanisawesome@users.noreply.github.com](mailto:81405043+laxmanisawesome@users.noreply.github.com)

## The Problem

**Documentation is changing faster than AI models can keep up.**

- Models are trained on snapshots of documentation that become outdated within months
- Copy-pasting docs into Claude/ChatGPT is tedious and loses context
- Existing solutions require API keys, subscriptions, or cloud dependencies
- gitMCP exists for Git repos, but what about documentation sites?

**The result:** AI assistants give outdated answers, hallucinate deprecated APIs, and you waste time correcting them.

## The Solution

DocsMCP scrapes any documentation website, indexes it locally, and exposes it via the **Model Context Protocol (MCP)** — the emerging standard for AI tool integration.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Docs Site     │────▶│    DocsMCP      │────▶│  Claude/VS Code │
│  (react.dev)    │     │  (your server)  │     │   (MCP client)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      Scrape              Index + Search           Query directly
```

Ask Claude: *"What's the useState hook signature?"* → Claude queries your local DocsMCP → Gets current docs → Answers accurately.

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and start
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp
cp .env.example .env
docker-compose up -d

# Open Web UI
open http://localhost:8090

# Add your first docs
curl -X POST http://localhost:8090/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer changeme" \
  -d '{"id": "react", "base_url": "https://react.dev/reference"}'
```

### Option 2: One-Line Install

```bash
curl -sSL https://raw.githubusercontent.com/laxmanisawesome/docsmcp/master/scripts/install.sh | bash
```

### Option 3: Manual Installation

```bash
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

---

## Features

### 🔍 **Search That Actually Works**

| Feature | Default (FTS) | Optional (Vector) |
|---------|---------------|-------------------|
| Dependencies | None | +300MB |
| RAM Usage | ~50MB | ~500MB |
| Query Speed | <10ms | <50ms |
| Semantic Search | Keyword-based | Yes |
| Offline | ✅ | ✅ |

**Default: SQLite FTS5** — Zero setup, zero external dependencies, blazing fast.

**Optional: Local Vector Search** — Enable with `ENABLE_VECTOR_INDEX=1` for semantic queries using `all-MiniLM-L6-v2` (runs 100% locally).

### 🔌 **Native MCP Integration**

Works out-of-the-box with:
- **Claude Desktop** — Drop-in configuration
- **VS Code** — With MCP extension
- **Any MCP Client** — Standard JSON-RPC protocol

### 🖥️ **Clean Web Dashboard**

- Add/remove documentation projects
- Monitor scrape progress
- Search across all indexed docs
- Copy MCP configuration
- Mobile-responsive design

### 💻 **Powerful CLI**

```bash
# Add a project
docsmcp add react https://react.dev/reference

# Trigger rescrape
docsmcp scrape react

# Search
docsmcp search react "useState hook"

# List all projects
docsmcp list

# Delete a project
docsmcp delete react

# Export data
docsmcp export react ./backup/
```

### 🔒 **Self-Hosted & Private**

- **No telemetry** — Zero data leaves your server
- **No accounts** — No signup, no API keys required
- **Data ownership** — Your scraped docs stay on your infrastructure
- **Air-gapped** — Works completely offline after initial scrape

---

## ⚠️ Important Warnings

### Legal & Ethical Considerations

> **This tool scrapes websites. Use responsibly.**

- **Check Terms of Service** — Some sites explicitly prohibit scraping
- **Respect robots.txt** — Enabled by default, configurable
- **Rate limiting** — Built-in delays to avoid overloading servers
- **Private/auth content** — Only scrape publicly accessible pages
- **You are responsible** — DocsMCP is a tool; how you use it is your responsibility

### Security Considerations

> **Exposing DocsMCP to the public internet has risks.**

If you deploy on a VPS with a public IP:

1. **Always use authentication** — Set a strong `API_TOKEN` in `.env`
2. **Use HTTPS** — Put behind nginx/Caddy with SSL certificates
3. **Firewall rules** — Restrict access to known IPs if possible
4. **VPN recommended** — Access via Tailscale/WireGuard for maximum security

```bash
# Example: Restrict to localhost + your IP
ufw allow from 192.168.1.0/24 to any port 8090
ufw allow from YOUR_HOME_IP to any port 8090
```

For personal/private use, **run locally** or behind a VPN. The Web UI and API are designed for trusted environments.

---

## Architecture

```
docsmcp/
├── src/
│   ├── main.py          # FastAPI app, REST + MCP endpoints
│   ├── scraper.py       # Async web crawler
│   ├── fts_indexer.py   # SQLite FTS5 search
│   ├── indexer.py       # Optional vector search
│   ├── config.py        # Settings & environment
│   ├── models.py        # Pydantic schemas
│   ├── cli.py           # Command-line interface
│   └── web/             # Dashboard UI
├── data/
│   └── projects/        # Scraped docs storage
│       └── {project_id}/
│           ├── config.json
│           ├── index.json
│           ├── fts.db
│           └── docs/
│               └── *.md
```

### Data Flow

1. **Scrape** — Crawl documentation site, extract content
2. **Convert** — HTML → Clean Markdown with YAML frontmatter
3. **Index** — Build FTS (and optionally vector) index
4. **Query** — Search via REST API or MCP protocol
5. **Respond** — Return relevant docs to AI assistant

---

## Configuration

All settings via environment variables. Copy `.env.example` to `.env`:

```bash
# Required
API_TOKEN=your-secret-token-here

# Search (default: FTS only)
ENABLE_VECTOR_INDEX=0

# Scraping behavior
MAX_PAGES_PER_PROJECT=10000
RATE_LIMIT_DELAY=1.0
RESPECT_ROBOTS_TXT=permissive

# Server
HOST=0.0.0.0
PORT=8090
```

See [Configuration Guide](docs/configuration.md) for all options.

---

## MCP Client Setup

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "docs": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "docsmcp_data:/app/data",
        "ghcr.io/laxmanisawesome/docsmcp:latest",
        "python", "src/mcp_stdio.py"
      ]
    }
  }
}
```

Or if running locally:

```json
{
  "mcpServers": {
    "docs": {
      "command": "python",
      "args": ["/path/to/docsmcp/src/mcp_stdio.py"],
      "env": {
        "DATA_DIR": "/path/to/docsmcp/data"
      }
    }
  }
}
```

See [MCP Setup Guide](docs/mcp-setup.md) for VS Code and other clients.

---

## Comparison

| Feature | DocsMCP | RAG APIs | Manual Copy-Paste |
|---------|---------|----------|-------------------|
| Self-hosted | ✅ | ❌ | N/A |
| No API keys | ✅ | ❌ | ✅ |
| MCP native | ✅ | ❌ | ❌ |
| Auto-updates | ✅ Scheduled | Varies | ❌ Manual |
| Cost | $0-5/mo | $20-100+/mo | Free |
| Offline | ✅ | ❌ | ✅ |
| Multi-site | ✅ | Varies | Tedious |

---

## Roadmap

- [x] **v1.0** — Core scraper, FTS search, MCP endpoint, Web UI
- [ ] **v1.1** — Local vector search, scheduled scrapes, webhooks
- [ ] **v1.2** — Multi-tenancy, Kubernetes support, metrics
- [ ] **v2.0** — Cloud offering (optional managed hosting)

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

```bash
# Development setup
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install

# Run tests
pytest

# Start dev server
python src/main.py --reload
```

---

## Philosophy

> **DocsMCP will always be:**
>
> - 🔓 **Self-hostable** — Core functionality never cloud-only
> - 🔒 **Private** — Zero telemetry in self-hosted version
> - 📦 **Data ownership** — Your docs stay on your infrastructure
> - 📐 **API stable** — Semantic versioning, deprecation notices
> - 📜 **MIT licensed** — Fork it, sell it, modify it

---

## Support

- 📖 [Documentation](docs/)
- 💬 [GitHub Discussions](https://github.com/laxmanisawesome/docsmcp/discussions)
- 🐛 [Issue Tracker](https://github.com/laxmanisawesome/docsmcp/issues)

---

## License

[MIT](LICENSE) — Use it however you want.

---

<p align="center">
  Built with ❤️ for the MCP ecosystem
</p>
