#!/usr/bin/env bash
#
# DocsMCP Uninstaller
# Safely removes DocsMCP and optionally its data
#

set -euo pipefail

DOCSMCP_DIR="${DOCSMCP_DIR:-$HOME/.docsmcp}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[Uninstall]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                  DocsMCP Uninstaller                      ║${NC}"
echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if installed
if [[ ! -d "$DOCSMCP_DIR" ]]; then
    error "DocsMCP not found at $DOCSMCP_DIR"
fi

# Confirm
warn "This will remove DocsMCP from $DOCSMCP_DIR"
echo ""
echo "Options:"
echo "  1) Remove everything (containers, data, configuration)"
echo "  2) Remove containers only (keep data)"
echo "  3) Cancel"
echo ""
read -p "Choice [1-3]: " choice

case "$choice" in
    1)
        REMOVE_DATA=1
        ;;
    2)
        REMOVE_DATA=0
        ;;
    *)
        log "Cancelled"
        exit 0
        ;;
esac

# Stop and remove containers
log "Stopping containers..."
cd "$DOCSMCP_DIR"
if docker compose ps -q 2>/dev/null | grep -q .; then
    docker compose down --volumes --remove-orphans 2>/dev/null || true
fi

# Remove Docker image
log "Removing Docker image..."
docker rmi docsmcp:latest 2>/dev/null || true

if [[ "$REMOVE_DATA" == "1" ]]; then
    # Offer backup
    warn "Create backup before removing data? [Y/n]"
    read -r response
    if [[ ! "$response" =~ ^[Nn]$ ]]; then
        if [[ -f "$DOCSMCP_DIR/scripts/backup.sh" ]]; then
            BACKUP_DIR="$HOME" "$DOCSMCP_DIR/scripts/backup.sh"
        fi
    fi
    
    # Remove directory
    log "Removing $DOCSMCP_DIR..."
    rm -rf "$DOCSMCP_DIR"
    
    # Remove from PATH if added
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ -f "$rc" ]] && grep -q "docsmcp" "$rc"; then
            log "Removing from $rc..."
            sed -i.bak '/docsmcp/d' "$rc"
        fi
    done
    
    success "DocsMCP completely removed"
else
    # Remove only containers/configs, keep data
    rm -f "$DOCSMCP_DIR/docker-compose.yml"
    rm -f "$DOCSMCP_DIR/docsmcp"
    rm -rf "$DOCSMCP_DIR/scripts"
    
    success "Containers removed, data preserved at $DOCSMCP_DIR/data"
fi

echo ""
log "Thank you for using DocsMCP!"
echo ""
