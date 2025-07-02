# Simplified Dockerfile without ta-lib compilation issues
# Uses conda or pre-built packages to avoid compilation

FROM python:3.11-slim AS base

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Add metadata
LABEL maintainer="Trading Bot Team" \
      version="${VERSION}" \
      description="Optimized Trading Bot - Simple Build" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements but exclude ta-lib temporarily
COPY requirements.txt /tmp/requirements.txt

# Create requirements without ta-lib for now
RUN grep -v "ta-lib" /tmp/requirements.txt > /tmp/requirements_no_talib.txt

# Install all dependencies except ta-lib
RUN pip install --no-cache-dir -r /tmp/requirements_no_talib.txt

# Try to install ta-lib using conda-forge (more reliable)
RUN pip install --no-cache-dir \
    --find-links https://download.lfd.uci.edu/pythonlibs/archived/ \
    --trusted-host download.lfd.uci.edu \
    --no-deps \
    TA-Lib || echo "ta-lib installation failed, continuing without it"

# Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r trading && useradd -r -g trading -d /app -s /bin/bash trading

# Copy virtual environment
COPY --from=base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=trading:trading src/ /app/src/
COPY --chown=trading:trading config/ /app/config/
COPY --chown=trading:trading scripts/ /app/scripts/
COPY --chown=trading:trading .env.example /app/.env

# Create directories
RUN mkdir -p /app/logs /app/data && \
    chown -R trading:trading /app

# Set environment variables
ENV PYTHONPATH="/app/src:/app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

# Switch to non-root user
USER trading

# Expose dashboard port
EXPOSE 8080

# Default command
CMD ["python", "src/main.py", "--paper-trading"]

# Development stage
FROM production AS development

USER root

# Install development tools
RUN pip install \
    pytest \
    black \
    flake8 \
    ipython

USER trading

CMD ["python", "src/main.py", "--paper-trading"]