# Trading Bot Dockerfile for AWS Deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create trading user
RUN groupadd -r trading && useradd -r -g trading -d /app -s /bin/bash trading

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/
COPY config/ /app/config/
COPY *.py /app/
COPY *.md /app/
COPY *.json /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/data/historical /app/data/ml_models /app/data/news \
    /app/data/economic /app/data/fundamental /app/data/realtime

# Set permissions
RUN chown -R trading:trading /app
RUN chmod -R 755 /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

# Switch to trading user
USER trading

# Expose ports
EXPOSE 8080 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "src/main.py", "--paper"]