# Multi-stage Dockerfile for ViraLearn ContentBot
# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements files
COPY requirements/requirements.txt requirements/requirements-dev.txt ./requirements/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements/requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create application directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY run_integrated_system.py ./
COPY requirements/ ./requirements/

# Create necessary directories
RUN mkdir -p logs data uploads temp && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Default command
CMD ["python", "run_integrated_system.py", "serve", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM production as development

# Switch back to root to install dev dependencies
USER root

# Install development dependencies
RUN pip install -r requirements/requirements-dev.txt

# Install additional development tools
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy development files
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY docs/ ./docs/
COPY .env.example ./

# Set development environment
ENV ENVIRONMENT=development \
    DEBUG=true \
    LOG_LEVEL=DEBUG

# Create development directories
RUN mkdir -p .pytest_cache coverage_reports && \
    chown -R appuser:appuser /app

# Switch back to non-root user
USER appuser

# Development command with auto-reload
CMD ["python", "run_integrated_system.py", "serve", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Testing stage
FROM development as testing

# Run tests by default
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html:coverage_reports/", "--cov-report=term"]

# Production-optimized stage
FROM production as production-optimized

# Install additional production optimizations
USER root
RUN pip install gunicorn uvloop httptools

# Create gunicorn configuration
RUN echo 'bind = "0.0.0.0:8000"' > gunicorn.conf.py && \
    echo 'workers = 4' >> gunicorn.conf.py && \
    echo 'worker_class = "uvicorn.workers.UvicornWorker"' >> gunicorn.conf.py && \
    echo 'worker_connections = 1000' >> gunicorn.conf.py && \
    echo 'max_requests = 1000' >> gunicorn.conf.py && \
    echo 'max_requests_jitter = 100' >> gunicorn.conf.py && \
    echo 'timeout = 30' >> gunicorn.conf.py && \
    echo 'keepalive = 2' >> gunicorn.conf.py && \
    echo 'preload_app = True' >> gunicorn.conf.py && \
    chown appuser:appuser gunicorn.conf.py

USER appuser

# Production command with Gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "run_integrated_system:app"]

# Labels for metadata
LABEL maintainer="ViraLearn Team" \
      version="1.0.0" \
      description="ViraLearn ContentBot - AI-powered content generation platform" \
      org.opencontainers.image.source="https://github.com/viralearn/contentbot" \
      org.opencontainers.image.documentation="https://docs.viralearn.com/contentbot" \
      org.opencontainers.image.licenses="MIT"