"""File-based storage utilities for DocsMCP.

Handles project directories, JSON metadata, and document files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from config import settings


def projects_root() -> Path:
    """Get the root directory for all projects."""
    root = settings.projects_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_dir(project_id: str) -> Path:
    """Get the directory for a specific project."""
    return projects_root() / project_id


def config_path(project_id: str) -> Path:
    """Get the config.json path for a project."""
    return project_dir(project_id) / "config.json"


def docs_dir(project_id: str) -> Path:
    """Get the docs directory for a project."""
    return project_dir(project_id) / "docs"


def index_path(project_id: str) -> Path:
    """Get the index.json path for a project."""
    return project_dir(project_id) / "index.json"


def fts_db_path(project_id: str) -> Path:
    """Get the FTS database path for a project."""
    return project_dir(project_id) / "fts.db"


def vectors_path(project_id: str) -> Path:
    """Get the vector index path for a project."""
    return project_dir(project_id) / "vectors.index"


def read_json(path: Path) -> Dict[str, Any]:
    """Read a JSON file, returning empty dict if not exists."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write data to a JSON file, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def list_projects() -> list[str]:
    """List all project IDs."""
    root = projects_root()
    return [
        d.name for d in root.iterdir()
        if d.is_dir() and (d / "config.json").exists()
    ]


def project_exists(project_id: str) -> bool:
    """Check if a project exists."""
    return config_path(project_id).exists()


def delete_project(project_id: str) -> bool:
    """Delete a project and all its data."""
    proj_dir = project_dir(project_id)
    if not proj_dir.exists():
        return False
    
    import shutil
    shutil.rmtree(proj_dir)
    return True


def get_project_stats(project_id: str) -> Dict[str, Any]:
    """Get statistics for a project."""
    docs = docs_dir(project_id)
    if not docs.exists():
        return {"page_count": 0, "total_words": 0, "index_size_bytes": 0}
    
    page_count = 0
    total_words = 0
    index_size = 0
    
    for md_file in docs.glob("*.md"):
        page_count += 1
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            total_words += len(content.split())
        except IOError:
            pass
    
    fts_db = fts_db_path(project_id)
    if fts_db.exists():
        index_size += fts_db.stat().st_size
    
    vectors = vectors_path(project_id)
    if vectors.exists():
        index_size += vectors.stat().st_size
    
    return {
        "page_count": page_count,
        "total_words": total_words,
        "index_size_bytes": index_size,
    }


def read_document(project_id: str, doc_path: str) -> Optional[Dict[str, Any]]:
    """Read a document and its metadata."""
    full_path = docs_dir(project_id) / doc_path
    if not full_path.exists():
        return None
    
    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")
    except IOError:
        return None
    
    # Parse YAML frontmatter if present
    title = doc_path
    url = ""
    metadata = {}
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml
            try:
                fm = yaml.safe_load(parts[1])
                if fm:
                    title = fm.get("title", doc_path)
                    url = fm.get("url", "")
                    metadata = fm
                content = parts[2].strip()
            except Exception:
                pass
    
    # Fallback title extraction
    if title == doc_path:
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#"):
                title = line.lstrip("# ").strip()
                break
    
    return {
        "path": doc_path,
        "title": title,
        "url": url,
        "content": content,
        "metadata": metadata,
    }


def list_documents(project_id: str, page: int = 1, limit: int = 50) -> Dict[str, Any]:
    """List documents with pagination."""
    docs = docs_dir(project_id)
    if not docs.exists():
        return {"documents": [], "total": 0, "page": page, "limit": limit, "pages": 0}
    
    all_docs = sorted(docs.glob("*.md"))
    total = len(all_docs)
    pages = (total + limit - 1) // limit
    
    start = (page - 1) * limit
    end = start + limit
    page_docs = all_docs[start:end]
    
    documents = []
    for md_file in page_docs:
        doc = read_document(project_id, md_file.name)
        if doc:
            documents.append({
                "path": doc["path"],
                "title": doc["title"],
                "url": doc["url"],
                "word_count": len(doc["content"].split()),
                "scraped_at": doc["metadata"].get("scraped_at"),
            })
    
    return {
        "documents": documents,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }
