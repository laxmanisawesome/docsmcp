"""DocsMCP Command Line Interface.

Provides commands for managing documentation projects.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from storage import (
    list_projects, project_exists, read_json, write_json,
    config_path, delete_project, get_project_stats, docs_dir,
)
from scraper import scrape_project
from fts_indexer import query_fts, build_fts_index, get_fts_stats


@click.group()
@click.version_option(version="1.0.0", prog_name="docsmcp")
def cli():
    """DocsMCP - Self-hosted documentation search with MCP support."""
    pass


@cli.command()
@click.argument("project_id")
@click.argument("base_url")
@click.option("--max-depth", "-d", default=5, help="Maximum crawl depth")
@click.option("--max-pages", "-p", default=1000, help="Maximum pages to scrape")
@click.option("--include", "-i", help="Regex pattern for URLs to include")
@click.option("--exclude", "-e", help="Regex pattern for URLs to exclude")
@click.option("--scrape/--no-scrape", default=True, help="Start scraping immediately")
def add(
    project_id: str,
    base_url: str,
    max_depth: int,
    max_pages: int,
    include: Optional[str],
    exclude: Optional[str],
    scrape: bool,
):
    """Add a new documentation project.
    
    Example:
        docsmcp add react https://react.dev/reference
    """
    if project_exists(project_id):
        click.echo(f"Error: Project '{project_id}' already exists.", err=True)
        sys.exit(1)
    
    from datetime import datetime
    
    config = {
        "id": project_id,
        "baseUrl": base_url,
        "config": {
            "max_depth": max_depth,
            "max_pages": max_pages,
        },
        "status": "created",
        "createdAt": datetime.utcnow().isoformat(),
    }
    
    if include:
        config["config"]["include_patterns"] = [include]
    if exclude:
        config["config"]["exclude_patterns"] = [exclude]
    
    write_json(config_path(project_id), config)
    click.echo(f"✓ Created project '{project_id}'")
    
    if scrape:
        click.echo(f"Starting scrape...")
        asyncio.run(_scrape_project(project_id))


@cli.command("scrape")
@click.argument("project_id")
@click.option("--full", is_flag=True, help="Clear existing docs and rescrape")
def scrape_cmd(project_id: str, full: bool):
    """Start or restart scraping for a project.
    
    Example:
        docsmcp scrape react
        docsmcp scrape react --full
    """
    if not project_exists(project_id):
        click.echo(f"Error: Project '{project_id}' not found.", err=True)
        sys.exit(1)
    
    asyncio.run(_scrape_project(project_id, clear_existing=full))


async def _scrape_project(project_id: str, clear_existing: bool = False):
    """Run scrape with progress output."""
    config = read_json(config_path(project_id))
    cfg = config.get("config", {})
    
    def on_progress(msg: str):
        click.echo(f"  {msg}")
    
    result = await scrape_project(
        project_id,
        config["baseUrl"],
        max_depth=cfg.get("max_depth", 5),
        max_pages=cfg.get("max_pages", 1000),
        include=cfg.get("include_patterns", [None])[0] if cfg.get("include_patterns") else None,
        exclude=cfg.get("exclude_patterns", [None])[0] if cfg.get("exclude_patterns") else None,
        clear_existing=clear_existing,
        on_progress=on_progress,
    )
    
    click.echo(f"✓ Scrape complete: {result['pagesWritten']} pages written, {result['errors']} errors")


@cli.command("search")
@click.argument("query")
@click.option("--project", "-p", help="Search specific project")
@click.option("--limit", "-l", default=5, help="Maximum results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_cmd(query: str, project: Optional[str], limit: int, as_json: bool):
    """Search documentation.
    
    Examples:
        docsmcp search "useState hook"
        docsmcp search "error handling" -p python
    """
    project_ids = [project] if project else list_projects()
    
    if project and not project_exists(project):
        click.echo(f"Error: Project '{project}' not found.", err=True)
        sys.exit(1)
    
    all_results = []
    for pid in project_ids:
        try:
            results = query_fts(pid, query, limit)
            for r in results:
                r["project"] = pid
            all_results.extend(results)
        except Exception:
            continue
    
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    all_results = all_results[:limit]
    
    if as_json:
        click.echo(json.dumps(all_results, indent=2))
    else:
        if not all_results:
            click.echo("No results found.")
        else:
            for i, r in enumerate(all_results, 1):
                click.echo(f"\n{i}. {r['title']}")
                click.echo(f"   Project: {r['project']}")
                click.echo(f"   URL: {r.get('url', 'N/A')}")
                snippet = r.get('snippet', '').replace('<mark>', '').replace('</mark>', '')
                click.echo(f"   {snippet[:100]}...")


@cli.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_cmd(as_json: bool):
    """List all projects."""
    projects = []
    for project_id in list_projects():
        config = read_json(config_path(project_id))
        stats = get_project_stats(project_id)
        projects.append({
            "id": project_id,
            "base_url": config.get("baseUrl", ""),
            "status": config.get("status", "unknown"),
            "pages": stats["page_count"],
        })
    
    if as_json:
        click.echo(json.dumps(projects, indent=2))
    else:
        if not projects:
            click.echo("No projects found. Add one with: docsmcp add <id> <url>")
        else:
            click.echo(f"{'ID':<20} {'Status':<12} {'Pages':<8} URL")
            click.echo("-" * 80)
            for p in projects:
                click.echo(f"{p['id']:<20} {p['status']:<12} {p['pages']:<8} {p['base_url'][:35]}")


@cli.command()
@click.argument("project_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(project_id: str, as_json: bool):
    """Get project status and statistics."""
    if not project_exists(project_id):
        click.echo(f"Error: Project '{project_id}' not found.", err=True)
        sys.exit(1)
    
    config = read_json(config_path(project_id))
    stats = get_project_stats(project_id)
    fts_stats = get_fts_stats(project_id)
    
    data = {
        "id": project_id,
        "base_url": config.get("baseUrl", ""),
        "status": config.get("status", "unknown"),
        "stats": stats,
        "fts": fts_stats,
        "last_error": config.get("lastError"),
    }
    
    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Project: {project_id}")
        click.echo(f"URL: {data['base_url']}")
        click.echo(f"Status: {data['status']}")
        click.echo(f"Pages: {stats['page_count']}")
        click.echo(f"Words: {stats['total_words']:,}")
        click.echo(f"Index size: {stats['index_size_bytes']:,} bytes")
        if fts_stats['exists']:
            click.echo(f"FTS indexed: {fts_stats['document_count']} documents")
        if data.get("last_error"):
            click.echo(f"Last error: {data['last_error'][:200]}...")


@cli.command()
@click.argument("project_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def delete(project_id: str, force: bool):
    """Delete a project and all its data."""
    if not project_exists(project_id):
        click.echo(f"Error: Project '{project_id}' not found.", err=True)
        sys.exit(1)
    
    stats = get_project_stats(project_id)
    
    if not force:
        click.confirm(
            f"Delete project '{project_id}' ({stats['page_count']} pages)?",
            abort=True
        )
    
    delete_project(project_id)
    click.echo(f"✓ Deleted project '{project_id}'")


@cli.command()
@click.argument("project_id")
@click.argument("output_dir", type=click.Path())
def export(project_id: str, output_dir: str):
    """Export project data to a directory.
    
    Example:
        docsmcp export react ./backup/react/
    """
    if not project_exists(project_id):
        click.echo(f"Error: Project '{project_id}' not found.", err=True)
        sys.exit(1)
    
    import shutil
    from storage import project_dir
    
    src = project_dir(project_id)
    dst = Path(output_dir)
    
    if dst.exists():
        click.confirm(f"Overwrite existing '{output_dir}'?", abort=True)
        shutil.rmtree(dst)
    
    shutil.copytree(src, dst)
    click.echo(f"✓ Exported project '{project_id}' to {output_dir}")


@cli.command()
@click.argument("project_id")
def index(project_id: str):
    """Rebuild search index for a project."""
    if not project_exists(project_id):
        click.echo(f"Error: Project '{project_id}' not found.", err=True)
        sys.exit(1)
    
    click.echo(f"Building FTS index for '{project_id}'...")
    count = build_fts_index(project_id)
    click.echo(f"✓ Indexed {count} documents")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8090, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the DocsMCP server."""
    import uvicorn
    
    click.echo(f"Starting DocsMCP server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command("config")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_config(as_json: bool):
    """Show current configuration."""
    config = {
        "data_dir": str(settings.data_dir),
        "port": settings.port,
        "enable_auth": settings.enable_auth,
        "enable_vector_index": settings.enable_vector_index,
        "max_pages_per_project": settings.max_pages_per_project,
        "rate_limit_delay": settings.rate_limit_delay,
    }
    
    if as_json:
        click.echo(json.dumps(config, indent=2))
    else:
        for k, v in config.items():
            click.echo(f"{k}: {v}")


if __name__ == "__main__":
    cli()
