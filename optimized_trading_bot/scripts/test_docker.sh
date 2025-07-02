#!/bin/bash

# Quick Docker test script
# Tests if the Dockerfile can build successfully

set -e

echo "🧪 Testing Docker build capability..."

# Test if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not available"
    exit 1
fi

echo "✅ Docker is available"

# Test if we can build just the builder stage (faster test)
echo "🔨 Testing builder stage..."
docker build --target builder -t trading-bot-test:builder -f docker/Dockerfile . > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Builder stage builds successfully"
    echo "🧹 Cleaning up test image..."
    docker rmi trading-bot-test:builder > /dev/null 2>&1 || true
    echo "✅ Docker build test passed!"
else
    echo "❌ Builder stage failed to build"
    echo "💡 Common issues:"
    echo "   - ta-lib compilation problems"
    echo "   - Missing system dependencies"
    echo "   - Network connectivity issues"
    exit 1
fi