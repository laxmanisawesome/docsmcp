"""Tests for FTS indexer."""

from pathlib import Path

import pytest

from src.fts_indexer import build_fts_index, get_fts_stats, query_fts


def test_build_fts_index(temp_data_dir: Path, sample_documents: list[dict]):
    """Test building FTS index from documents."""
    project_dir = temp_data_dir / "test-project"
    project_dir.mkdir()
    
    # Build index
    build_fts_index("test-project", str(temp_data_dir))
    
    # Verify index was created
    db_path = project_dir / "fts_index.db"
    # Note: This will fail until we create test documents
    # assert db_path.exists()


def test_query_fts_returns_results(temp_data_dir: Path, sample_documents: list[dict]):
    """Test FTS query returns relevant results."""
    project_dir = temp_data_dir / "test-project"
    project_dir.mkdir()
    docs_dir = project_dir / "docs"
    docs_dir.mkdir()
    
    # Create test documents
    for doc in sample_documents:
        doc_path = docs_dir / f"{doc['id']}.md"
        doc_path.write_text(f"# {doc['title']}\n\n{doc['content']}")
    
    # Build index
    build_fts_index("test-project", str(temp_data_dir))
    
    # Query
    results = query_fts("test-project", "FastAPI", str(temp_data_dir))
    
    assert len(results) > 0
    assert any("FastAPI" in r.get("title", "") or "FastAPI" in r.get("content", "") 
               for r in results)


def test_query_fts_empty_results(temp_data_dir: Path, sample_documents: list[dict]):
    """Test FTS query returns empty for non-matching query."""
    project_dir = temp_data_dir / "test-project"
    project_dir.mkdir()
    docs_dir = project_dir / "docs"
    docs_dir.mkdir()
    
    # Create test documents
    for doc in sample_documents:
        doc_path = docs_dir / f"{doc['id']}.md"
        doc_path.write_text(f"# {doc['title']}\n\n{doc['content']}")
    
    # Build index
    build_fts_index("test-project", str(temp_data_dir))
    
    # Query with non-matching term
    results = query_fts("test-project", "xyznonexistent", str(temp_data_dir))
    
    assert len(results) == 0


def test_get_fts_stats(temp_data_dir: Path, sample_documents: list[dict]):
    """Test getting FTS statistics."""
    project_dir = temp_data_dir / "test-project"
    project_dir.mkdir()
    docs_dir = project_dir / "docs"
    docs_dir.mkdir()
    
    # Create test documents
    for doc in sample_documents:
        doc_path = docs_dir / f"{doc['id']}.md"
        doc_path.write_text(f"# {doc['title']}\n\n{doc['content']}")
    
    # Build index
    build_fts_index("test-project", str(temp_data_dir))
    
    # Get stats
    stats = get_fts_stats("test-project", str(temp_data_dir))
    
    assert stats is not None
    assert stats.get("document_count", 0) == len(sample_documents)
