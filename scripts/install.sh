#!/usr/bin/env bash
#
# DocsMCP One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/yourusername/docsmcp/main/scripts/install.sh | bash
#
# Options (via environment variables):
#   DOCSMCP_DIR     Installation directory (default: ~/.docsmcp)
#   DOCSMCP_PORT    Server port (default: 8090)
#   SKIP_DOCKER     Skip Docker installation (set to 1)
#   DEV_MODE        Install from source for development (set to 1)
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
REPO_URL="https://github.com/yourusername/docsmcp"

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
        warn "Docker not found. Install Docker? [Y/n]"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            error "Docker is required. Install manually or set SKIP_DOCKER=1"
        fi
        install_docker
    fi
    
    if ! docker info &>/dev/null; then
        error "Docker daemon is not running. Please start Docker and try again."
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
    
    mkdir -p "$DOCSMCP_DIR"/{data,logs,config}
    
    success "Created $DOCSMCP_DIR"
}

download_files() {
    log "Downloading DocsMCP..."
    
    cd "$DOCSMCP_DIR"
    
    if [[ "$DEV_MODE" == "1" ]]; then
        # Clone repository for development
        if [[ -d ".git" ]]; then
            git pull origin main
        else
            git clone "$REPO_URL.git" .
        fi
        success "Repository cloned"
    else
        # Download docker-compose and env files only
        $DOWNLOADER "$REPO_URL/raw/main/docker-compose.yml" > docker-compose.yml
        
        if [[ ! -f ".env" ]]; then
            $DOWNLOADER "$REPO_URL/raw/main/.env.example" > .env
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
        pip install -q -r requirements.txt
        
        warn "Development mode: Run 'source $DOCSMCP_DIR/venv/bin/activate && python -m src.main' to start"
    else
        # Production mode - use Docker
        docker compose pull
        docker compose up -d
        
        # Wait for service to be ready
        log "Waiting for service to start..."
        for i in {1..30}; do
            if curl -sf "http://localhost:$DOCSMCP_PORT/health" &>/dev/null; then
                success "DocsMCP is running!"
                break
            fi
            sleep 1
        done
    fi
}

create_cli_wrapper() {
    log "Creating CLI wrapper..."
    
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
        read -r response
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
    echo "  Logs:       docker compose -f $DOCSMCP_DIR/docker-compose.yml logs -f"
    echo "  Stop:       docker compose -f $DOCSMCP_DIR/docker-compose.yml down"
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
    create_cli_wrapper
    print_success
}

main "$@"
