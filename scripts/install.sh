#!/usr/bin/env bash
#
# DocsMCP One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/laxmanisawesome/docsmcp/master/scripts/install.sh | bash
#
# Options (via environment variables):
#   DOCSMCP_DIR     Installation directory (default: ~/.docsmcp)
#   DOCSMCP_PORT    Server port (default: 8090)
#   SKIP_DOCKER     Skip Docker installation (set to 1)
#   DEV_MODE        Install from source for development (set to 1)
#   AUTO_INSTALL_DOCKER  Install Docker non-interactively if missing (set to 1)
#   FORCE_LOCAL          Force local Python (dev) mode non-interactively (set to 1)
#   AUTO_START_DOCKER    Attempt to auto-start Docker if daemon not running (macOS only)
#

set -euo pipefail

# Colors (disabled if not TTY)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Defaults
DOCSMCP_DIR="${DOCSMCP_DIR:-$HOME/.docsmcp}"
DOCSMCP_PORT="${DOCSMCP_PORT:-8090}"
SKIP_DOCKER="${SKIP_DOCKER:-0}"
DEV_MODE="${DEV_MODE:-0}"
REPO_URL="https://github.com/laxmanisawesome/docsmcp"

log() { echo -e "${BLUE}[DocsMCP]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

print_banner() {
    echo ""
    echo -e "${BLUE}"
    echo "  ┌─────────────────────────────────────────┐"
    echo "  │            DocsMCP Installer            │"
    echo "  │    Documentation → MCP in minutes       │"
    echo "  └─────────────────────────────────────────┘"
    echo -e "${NC}"
    echo ""
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check OS
    OS="$(uname -s)"
    case "$OS" in
        Linux*)  OS_TYPE=linux;;
        Darwin*) OS_TYPE=macos;;
        *)       error "Unsupported OS: $OS";;
    esac
    
    # Check architecture
    ARCH="$(uname -m)"
    case "$ARCH" in
        x86_64|amd64)   ARCH_TYPE=amd64;;
        arm64|aarch64)  ARCH_TYPE=arm64;;
        *)              error "Unsupported architecture: $ARCH";;
    esac
    
    success "OS: $OS_TYPE ($ARCH_TYPE)"
    
    # Check curl or wget
    if command -v curl &>/dev/null; then
        DOWNLOADER="curl -fsSL"
    elif command -v wget &>/dev/null; then
        DOWNLOADER="wget -qO-"
    else
        error "curl or wget is required"
    fi
    
    # Check git (for dev mode)
    if [[ "$DEV_MODE" == "1" ]] && ! command -v git &>/dev/null; then
        error "git is required for development mode"
    fi
}

check_docker() {
    if [[ "$SKIP_DOCKER" == "1" ]]; then
        warn "Skipping Docker check (SKIP_DOCKER=1)"
        return
    fi

    log "Checking Docker..."

    if ! command -v docker &>/dev/null; then
        # Non-interactive options
        if [[ "${AUTO_INSTALL_DOCKER:-0}" == "1" ]]; then
            log "AUTO_INSTALL_DOCKER=1 set — installing Docker automatically"
            install_docker
            return
        fi
        if [[ "${FORCE_LOCAL:-0}" == "1" ]]; then
            log "FORCE_LOCAL=1 set — switching to local Python (development) mode"
            DEV_MODE=1
            return
        fi

        # Interactive prompt with choices
        echo ""
        echo "[!] Docker not found. What would you like to do?"
        echo "  (I)nstall Docker now (recommended)"
        echo "  (L)ocal Python (dev) mode — run using virtualenv on this machine"
        echo "  (S)kip Docker and exit (you can set SKIP_DOCKER=1 to bypass)"
        # Read from /dev/tty so prompts work when script is piped into bash
        read -r -p "Choose I / L / S [I]: " choice </dev/tty
        choice="${choice:-I}"
        # Portable uppercase conversion for macOS bash compatibility
        choice="$(printf '%s' "$choice" | tr '[:lower:]' '[:upper:]')"
        case "$choice" in
            I)
                install_docker
                ;;
            L)
                log "Switching to local Python (development) mode"
                DEV_MODE=1
                ;;
            S)
                warn "Skipping Docker. You can rerun the installer with Docker available or set SKIP_DOCKER=1"
                SKIP_DOCKER=1
                ;;
            *)
                log "Unrecognized option — defaulting to Install Docker"
                install_docker
                ;;
        esac
    fi

    # If Docker exists but daemon is not running
    if command -v docker &>/dev/null; then
        if ! docker info &>/dev/null; then
            warn "Docker CLI found but Docker daemon isn't running."
            if [[ "${AUTO_START_DOCKER:-0}" == "1" ]]; then
                log "AUTO_START_DOCKER=1 set — attempting to start Docker (macOS only supported via open)"
                if [[ "$OS_TYPE" == "macos" ]]; then
                    open -a Docker || true
                    log "Launched Docker.app — please wait a few seconds and re-run the installer if it's still not ready"
                else
                    warn "Automatic Docker start is not implemented for this OS. Please start the daemon and re-run the installer."
                fi
            else
                error "Docker daemon is not running. Please start Docker and try again."
            fi
        fi
    fi

    success "Docker is ready"
}

