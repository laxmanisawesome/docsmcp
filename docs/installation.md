# Installation Guide

This guide covers all installation methods for DocsMCP.

---

## Requirements

- **Python 3.10+** (if running manually)
- **Docker 20.10+** (if using Docker)
- **2GB disk space** (minimum, grows with scraped content)
- **512MB RAM** (FTS mode) / **1GB RAM** (vector mode)

---

## Method 1: Docker Compose (Recommended)

The easiest way to run DocsMCP. Works on Linux, macOS, and Windows.

### Step 1: Clone the Repository

```bash
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
API_TOKEN=your-secret-token-here  # Change this!
```

### Step 3: Start the Server

```bash
docker-compose up -d
```

### Step 4: Verify Installation

```bash
# Check health
curl http://localhost:8090/health

# Should return:
# {"status": "healthy", "version": "1.0.0"}
```

### Step 5: Open Web UI

Navigate to [http://localhost:8090](http://localhost:8090)

---

## Method 2: One-Line Install Script

For quick setup on a fresh server:

```bash
curl -sSL https://raw.githubusercontent.com/laxmanisawesome/docsmcp/master/scripts/install.sh | bash
```

The script will:
1. Check prerequisites
2. Clone the repository
3. Create `.env` file
4. Start Docker containers
5. Print access instructions

### Interactive Mode

For guided setup with prompts:

```bash
curl -sSL https://raw.githubusercontent.com/laxmanisawesome/docsmcp/master/scripts/install.sh | bash -s -- --interactive
```

---

## Method 3: Manual Installation (No Docker)

For development or systems without Docker.

### Step 1: Clone and Setup Virtual Environment

```bash
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Core dependencies only (FTS search)
pip install -r requirements.txt

# Optional: Vector search support
pip install -r requirements-vector.txt
```

### Step 3: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### Step 4: Run the Server

```bash
python src/main.py
```

Or with hot reload for development:

```bash
python src/main.py --reload
```

---

## Method 4: Kubernetes / Helm

For production deployments on Kubernetes.

### Using Helm Chart

```bash
# Add helm repo
helm repo add docsmcp https://laxmanisawesome.github.io/docsmcp-charts
helm repo update

# Install
helm install docsmcp docsmcp/docsmcp \
  --set apiToken=your-secret-token \
  --set persistence.size=10Gi
```

### Using Raw Manifests

```bash
# Apply manifests
kubectl apply -f examples/kubernetes/

# Check deployment
kubectl get pods -l app=docsmcp
```

See [examples/kubernetes/](../examples/kubernetes/) for manifest files.

---

## Post-Installation

### 1. Add Your First Documentation Project

**Via Web UI:**
1. Open http://localhost:8090
2. Click "Add Project"
3. Enter project ID and documentation URL
4. Click "Start Scraping"

**Via CLI:**
```bash
docsmcp add react https://react.dev/reference
```

**Via API:**
```bash
curl -X POST http://localhost:8090/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"id": "react", "base_url": "https://react.dev/reference"}'
```

### 2. Configure MCP Client

See [MCP Setup Guide](mcp-setup.md) for Claude Desktop and VS Code configuration.

### 3. Set Up Scheduled Scrapes (Optional)

Add to your crontab for automatic updates:

```bash
# Update docs daily at 2 AM
0 2 * * * curl -X POST http://localhost:8090/api/projects/react/scrape -H "Authorization: Bearer your-token"
```

---

## Upgrading

### Docker

```bash
cd docsmcp
git pull
docker-compose pull
docker-compose up -d
```

### Manual Installation

```bash
cd docsmcp
git pull
source .venv/bin/activate
pip install -r requirements.txt --upgrade
# Restart the server
```

---

## Uninstalling

### Docker

```bash
cd docsmcp
docker-compose down -v  # -v removes volumes (data)
cd ..
rm -rf docsmcp
```

### Manual

```bash
rm -rf docsmcp
```

---

## Troubleshooting

### Port Already in Use

```bash
# Change port in .env
PORT=8091

# Or kill existing process
lsof -i :8090
kill -9 <PID>
```

### Permission Denied (Docker)

```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Out of Memory (Vector Search)

Vector search requires ~500MB additional RAM. Either:
- Disable vector search: `ENABLE_VECTOR_INDEX=0`
- Increase container memory limits
- Use a larger server

### Can't Connect from Claude Desktop

1. Ensure DocsMCP is running: `curl http://localhost:8090/health`
2. Check Claude Desktop config path is correct
3. Restart Claude Desktop after config changes
4. Check Claude Desktop logs for errors

See [Configuration Guide](configuration.md) for more troubleshooting.

---

## Next Steps

- [Configuration Guide](configuration.md) — All settings explained
- [MCP Setup](mcp-setup.md) — Connect to Claude Desktop
- [API Reference](api-reference.md) — REST & MCP endpoints
- [Self-Hosting Guide](self-hosting.md) — Production deployment
