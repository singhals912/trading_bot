#!/bin/bash

# Docker build script for the trading bot
# Usage: ./scripts/docker_build.sh [target] [tag]
# Example: ./scripts/docker_build.sh development latest

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="optimized-trading-bot"
DOCKERFILE_PATH="$PROJECT_ROOT/docker/Dockerfile"

# Default values
TARGET="${1:-production}"
TAG="${2:-latest}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION="2.0.0"

# Get git commit hash if available
if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    VCS_REF=$(git rev-parse --short HEAD)
else
    VCS_REF="unknown"
fi

echo "🐳 Building Docker image for trading bot..."
echo "📦 Target: $TARGET"
echo "🏷️  Tag: $TAG"
echo "📅 Build Date: $BUILD_DATE"
echo "🔖 Version: $VERSION"
echo "📝 Git Ref: $VCS_REF"
echo "🔧 Note: Using simplified build (ta-lib optional for compatibility)"
echo ""

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Build the Docker image
docker build \
    --target "$TARGET" \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg VERSION="$VERSION" \
    --build-arg VCS_REF="$VCS_REF" \
    -t "$IMAGE_NAME:$TAG" \
    -t "$IMAGE_NAME:$TARGET-$TAG" \
    -f "$DOCKERFILE_PATH" \
    .

echo ""
echo "✅ Docker image built successfully!"
echo "📷 Image: $IMAGE_NAME:$TAG"
echo ""
echo "🚀 To run the container:"
echo "   docker run -d -p 8080:8080 --name trading-bot $IMAGE_NAME:$TAG"
echo ""
echo "🌐 To access dashboard:"
echo "   http://localhost:8080"
echo ""
echo "📊 To run with docker-compose:"
echo "   cd docker && docker-compose up -d"
echo ""

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Copy .env.example to .env and configure your API keys:"
    echo "   cp .env.example .env"
    echo ""
fi