install_docker() {
    log "Installing Docker..."
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        # Use official Docker install script
        $DOWNLOADER https://get.docker.com | sh
        
        # Add current user to docker group
        if [[ -n "${SUDO_USER:-}" ]]; then
            sudo usermod -aG docker "$SUDO_USER"
        else
            sudo usermod -aG docker "$USER"
        fi
        
        warn "You may need to log out and back in for Docker group changes to take effect"
    elif [[ "$OS_TYPE" == "macos" ]]; then
        if command -v brew &>/dev/null; then
            brew install --cask docker
        else
            error "Please install Docker Desktop from https://docker.com/products/docker-desktop"
        fi
    fi
    
    success "Docker installed"
}

create_directories() {
    log "Creating installation directory..."
    
    # For dev mode, create empty directory for git clone
    # For docker mode, create subdirectories
    if [[ "$DEV_MODE" == "1" ]]; then
        mkdir -p "$DOCSMCP_DIR"
    else
        mkdir -p "$DOCSMCP_DIR"/{data,logs,config}
    fi
    
    success "Created $DOCSMCP_DIR"
}

download_files() {
    log "Downloading DocsMCP..."
    
    cd "$DOCSMCP_DIR"
    
    if [[ "$DEV_MODE" == "1" ]]; then
        # Clone repository for development
        if [[ -d ".git" ]]; then
            git pull origin master
        else
            git clone "$REPO_URL.git" .
            # Create data directories after clone
            mkdir -p data logs config
        fi
        success "Repository cloned"
    else
        # Download docker-compose and env files only
        $DOWNLOADER "$REPO_URL/raw/master/docker-compose.yml" > docker-compose.yml
        
        if [[ ! -f ".env" ]]; then
            $DOWNLOADER "$REPO_URL/raw/master/.env.example" > .env
        fi
        
        success "Configuration files downloaded"
    fi
}

configure() {
    log "Configuring DocsMCP..."
    
    cd "$DOCSMCP_DIR"
    
    # Update port in .env if specified
    if [[ "$DOCSMCP_PORT" != "8090" ]]; then
        if [[ "$OS_TYPE" == "macos" ]]; then
            sed -i '' "s/PORT=8090/PORT=$DOCSMCP_PORT/" .env
        else
            sed -i "s/PORT=8090/PORT=$DOCSMCP_PORT/" .env
        fi
    fi
    
    # Update data directory in docker-compose
    if [[ "$OS_TYPE" == "macos" ]]; then
        sed -i '' "s|./data:|$DOCSMCP_DIR/data:|g" docker-compose.yml
    else
        sed -i "s|./data:|$DOCSMCP_DIR/data:|g" docker-compose.yml
    fi
    
    success "Configuration complete"
}

start_service() {
    log "Starting DocsMCP..."
    
    cd "$DOCSMCP_DIR"
    
    if [[ "$DEV_MODE" == "1" ]]; then
        # Development mode - use local Python
        if ! command -v python3 &>/dev/null; then
            error "Python 3 is required for development mode"
        fi
        
        log "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        
        log "Installing dependencies..."
        pip install -q -r requirements.txt
        
        # Install missing dependencies that might be needed
        pip install -q lxml_html_clean >/dev/null 2>&1 || true
        
        # Create startup script
        cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
exec python -m src.main
EOF
        chmod +x start.sh
        
        # Create stop script 
        cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stopping DocsMCP..."
pkill -f "python -m src.main" || true
EOF
        chmod +x stop.sh
        
        # Test startup briefly to verify everything works
        log "Testing service startup..."
        timeout 10s python -m src.main > startup.log 2>&1 &
        SERVICE_PID=$!
        
        # Wait a moment for startup
        sleep 5
        
        # Test if service responds
        if curl -sf \"http://localhost:$DOCSMCP_PORT/health\" >/dev/null 2>&1; then
            log "Service test successful - stopping test instance"
            kill $SERVICE_PID 2>/dev/null || true
            wait $SERVICE_PID 2>/dev/null || true
            success "DocsMCP installed and tested successfully"
        else
            kill $SERVICE_PID 2>/dev/null || true
            wait $SERVICE_PID 2>/dev/null || true
            warn "Service test failed - check startup.log for details"
            log "You can manually start with: cd $DOCSMCP_DIR && ./start.sh"
        fi
        
    else
        # Production mode - use Docker
        if ! command -v docker &>/dev/null; then
            error "Docker is required for production mode. Install Docker first or use local Python mode."
        fi
        
        docker compose pull
        docker compose up -d
        
        # Wait for service to be ready
        log "Waiting for service to start..."
        for i in {1..30}; do
            if curl -sf "http://localhost:$DOCSMCP_PORT/health" &>/dev/null; then
                success "Service is ready"
                return
            fi
            sleep 1
        done
        
        warn "Service may still be starting. Check logs: docker compose logs -f"
    fi
}

