# Changelog

All notable changes to DocsMCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
