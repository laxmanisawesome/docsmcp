# Changelog

All notable changes to DocsMCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2024-12-19

### Added
- Unified service management commands (`docsmcp-start`, `docsmcp-stop`, `docsmcp-status`)
- PID-based process management for local Python installations
- Proper service scripts for both Docker and local Python modes
- Status checking with health endpoint validation and service URLs
- Dedicated log files for local Python mode (`docsmcp.log`)

### Fixed
- Critical bash syntax errors in installer script (lines 337-338)
- Orphaned code blocks causing installation failures
- Broken function definitions in installer
- Service management inconsistencies between Docker and local modes
- Missing graceful shutdown procedures

### Improved
- Unified command interface for both Docker and local Python installations
- Better process isolation with PID file management
- Enhanced service status reporting with emoji indicators
- Cleaner installation output with proper service management instructions
- More robust service detection and cleanup procedures

### Changed
- Replaced manual start/stop scripts with unified management commands
- Standardized service management across installation modes
- Updated documentation to reflect new unified command structure

### Added
- Enhanced web dashboard with complete project management interface
- MCP configuration generator for Claude Desktop, VS Code, and custom clients
- Interactive project details modal with document browser
- Comprehensive installation testing and validation
- Service management scripts for local Python installations  
- Docker prerequisite guidance in installation docs

### Improved
- Local Python mode now includes automatic service testing and validation
- Installation script provides working localhost URL immediately after setup
- Better error handling and diagnostic logging during installation
- Start/stop scripts created automatically for local installations
- Enhanced documentation with service management instructions

### Fixed
- macOS bash compatibility issues in installer script
- Git clone conflicts during installation
- Template path resolution in web interface
- Python 3.9 compatibility for Union type annotations
- Missing health endpoint usage in installation testing

### Changed
- Documentation: updated repository links to https://github.com/laxmanisawesome/docsmcp and added maintainer contact ([@laxmanisawesome](https://github.com/laxmanisawesome), laxtothemax@proton.me)

### Added
- Initial open-source release

## [1.0.0] - 2024-XX-XX

### Added
- Web scraper with robots.txt support
- SQLite FTS5 full-text search (default)
- Optional vector search with sentence-transformers + FAISS
- MCP JSON-RPC endpoint for AI assistants
- REST API for programmatic access
- Clean web dashboard (no gradients, minimal design)
- CLI for command-line management
- Docker support with one-line installation
- Configuration via environment variables
- Backup and restore scripts
- Comprehensive documentation

### Security
- Non-root Docker container
- Rate limiting support
- Input validation

## Future Roadmap

### [1.1.0] - Planned
- [ ] Scheduled re-scraping
- [ ] Webhook notifications
- [ ] Basic authentication for dashboard
- [ ] Export to different formats (JSON, PDF)

### [1.2.0] - Planned
- [ ] Multi-user support
- [ ] Project sharing
- [ ] Custom scraping rules
- [ ] Plugin system for custom extractors

### [2.0.0] - Planned
- [ ] Distributed scraping
- [ ] Cloud sync option
- [ ] Team collaboration features
- [ ] Advanced analytics

---

## Versioning

- **MAJOR**: Breaking changes to API or configuration
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, security updates
