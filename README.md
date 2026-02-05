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

**Maintainer:** [@laxmanisawesome](https://github.com/laxmanisawesome) • [laxtothemax@proton.me](mailto:laxtothemax@proton.me)

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

### 🚀 **One-Line Installation** (Recommended)

**Prerequisites:** For the best experience, install [Docker](https://docs.docker.com/get-docker/) first.

```bash
# Install DocsMCP with interactive setup
curl -sSL https://raw.githubusercontent.com/laxmanisawesome/docsmcp/master/scripts/install.sh | bash
```

**What happens:**
1. **Detects Docker** — Recommends Docker mode for production or local Python for development
2. **Installs DocsMCP** — Complete setup with all dependencies
3. **Tests the service** — Verifies everything works and provides localhost URL
4. **Creates management scripts** — Easy start/stop commands for your installation

### 📊 **Using the Web Dashboard**

1. **Visit:** `http://localhost:8090`
2. **Add a project:** Enter any documentation URL (e.g., `https://react.dev`)
3. **Auto-scraping:** DocsMCP indexes the site in the background
4. **Get MCP config:** Copy the ready-to-use configuration for Claude Desktop or VS Code
5. **Start querying:** Ask your AI about the latest documentation!

### 🔧 **Service Management**

After installation, you can manage DocsMCP using these commands:

**Docker Mode:**
```bash
# View logs
docker compose -f ~/.docsmcp/docker-compose.yml logs -f

# Stop service
docker compose -f ~/.docsmcp/docker-compose.yml down

# Restart service
docker compose -f ~/.docsmcp/docker-compose.yml restart
```

**Local Python Mode:**
```bash
# Start service
cd ~/.docsmcp && ./start.sh

# Stop service 
cd ~/.docsmcp && ./stop.sh

# Manual start (for development)
cd ~/.docsmcp && source venv/bin/activate && python -m src.main
```

**Uninstall (both modes):**
```bash
rm -rf ~/.docsmcp
```

### ⚡ **Alternative Methods**

<details>
<summary>Docker Compose Setup</summary>

```bash
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp
cp .env.example .env
docker-compose up -d
# Open http://localhost:8090
```

</details>

<details>
<summary>Manual Python Installation</summary>

```bash
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
# Open http://localhost:8090
```

</details>

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

### 🖥️ **Complete Web Dashboard**

**Professional interface for managing your documentation ecosystem:**

- **📊 Project Overview** — Real-time stats and status monitoring
- **➕ One-Click Setup** — Add any documentation site with a URL
- **📋 MCP Config Generator** — Get ready-to-use configuration for:
  - Claude Desktop
  - VS Code MCP
  - Custom MCP clients
- **🔍 Integrated Search** — Query across all projects with live results  
- **📂 Project Management** — View details, documents, scraping status
- **📱 Mobile Responsive** — Clean interface on any device
- **🔧 Configuration Hub** — Manage settings, API keys, endpoints

**Try it live:** After installation, visit `http://localhost:8090` to see the full dashboard in action.

![DocsMCP Dashboard Preview](https://via.placeholder.com/800x400/f8f8f8/333333?text=DocsMCP+Dashboard+%E2%80%A2+Add+Projects+%E2%80%A2+Generate+Configs+%E2%80%A2+Search+Docs)

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

## MCP Setup & Integration

DocsMCP provides **automatic MCP configuration generation** for seamless integration with any MCP client.

### 🖥️ **Claude Desktop** 

1. Open DocsMCP dashboard → **MCP Configuration** section
2. Copy the **Claude Desktop** config
3. Paste into your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "docsmcp": {
      "command": "curl",
      "args": [
        "-s", "-X", "POST", 
        "http://localhost:8090/mcp",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ]
    }
  }
}
```

4. Restart Claude Desktop
5. **Test:** Ask Claude *"Search my documentation for useState"*

### 🔧 **VS Code MCP**

1. Install the MCP extension in VS Code
2. Copy the **VS Code** config from the dashboard:

```json
{
  "docsmcp": {
    "type": "http",
    "url": "http://localhost:8090/mcp",
    "description": "Documentation search via DocsMCP"
  }
}
```

3. Add to your MCP settings
4. **Test:** Use MCP commands to query your indexed docs

### ⚡ **Project-Specific Configs**

The dashboard can generate MCP configurations for individual projects:

1. Click **"Details"** on any project
2. Copy the project-specific MCP config
3. Multiple projects = Multiple MCP servers for organized access

### 🔗 **Custom MCP Clients**

**Endpoint:** `http://localhost:8090/mcp`  
**Protocol:** JSON-RPC 2.0 over HTTP POST

Example query:
```bash
curl -X POST http://localhost:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": "1"
  }'
```

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
