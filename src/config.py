"""Configuration management for DocsMCP.

Loads settings from environment variables with sensible defaults.
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Settings:
    """Application settings loaded from environment."""
    
    # Core
    api_token: str = field(default_factory=lambda: os.environ.get("API_TOKEN", ""))
    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8090")))
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("DATA_DIR", "./data")))
    
    # Search
    enable_vector_index: bool = field(default_factory=lambda: os.environ.get("ENABLE_VECTOR_INDEX", "0") == "1")
    search_results_limit: int = field(default_factory=lambda: int(os.environ.get("SEARCH_RESULTS_LIMIT", "10")))
    embedding_model: str = field(default_factory=lambda: os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    
    # Scraping
    max_pages_per_project: int = field(default_factory=lambda: int(os.environ.get("MAX_PAGES_PER_PROJECT", "10000")))
    rate_limit_delay: float = field(default_factory=lambda: float(os.environ.get("RATE_LIMIT_DELAY", "1.0")))
    respect_robots_txt: str = field(default_factory=lambda: os.environ.get("RESPECT_ROBOTS_TXT", "permissive"))
    user_agent: str = field(default_factory=lambda: os.environ.get("USER_AGENT", "DocsMCP/1.0"))
    request_timeout: int = field(default_factory=lambda: int(os.environ.get("REQUEST_TIMEOUT", "30")))
    max_concurrent_scrapes: int = field(default_factory=lambda: int(os.environ.get("MAX_CONCURRENT_SCRAPES", "3")))
    max_depth: int = field(default_factory=lambda: int(os.environ.get("MAX_DEPTH", "5")))
    
    # Webhooks
    webhook_url: Optional[str] = field(default_factory=lambda: os.environ.get("WEBHOOK_URL"))
    webhook_on_success: bool = field(default_factory=lambda: os.environ.get("WEBHOOK_ON_SUCCESS", "true").lower() == "true")
    webhook_on_error: bool = field(default_factory=lambda: os.environ.get("WEBHOOK_ON_ERROR", "true").lower() == "true")
    
    # Logging
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.environ.get("LOG_FORMAT", "text"))
    sentry_dsn: Optional[str] = field(default_factory=lambda: os.environ.get("SENTRY_DSN"))
    
    # Security
    allowed_origins: str = field(default_factory=lambda: os.environ.get("ALLOWED_ORIGINS", "*"))
    enable_auth: bool = field(default_factory=lambda: os.environ.get("ENABLE_AUTH", "true").lower() == "true")
    rate_limit_requests: int = field(default_factory=lambda: int(os.environ.get("RATE_LIMIT_REQUESTS", "100")))
    rate_limit_window: int = field(default_factory=lambda: int(os.environ.get("RATE_LIMIT_WINDOW", "60")))
    
    def __post_init__(self):
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def projects_dir(self) -> Path:
        """Get projects storage directory."""
        return self.data_dir / "projects"
    
    def validate(self) -> list[str]:
        """Validate settings and return list of errors."""
        errors = []
        
        if self.enable_auth and not self.api_token:
            errors.append("API_TOKEN is required when ENABLE_AUTH=true")
        
        if self.api_token and len(self.api_token) < 16:
            errors.append("API_TOKEN should be at least 16 characters for security")
        
        if self.port < 1 or self.port > 65535:
            errors.append(f"PORT must be 1-65535, got {self.port}")
        
        if self.rate_limit_delay < 0.1:
            errors.append(f"RATE_LIMIT_DELAY should be >= 0.1, got {self.rate_limit_delay}")
        
        if self.respect_robots_txt not in ("strict", "permissive", "ignore"):
            errors.append(f"RESPECT_ROBOTS_TXT must be strict/permissive/ignore, got {self.respect_robots_txt}")
        
        return errors


# Global settings instance
settings = Settings()


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)."""
    global settings
    settings = Settings()
    return settings
