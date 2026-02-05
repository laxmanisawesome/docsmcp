"""Async web scraper for documentation sites.

Crawls documentation websites, extracts content, and converts to Markdown.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from config import settings
from storage import config_path, docs_dir, index_path, read_json, write_json
from fts_indexer import build_fts_index


class ScrapeStats:
    """Scrape progress statistics."""
    
    def __init__(self):
        self.pages_fetched = 0
        self.pages_written = 0
        self.errors = 0
        self.progress = "Starting..."
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pagesFetched": self.pages_fetched,
            "pagesWritten": self.pages_written,
            "errors": self.errors,
            "progress": self.progress,
        }


async def scrape_project(
    project_id: str,
    base_url: str,
    *,
    max_depth: int = None,
    max_pages: int = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    clear_existing: bool = False,
    on_progress: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Crawl documentation site and store as Markdown.
    
    Args:
        project_id: Unique project identifier
        base_url: Starting URL for crawl
        max_depth: Maximum crawl depth (default from settings)
        max_pages: Maximum pages to scrape (default from settings)
        include: Regex pattern for URLs to include
        exclude: Regex pattern for URLs to exclude
        clear_existing: Delete existing docs before scraping
        on_progress: Callback for progress updates
    
    Returns:
        Dict with scrape statistics
    """
    max_depth = max_depth or settings.max_depth
    max_pages = max_pages or settings.max_pages_per_project
    
    include_re = re.compile(include) if include else None
    exclude_re = re.compile(exclude) if exclude else None
    
    # Clear existing docs if requested
    if clear_existing:
        docs_folder = docs_dir(project_id)
        if docs_folder.exists():
            for md_file in docs_folder.glob("*.md"):
                md_file.unlink()

    # Initialize config
    config = read_json(config_path(project_id))
    config.update({
        "status": "scraping",
        "startedAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat(),
    })
    write_json(config_path(project_id), config)

    stats = ScrapeStats()
    
    def update_progress(message: str) -> None:
        stats.progress = message
        config["stats"] = stats.to_dict()
        config["updatedAt"] = datetime.utcnow().isoformat()
        write_json(config_path(project_id), config)
        if on_progress:
            on_progress(message)

    try:
        await _crawl(
            project_id,
            base_url,
            max_depth=max_depth,
            max_pages=max_pages,
            include_re=include_re,
            exclude_re=exclude_re,
            stats=stats,
            on_progress=update_progress,
        )
        
        # Build search index
        update_progress("Building search index...")
        doc_count = build_fts_index(project_id)
        
        config.update({
            "status": "ready",
            "lastError": None,
            "completedAt": datetime.utcnow().isoformat(),
        })
        stats.progress = f"Complete: {stats.pages_written} pages indexed"
        
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        config.update({
            "status": "error",
            "lastError": tb,
        })
        stats.progress = f"Error: {exc}"
        
    finally:
        config["stats"] = stats.to_dict()
        config["updatedAt"] = datetime.utcnow().isoformat()
        write_json(config_path(project_id), config)
    
    return stats.to_dict()


async def _crawl(
    project_id: str,
    base_url: str,
    *,
    max_depth: int,
    max_pages: int,
    include_re: Optional[re.Pattern],
    exclude_re: Optional[re.Pattern],
    stats: ScrapeStats,
    on_progress: Callable[[str], None],
) -> None:
    """Internal crawl implementation."""
    
    parsed_base = urlparse(base_url)
    if not parsed_base.scheme.startswith("http"):
        raise ValueError("base_url must be http or https")
    
    host = parsed_base.netloc
    queue: deque[Tuple[str, int]] = deque([(base_url, 0)])
    visited: Set[str] = set()
    
    docs_folder = docs_dir(project_id)
    docs_folder.mkdir(parents=True, exist_ok=True)
    
    # Fetch robots.txt
    robots_parser = await _fetch_robots(parsed_base.scheme, host)
    
    async with httpx.AsyncClient(
        headers={"User-Agent": settings.user_agent},
        follow_redirects=True,
        timeout=settings.request_timeout,
    ) as client:
        
        while queue and stats.pages_fetched < max_pages:
            current_url, depth = queue.popleft()
            
            if current_url in visited:
                continue
            visited.add(current_url)
            
            if depth > max_depth:
                continue
            
            # Check robots.txt
            if robots_parser and not _check_robots(robots_parser, current_url):
                continue
            
            # Apply include/exclude patterns
            if include_re and not include_re.search(current_url):
                continue
            if exclude_re and exclude_re.search(current_url):
                continue
            
            on_progress(f"Fetching {stats.pages_fetched + 1}/{max_pages}: {current_url[:60]}...")
            
            try:
                response = await client.get(current_url)
                stats.pages_fetched += 1
                
                if response.status_code != 200:
                    stats.errors += 1
                    continue
                
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    continue
                
                html = response.text
                
                # Extract and save content
                saved = _process_page(project_id, current_url, html, docs_folder)
                if saved:
                    stats.pages_written += 1
                
                # Extract links for crawling
                if depth < max_depth:
                    links = _extract_links(html, current_url, host)
                    for link in links:
                        if link not in visited:
                            queue.append((link, depth + 1))
                
                # Rate limiting
                await asyncio.sleep(settings.rate_limit_delay)
                
            except Exception as e:
                stats.errors += 1
                continue


