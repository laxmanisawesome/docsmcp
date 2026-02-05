"""SQLite FTS5 search indexer.

Creates a lightweight full-text search index using only Python's stdlib sqlite3.
Perfect for low-resource environments where vector search is overkill.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from storage import project_dir, docs_dir, fts_db_path


def build_fts_index(project_id: str) -> int:
    """Build FTS5 index for a project.
    
    Returns the number of documents indexed.
    """
    db_path = fts_db_path(project_id)
    docs_folder = docs_dir(project_id)
    
    if not docs_folder.exists():
        return 0

    # Collect documents
    docs = []
    for md in sorted(docs_folder.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        
        # Parse YAML frontmatter for metadata
        title = None
        url = ""
        
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                import yaml
                try:
                    fm = yaml.safe_load(parts[1])
                    if fm:
                        title = fm.get("title")
                        url = fm.get("url", "")
                except Exception:
                    pass
        
        # Fallback title extraction from first heading
        if not title:
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("#"):
                    title = s.lstrip("# ").strip()
                    break
        
        if not title:
            title = md.stem
        
        docs.append((md.name, title, url, text))

    # Build/replace FTS DB
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        
        # Drop and recreate table for clean rebuild
        cur.execute("DROP TABLE IF EXISTS docs_fts")
        
        # Create FTS table (path and url are unindexed - stored only for reference)
        cur.execute("""
            CREATE VIRTUAL TABLE docs_fts USING fts5(
                path UNINDEXED,
                title,
                url UNINDEXED,
                content,
                tokenize='porter unicode61'
            )
        """)
        
        cur.executemany(
            "INSERT INTO docs_fts (path, title, url, content) VALUES (?, ?, ?, ?)",
            docs
        )
        conn.commit()
    finally:
        conn.close()

    return len(docs)


def query_fts(
    project_id: str,
    query: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """Query the FTS index.
    
    Returns list of results with title, path, url, snippet, and score.
    """
    db_path = fts_db_path(project_id)
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        
        # Sanitize query for FTS
        q = query.replace('"', ' ').replace("'", " ").strip()
        if not q:
            return []
        
        # Use MATCH with bm25 ranking
        sql = """
            SELECT 
                path,
                title,
                url,
                snippet(docs_fts, 3, '<mark>', '</mark>', '...', 64) as snippet,
                bm25(docs_fts) as score
            FROM docs_fts 
            WHERE docs_fts MATCH ?
            ORDER BY score
            LIMIT ?
        """
        
        cur.execute(sql, (q, top_k))
        rows = cur.fetchall()
        
        results = []
        for path, title, url, snippet, score in rows:
            results.append({
                "path": path,
                "title": title,
                "url": url,
                "snippet": snippet,
                "score": abs(score),  # bm25 returns negative values
            })
        
        return results
    finally:
        conn.close()


def delete_fts_index(project_id: str) -> bool:
    """Delete the FTS index for a project."""
    db_path = fts_db_path(project_id)
    if db_path.exists():
        db_path.unlink()
        return True
    return False


def get_fts_stats(project_id: str) -> Dict[str, Any]:
    """Get statistics about the FTS index."""
    db_path = fts_db_path(project_id)
    if not db_path.exists():
        return {"exists": False, "document_count": 0, "size_bytes": 0}
    
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM docs_fts")
        count = cur.fetchone()[0]
        
        return {
            "exists": True,
            "document_count": count,
            "size_bytes": db_path.stat().st_size,
        }
    except Exception:
        return {"exists": True, "document_count": 0, "size_bytes": db_path.stat().st_size}
    finally:
        conn.close()
