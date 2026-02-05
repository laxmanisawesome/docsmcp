# Contributing to DocsMCP

Thank you for your interest in contributing to DocsMCP! This document provides guidelines and information for contributors.

**Maintainer:** [@laxmanisawesome](https://github.com/laxmanisawesome) • [laxtothemax@proton.me](mailto:laxtothemax@proton.me)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Be kind, be helpful, and assume good intentions.

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/laxmanisawesome/docsmcp/issues) to avoid duplicates
2. Use the bug report template
3. Include:
   - DocsMCP version
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

### Suggesting Features

1. Check existing issues and discussions
2. Open a new issue with the feature request template
3. Describe the use case and proposed solution
4. Be open to discussion and alternatives

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Add/update tests
5. Update documentation
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- Docker (optional, for testing)

### Local Development

```bash
# Clone your fork
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run the development server
python -m src.main
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scraper.py

# Run with verbose output
pytest -v
```

### Code Style

We use the following tools for code quality:

- **Ruff**: Linting and formatting
- **Black**: Code formatting (via Ruff)
- **MyPy**: Type checking

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type check
mypy src/
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

## Project Structure

```
docsmcp/
├── src/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── cli.py           # CLI commands
│   ├── config.py        # Configuration
│   ├── models.py        # Pydantic models
│   ├── scraper.py       # Web scraping
│   ├── storage.py       # File storage
│   ├── fts_indexer.py   # Full-text search
│   ├── indexer.py       # Vector search
│   ├── mcp_server.py    # MCP handlers
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS, JS
├── tests/
│   ├── conftest.py      # Pytest fixtures
│   ├── test_scraper.py
│   ├── test_fts.py
│   └── test_api.py
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── examples/            # Example configs
```

## Writing Tests

### Test Guidelines

1. Test one thing per test function
2. Use descriptive test names
3. Use fixtures for common setup
4. Mock external services

### Example Test

```python
import pytest
from src.fts_indexer import build_fts_index, query_fts

@pytest.fixture
def sample_docs():
    return [
        {"id": "1", "content": "FastAPI is a modern web framework"},
        {"id": "2", "content": "Python is a programming language"},
    ]

def test_fts_returns_relevant_results(sample_docs, tmp_path):
    # Build index
    db_path = tmp_path / "test.db"
    build_fts_index(sample_docs, str(db_path))
    
    # Query
    results = query_fts("FastAPI", str(db_path))
    
    # Assert
    assert len(results) == 1
    assert results[0]["id"] == "1"
```

## Documentation

### Updating Docs

- Documentation is in `docs/` directory
- Use Markdown format
- Include code examples
- Update relevant docs with code changes

### Building Docs Locally

```bash
# Preview documentation
mkdocs serve
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a pull request
4. After merge, tag the release
5. GitHub Actions will publish to PyPI

## Getting Help

- Open an issue for bugs or features
- Start a discussion for questions
- Check existing documentation

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- README acknowledgments

Thank you for contributing!