async def _fetch_robots(scheme: str, host: str) -> Optional[RobotFileParser]:
    """Fetch and parse robots.txt."""
    if settings.respect_robots_txt == "ignore":
        return None
    
    robots_url = f"{scheme}://{host}/robots.txt"
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        ) as client:
            response = await client.get(robots_url, timeout=5.0)
            if response.status_code == 200:
                rp = RobotFileParser()
                rp.parse(response.text.splitlines())
                return rp
    except Exception:
        pass
    return None


def _check_robots(robots_parser: RobotFileParser, url: str) -> bool:
    """Check if URL is allowed by robots.txt."""
    if settings.respect_robots_txt == "ignore":
        return True
    
    if settings.respect_robots_txt == "permissive":
        # Only respect crawl-delay, not disallow rules
        return True
    
    # Strict mode
    return robots_parser.can_fetch(settings.user_agent, url)


def _process_page(
    project_id: str,
    url: str,
    html: str,
    docs_folder,
) -> bool:
    """Extract content from HTML and save as Markdown."""
    
    # Try trafilatura first (best for article extraction)
    content = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )
    
    # Fallback to BeautifulSoup + markdownify
    if not content or len(content) < 100:
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove unwanted elements
        for tag in soup.find_all(["nav", "header", "footer", "aside", "script", "style"]):
            tag.decompose()
        
        # Try to find main content
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            content = md(str(main), strip=["script", "style"])
    
    if not content or len(content.strip()) < 50:
        return False
    
    # Extract title
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    if soup.title:
        title = soup.title.get_text().strip()
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text().strip()
    if not title:
        title = urlparse(url).path.split("/")[-1] or "Untitled"
    
    # Generate filename
    slug = _url_to_slug(url)
    filename = f"{slug}.md"
    
    # Create Markdown with YAML frontmatter
    frontmatter = f"""---
title: "{title.replace('"', "'")}"
url: "{url}"
scraped_at: "{datetime.utcnow().isoformat()}"
---

"""
    
    full_content = frontmatter + content.strip()
    
    # Save
    filepath = docs_folder / filename
    filepath.write_text(full_content, encoding="utf-8")
    
    return True


def _extract_links(html: str, base_url: str, host: str) -> List[str]:
    """Extract same-host links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        
        # Skip anchors, javascript, mailto, etc.
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        
        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        # Only same-host links
        if parsed.netloc != host:
            continue
        
        # Remove fragments
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
        
        # Skip common non-doc URLs
        skip_extensions = {".pdf", ".zip", ".tar", ".gz", ".exe", ".dmg", ".png", ".jpg", ".gif", ".svg"}
        if any(clean_url.lower().endswith(ext) for ext in skip_extensions):
            continue
        
        links.append(clean_url)
    
    return list(set(links))


def _url_to_slug(url: str) -> str:
    """Convert URL to filesystem-safe slug."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    
    if not path:
        path = "index"
    
    # Replace slashes and special chars
    slug = re.sub(r"[^\w\-]", "-", path)
    slug = re.sub(r"-+", "-", slug).strip("-")
    
    # Limit length and add hash for uniqueness
    if len(slug) > 80:
        hash_suffix = hashlib.md5(url.encode()).hexdigest()[:8]
        slug = slug[:70] + "-" + hash_suffix
    
    return slug or "page"
