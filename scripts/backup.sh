#!/usr/bin/env bash
#
# DocsMCP Backup Script
# Creates timestamped backups of all data
#
# Usage:
#   ./backup.sh                    # Full backup
#   ./backup.sh --projects-only    # Backup only project data
#   ./backup.sh --restore <file>   # Restore from backup
#

set -euo pipefail

# Configuration
DOCSMCP_DIR="${DOCSMCP_DIR:-$(dirname "$(dirname "$(readlink -f "$0")")")}"
BACKUP_DIR="${BACKUP_DIR:-$DOCSMCP_DIR/backups}"
MAX_BACKUPS="${MAX_BACKUPS:-10}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[Backup]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

show_help() {
    cat << EOF
DocsMCP Backup Utility

Usage: $0 [OPTIONS]

Options:
    -h, --help          Show this help message
    -p, --projects-only Backup only project data (no logs)
    -r, --restore FILE  Restore from a backup file
    -l, --list          List available backups
    -d, --dir DIR       Custom backup directory
    --no-compress       Don't compress the backup

Environment Variables:
    DOCSMCP_DIR     DocsMCP installation directory
    BACKUP_DIR      Backup storage directory
    MAX_BACKUPS     Maximum number of backups to keep (default: 10)

Examples:
    $0                          # Create full backup
    $0 --projects-only          # Backup projects only
    $0 --restore backup.tar.gz  # Restore from backup
    $0 --list                   # Show available backups
EOF
}

list_backups() {
    log "Available backups in $BACKUP_DIR:"
    echo ""
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warn "No backups found"
        return
    fi
    
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | while read -r line; do
        file=$(echo "$line" | awk '{print $NF}')
        size=$(echo "$line" | awk '{print $5}')
        date=$(echo "$line" | awk '{print $6, $7, $8}')
        name=$(basename "$file")
        echo "  $name ($size) - $date"
    done || warn "No backups found"
}

create_backup() {
    local projects_only="${1:-0}"
    local compress="${2:-1}"
    
    log "Creating backup..."
    
    # Ensure backup directory exists
    mkdir -p "$BACKUP_DIR"
    
    # Determine what to backup
    local backup_paths=()
    local backup_name="docsmcp_backup_$TIMESTAMP"
    
    if [[ "$projects_only" == "1" ]]; then
        backup_paths+=("$DOCSMCP_DIR/data/projects")
        backup_name="docsmcp_projects_$TIMESTAMP"
    else
        backup_paths+=("$DOCSMCP_DIR/data")
        [[ -f "$DOCSMCP_DIR/.env" ]] && backup_paths+=("$DOCSMCP_DIR/.env")
        [[ -f "$DOCSMCP_DIR/docker-compose.yml" ]] && backup_paths+=("$DOCSMCP_DIR/docker-compose.yml")
    fi
    
    # Check if paths exist
    local existing_paths=()
    for path in "${backup_paths[@]}"; do
        if [[ -e "$path" ]]; then
            existing_paths+=("$path")
        else
            warn "Skipping non-existent path: $path"
        fi
    done
    
    if [[ ${#existing_paths[@]} -eq 0 ]]; then
        error "No data to backup"
    fi
    
    # Create backup
    local backup_file
    if [[ "$compress" == "1" ]]; then
        backup_file="$BACKUP_DIR/$backup_name.tar.gz"
        tar -czf "$backup_file" -C "$(dirname "$DOCSMCP_DIR")" "${existing_paths[@]/#$DOCSMCP_DIR\//$(basename "$DOCSMCP_DIR")/}"
    else
        backup_file="$BACKUP_DIR/$backup_name.tar"
        tar -cf "$backup_file" -C "$(dirname "$DOCSMCP_DIR")" "${existing_paths[@]/#$DOCSMCP_DIR\//$(basename "$DOCSMCP_DIR")/}"
    fi
    
    # Calculate size
    local size
    size=$(du -h "$backup_file" | cut -f1)
    
    success "Backup created: $backup_file ($size)"
    
    # Cleanup old backups
    cleanup_old_backups
    
    echo "$backup_file"
}

cleanup_old_backups() {
    log "Cleaning up old backups (keeping last $MAX_BACKUPS)..."
    
    local count
    count=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
    
    if [[ $count -gt $MAX_BACKUPS ]]; then
        local to_delete=$((count - MAX_BACKUPS))
        ls -1t "$BACKUP_DIR"/*.tar.gz | tail -n "$to_delete" | while read -r file; do
            rm -f "$file"
            log "Deleted old backup: $(basename "$file")"
        done
    fi
}

restore_backup() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        # Check if it's a relative path in backup dir
        if [[ -f "$BACKUP_DIR/$backup_file" ]]; then
            backup_file="$BACKUP_DIR/$backup_file"
        else
            error "Backup file not found: $backup_file"
        fi
    fi
    
    log "Restoring from $backup_file..."
    
    # Confirm
    warn "This will overwrite existing data. Continue? [y/N]"
    # Read from /dev/tty so prompt works when script is piped
    read -r response </dev/tty
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Restore cancelled"
        exit 0
    fi
    
    # Stop service if running
    if docker compose -f "$DOCSMCP_DIR/docker-compose.yml" ps -q 2>/dev/null | grep -q .; then
        log "Stopping DocsMCP service..."
        docker compose -f "$DOCSMCP_DIR/docker-compose.yml" down
    fi
    
    # Create backup of current state
    log "Creating backup of current state before restore..."
    create_backup 0 1 > /dev/null
    
    # Extract backup
    log "Extracting backup..."
    tar -xzf "$backup_file" -C "$(dirname "$DOCSMCP_DIR")"
    
    success "Restore complete!"
    
    # Restart service
    log "Restarting DocsMCP service..."
    docker compose -f "$DOCSMCP_DIR/docker-compose.yml" up -d
    
    success "Service restarted"
}

# Parse arguments
PROJECTS_ONLY=0
COMPRESS=1
RESTORE_FILE=""
ACTION="backup"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--projects-only)
            PROJECTS_ONLY=1
            shift
            ;;
        -r|--restore)
            ACTION="restore"
            RESTORE_FILE="$2"
            shift 2
            ;;
        -l|--list)
            ACTION="list"
            shift
            ;;
        -d|--dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --no-compress)
            COMPRESS=0
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Execute action
case "$ACTION" in
    backup)
        create_backup "$PROJECTS_ONLY" "$COMPRESS"
        ;;
    restore)
        restore_backup "$RESTORE_FILE"
        ;;
    list)
        list_backups
        ;;
esac
