# MCP Client Setup Guide

Connect DocsMCP to Claude Desktop, VS Code, and other MCP clients.

---

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard that allows AI assistants to connect to external tools and data sources. DocsMCP implements MCP, allowing Claude and other AI assistants to query your documentation directly.

---

## Claude Desktop

### Prerequisites

- Claude Desktop installed ([download](https://claude.ai/download))
- DocsMCP running (see [Installation](installation.md))

### Configuration

1. **Locate Claude Desktop config file:**

   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. **Edit the config file:**

   Create the file if it doesn't exist, then add:

### Option A: Connect to Running Server (HTTP)

If DocsMCP is running as a server (Docker or manual):

```json
{
  "mcpServers": {
    "docs": {
      "url": "http://localhost:8090/mcp",
      "headers": {
        "Authorization": "Bearer your-api-token"
      }
    }
  }
}
```

### Option B: Spawn Docker Container (STDIO)

Claude Desktop can spawn a Docker container directly:

```json
{
  "mcpServers": {
    "docs": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "docsmcp_data:/app/data",
        "-e", "API_TOKEN=your-api-token",
        "ghcr.io/laxmanisawesome/docsmcp:latest",
        "python", "src/mcp_stdio.py"
      ]
    }
  }
}
```

### Option C: Direct Python (Local Install)

If you installed DocsMCP manually:

```json
{
  "mcpServers": {
    "docs": {
      "command": "python",
      "args": ["/path/to/docsmcp/src/mcp_stdio.py"],
      "env": {
        "DATA_DIR": "/path/to/docsmcp/data",
        "API_TOKEN": "your-api-token"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

   Completely quit and restart Claude Desktop for config changes to take effect.

4. **Verify Connection**

   In Claude Desktop, you should see "docs" in the available tools. Ask Claude:

   > "What documentation sources are available?"

   Claude should respond with your indexed projects.

---

## VS Code (MCP Extension)

### Prerequisites

- VS Code installed
- MCP extension for VS Code (when available)
- DocsMCP running

### Configuration

Add to your VS Code `settings.json`:

```json
{
  "mcp.servers": [
    {
      "name": "DocsMCP",
      "url": "http://localhost:8090/mcp",
      "headers": {
        "Authorization": "Bearer your-api-token"
      }
    }
  ]
}
```

---

## Continue.dev

For Continue.dev IDE extension:

```json
{
  "models": [...],
  "mcpServers": [
    {
      "name": "docs",
      "transport": {
        "type": "http",
        "url": "http://localhost:8090/mcp",
        "headers": {
          "Authorization": "Bearer your-api-token"
        }
      }
    }
  ]
}
```

---

## Custom MCP Client

If building your own MCP client, connect via:

### HTTP Transport

```
POST http://localhost:8090/mcp
Content-Type: application/json
Authorization: Bearer your-api-token

{
  "jsonrpc": "2.0",
  "method": "search_docs",
  "params": {
    "project": "react",
    "query": "useState hook"
  },
  "id": 1
}
```

### STDIO Transport

Run the STDIO bridge:

```bash
python src/mcp_stdio.py
```

Then send JSON-RPC messages via stdin, receive via stdout.

---

## Available MCP Methods

### `list_projects`

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

### `search_docs`

Search documentation across all or specific projects.

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

### `get_document`

Retrieve full content of a specific document.

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

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "title": "useState",
    "url": "https://react.dev/reference/react/useState",
    "content": "# useState\n\n`useState` is a React Hook...",
    "metadata": {
      "scraped_at": "2026-02-05T10:30:00Z",
      "word_count": 1500
    }
  },
  "id": 3
}
```

---

## Troubleshooting

### Claude Desktop Not Showing Tools

1. **Check config file location** — Path is case-sensitive
2. **Validate JSON syntax** — Use a JSON validator
3. **Restart Claude Desktop** — Fully quit (not just close window)
4. **Check Claude Desktop logs:**
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### Connection Refused

1. **Verify DocsMCP is running:**
   ```bash
   curl http://localhost:8090/health
   ```

2. **Check port is correct** — Default is 8090

3. **Check firewall** — Allow connections on port 8090

### Authentication Failed

1. **Verify API token matches** — Token in Claude config must match DocsMCP `.env`

2. **Check for typos** — Tokens are case-sensitive

3. **Regenerate token:**
   ```bash
   # In .env
   API_TOKEN=$(openssl rand -hex 32)
   ```

### No Search Results

1. **Verify project is scraped:**
   ```bash
   curl http://localhost:8090/api/projects
   ```

2. **Check project has pages:**
   ```bash
   curl http://localhost:8090/api/projects/react
   ```

3. **Trigger a rescrape:**
   ```bash
   curl -X POST http://localhost:8090/api/projects/react/scrape \
     -H "Authorization: Bearer your-token"
   ```

---

## Example Prompts

Once connected, try these prompts in Claude:

> "Search the React docs for information about the useEffect hook"

> "What projects are available in my docs?"

> "Find documentation about error handling in Python"

> "Get the full content of the useState reference page from React docs"

---

## Next Steps

- [API Reference](api-reference.md) — All REST & MCP endpoints
- [Configuration Guide](configuration.md) — Customize DocsMCP
- [Self-Hosting Guide](self-hosting.md) — Deploy on a VPS
