"""Optional vector search indexer using local embeddings.

Only loaded when ENABLE_VECTOR_INDEX=1. Requires:
- sentence-transformers
- faiss-cpu

Install with: pip install -r requirements-vector.txt
"""
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

from storage import project_dir, docs_dir


def _vectors_path(project_id: str) -> Path:
    return project_dir(project_id) / "vectors.index"


def _mappings_path(project_id: str) -> Path:
    return project_dir(project_id) / "vectors.pkl"


# Lazy-load heavy dependencies
_model = None
_faiss = None


def _load_dependencies():
    """Lazy-load sentence-transformers and faiss."""
    global _model, _faiss
    
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            
            model_name = os.environ.get(
                "EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            _model = SentenceTransformer(model_name)
            _faiss = faiss
        except ImportError as e:
            raise ImportError(
                "Vector search requires sentence-transformers and faiss-cpu. "
                "Install with: pip install -r requirements-vector.txt"
            ) from e
    
    return _model, _faiss


def build_vector_index(project_id: str) -> int:
    """Build FAISS vector index for a project.
    
    Returns the number of documents indexed.
    """
    model, faiss = _load_dependencies()
    
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
        
        # Parse metadata
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
                    text = parts[2]
                except Exception:
                    pass
        
        if not title:
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("#"):
                    title = s.lstrip("# ").strip()
                    break
        
        if not title:
            title = md.stem
        
        docs.append({
            "path": md.name,
            "title": title,
            "url": url,
            "content": text[:8000],  # Limit content length for embedding
        })

    if not docs:
        return 0

    # Generate embeddings
    texts = [f"{d['title']}\n{d['content'][:2000]}" for d in docs]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    
    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product (cosine sim with normalized vectors)
    
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    # Save index and mappings
    vectors_path = _vectors_path(project_id)
    mappings_path = _mappings_path(project_id)
    
    faiss.write_index(index, str(vectors_path))
    with open(mappings_path, "wb") as f:
        pickle.dump(docs, f)

    return len(docs)


def query_vectors(
    project_id: str,
    query: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """Query the vector index.
    
    Returns list of results with title, path, url, snippet, and score.
    """
    model, faiss = _load_dependencies()
    
    vectors_path = _vectors_path(project_id)
    mappings_path = _mappings_path(project_id)
    
    if not vectors_path.exists() or not mappings_path.exists():
        return []

    # Load index and mappings
    index = faiss.read_index(str(vectors_path))
    with open(mappings_path, "rb") as f:
        docs = pickle.load(f)

    # Generate query embedding
    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    
    # Search
    scores, indices = index.search(query_embedding, min(top_k, len(docs)))
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        
        doc = docs[idx]
        
        # Generate snippet from content
        content = doc["content"]
        snippet = content[:200].replace("\n", " ").strip()
        if len(content) > 200:
            snippet += "..."
        
        results.append({
            "path": doc["path"],
            "title": doc["title"],
            "url": doc["url"],
            "snippet": snippet,
            "score": float(score),
        })
    
    return results


def delete_vector_index(project_id: str) -> bool:
    """Delete the vector index for a project."""
    vectors_path = _vectors_path(project_id)
    mappings_path = _mappings_path(project_id)
    
    deleted = False
    if vectors_path.exists():
        vectors_path.unlink()
        deleted = True
    if mappings_path.exists():
        mappings_path.unlink()
        deleted = True
    
    return deleted


def get_vector_stats(project_id: str) -> Dict[str, Any]:
    """Get statistics about the vector index."""
    vectors_path = _vectors_path(project_id)
    mappings_path = _mappings_path(project_id)
    
    if not vectors_path.exists():
        return {"exists": False, "document_count": 0, "size_bytes": 0}
    
    size = vectors_path.stat().st_size
    if mappings_path.exists():
        size += mappings_path.stat().st_size
    
    doc_count = 0
    if mappings_path.exists():
        try:
            with open(mappings_path, "rb") as f:
                docs = pickle.load(f)
                doc_count = len(docs)
        except Exception:
            pass
    
    return {
        "exists": True,
        "document_count": doc_count,
        "size_bytes": size,
    }