create_service_scripts() {
    log "Creating service management scripts..."
    
    if [[ "$DEV_MODE" == "1" ]]; then
        # Local Python mode scripts
        cat > "$DOCSMCP_DIR/docsmcp-start" << 'START_SCRIPT'
#!/bin/bash
DOCSMCP_DIR="$(dirname "$(realpath "$0")")"
cd "$DOCSMCP_DIR"

if [[ -f "docsmcp.pid" ]]; then
    PID=$(cat docsmcp.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo "DocsMCP is already running (PID: $PID)"
        echo "Access it at: http://localhost:8090"
        exit 0
    else
        rm -f docsmcp.pid
    fi
fi

echo "Starting DocsMCP..."
source venv/bin/activate
nohup python -m src.main > docsmcp.log 2>&1 &
echo $! > docsmcp.pid
echo "DocsMCP started (PID: $!)"
echo "Access it at: http://localhost:8090"
echo "View logs with: tail -f $DOCSMCP_DIR/docsmcp.log"
START_SCRIPT

        cat > "$DOCSMCP_DIR/docsmcp-stop" << 'STOP_SCRIPT'
#!/bin/bash
DOCSMCP_DIR="$(dirname "$(realpath "$0")")"
cd "$DOCSMCP_DIR"

if [[ -f "docsmcp.pid" ]]; then
    PID=$(cat docsmcp.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping DocsMCP (PID: $PID)..."
        kill "$PID"
        rm -f docsmcp.pid
        echo "DocsMCP stopped"
    else
        echo "DocsMCP is not running"
        rm -f docsmcp.pid
    fi
else
    echo "DocsMCP is not running (no PID file found)"
    # Fallback: kill any running instances
    pkill -f "python -m src.main" && echo "Killed orphaned DocsMCP processes"
fi
STOP_SCRIPT

        cat > "$DOCSMCP_DIR/docsmcp-status" << 'STATUS_SCRIPT'
#!/bin/bash
DOCSMCP_DIR="$(dirname "$(realpath "$0")")"
cd "$DOCSMCP_DIR"

if [[ -f "docsmcp.pid" ]]; then
    PID=$(cat docsmcp.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo "✅ DocsMCP is running (PID: $PID)"
        echo "📊 Access dashboard: http://localhost:8090"
        echo "🔗 MCP endpoint: http://localhost:8090/mcp"
        # Test if actually responding
        if curl -sf "http://localhost:8090/health" >/dev/null 2>&1; then
            echo "🟢 Service is responding"
        else
            echo "🔴 Service may be starting or having issues"
        fi
    else
        echo "🔴 DocsMCP is not running (stale PID file)"
        rm -f docsmcp.pid
    fi
else
    echo "🔴 DocsMCP is not running"
fi
STATUS_SCRIPT

        chmod +x "$DOCSMCP_DIR/docsmcp-start"
        chmod +x "$DOCSMCP_DIR/docsmcp-stop"
        chmod +x "$DOCSMCP_DIR/docsmcp-status"
        
    else
        # Docker mode scripts
        cat > "$DOCSMCP_DIR/docsmcp-start" << 'DOCKER_START'
#!/bin/bash
DOCSMCP_DIR="$(dirname "$(realpath "$0")")"
cd "$DOCSMCP_DIR"

echo "Starting DocsMCP with Docker..."
docker compose up -d

# Wait for service to be ready
echo "Waiting for service to start..."
for i in {1..30}; do
    if curl -sf "http://localhost:8090/health" &>/dev/null; then
        echo "✅ DocsMCP is running!"
        echo "📊 Access dashboard: http://localhost:8090"
        echo "🔗 MCP endpoint: http://localhost:8090/mcp"
        exit 0
    fi
    sleep 1
done

echo "⚠️  Service may still be starting. Check logs with: docker compose logs -f"
DOCKER_START

        cat > "$DOCSMCP_DIR/docsmcp-stop" << 'DOCKER_STOP'
#!/bin/bash
DOCSMCP_DIR="$(dirname "$(realpath "$0")")"
cd "$DOCSMCP_DIR"

echo "Stopping DocsMCP..."
docker compose down
echo "DocsMCP stopped"
DOCKER_STOP

        cat > "$DOCSMCP_DIR/docsmcp-status" << 'DOCKER_STATUS'
#!/bin/bash
DOCSMCP_DIR="$(dirname "$(realpath "$0")")"
cd "$DOCSMCP_DIR"

# Check if containers are running
if docker compose ps --services --filter "status=running" | grep -q docsmcp; then
    echo "✅ DocsMCP is running"
    echo "📊 Access dashboard: http://localhost:8090"
    echo "🔗 MCP endpoint: http://localhost:8090/mcp"
    # Test if actually responding
    if curl -sf "http://localhost:8090/health" >/dev/null 2>&1; then
        echo "🟢 Service is responding"
    else
        echo "🔴 Service may be starting or having issues"
    fi
else
    echo "🔴 DocsMCP is not running"
fi
echo ""
echo "📋 Container status:"
docker compose ps
DOCKER_STATUS

        chmod +x "$DOCSMCP_DIR/docsmcp-start"
        chmod +x "$DOCSMCP_DIR/docsmcp-stop"
        chmod +x "$DOCSMCP_DIR/docsmcp-status"
    fi
}

create_cli_wrapper() {
    
    # Create wrapper script
    cat > "$DOCSMCP_DIR/docsmcp" << 'WRAPPER'
#!/usr/bin/env bash
DOCSMCP_DIR="$(dirname "$(readlink -f "$0")")"
docker compose -f "$DOCSMCP_DIR/docker-compose.yml" exec docsmcp python -m src.cli "$@"
WRAPPER
    
    chmod +x "$DOCSMCP_DIR/docsmcp"
    
    # Optionally add to PATH
    if [[ ":$PATH:" != *":$DOCSMCP_DIR:"* ]]; then
        echo ""
        log "Add to PATH? This allows running 'docsmcp' from anywhere. [Y/n]"
        # Read from /dev/tty to allow interactive input when piped
        read -r response </dev/tty
        if [[ ! "$response" =~ ^[Nn]$ ]]; then
            SHELL_RC=""
            if [[ -f "$HOME/.zshrc" ]]; then
                SHELL_RC="$HOME/.zshrc"
            elif [[ -f "$HOME/.bashrc" ]]; then
                SHELL_RC="$HOME/.bashrc"
            fi
            
            if [[ -n "$SHELL_RC" ]]; then
                echo "export PATH=\"\$PATH:$DOCSMCP_DIR\"" >> "$SHELL_RC"
                success "Added to $SHELL_RC (restart shell to apply)"
            fi
        fi
    fi
}

print_success() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              DocsMCP Installation Complete!               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Dashboard:  http://localhost:$DOCSMCP_PORT"
    echo "  API Docs:   http://localhost:$DOCSMCP_PORT/docs"
    echo "  MCP Endpoint: http://localhost:$DOCSMCP_PORT/mcp"
    echo ""
    echo "  Quick Start:"
    echo "    1. Open http://localhost:$DOCSMCP_PORT in your browser"
    echo "    2. Add your first documentation project"
    echo "    3. Configure your MCP client to use http://localhost:$DOCSMCP_PORT/mcp"
    echo ""
    echo "  CLI Commands:"
    echo "    $DOCSMCP_DIR/docsmcp add <name> <url>"
    echo "    $DOCSMCP_DIR/docsmcp scrape <name>"
    echo "    $DOCSMCP_DIR/docsmcp search <query>"
    echo ""
    
    if [[ "$DEV_MODE" == "1" ]]; then
        # Local Python mode instructions
        echo "  Local Python Mode:"
        echo \"    Start:      $DOCSMCP_DIR/docsmcp-start\"
        echo "    Stop:       $DOCSMCP_DIR/docsmcp-stop"
        echo "    Manual:     cd $DOCSMCP_DIR && source venv/bin/activate && python -m src.main"
        echo "    Status:     $DOCSMCP_DIR/docsmcp-status"
        echo "    Logs:       tail -f $DOCSMCP_DIR/docsmcp.log"
    else
        # Docker mode instructions  
        echo "  Docker Mode:"
        echo "    Start:      $DOCSMCP_DIR/docsmcp-start"
        echo "    Stop:       $DOCSMCP_DIR/docsmcp-stop"
        echo "    Status:     $DOCSMCP_DIR/docsmcp-status"
        echo "    Logs:       docker compose -f $DOCSMCP_DIR/docker-compose.yml logs -f"
    fi
    
    echo ""
    echo "  Uninstall:  rm -rf $DOCSMCP_DIR"
    echo ""
}

# Main
main() {
    print_banner
    check_prerequisites
    check_docker
    create_directories
    download_files
    configure
    start_service
    create_service_scripts
    create_cli_wrapper
    print_success
}

main "$@"
