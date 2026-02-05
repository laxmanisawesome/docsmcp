# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

LABEL org.opencontainers.image.title="DocsMCP"
LABEL org.opencontainers.image.description="Self-hosted documentation search with MCP support"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/laxmanisawesome/docsmcp"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Create non-root user
RUN groupadd -r docsmcp && useradd -r -g docsmcp docsmcp

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY src/ ./src/

# Create data directory
RUN mkdir -p /app/data && chown -R docsmcp:docsmcp /app

# Switch to non-root user
USER docsmcp

# Environment defaults
ENV HOST=0.0.0.0
ENV PORT=8090
ENV DATA_DIR=/app/data
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Entry point
WORKDIR /app/src
CMD ["python", "main.py"]
