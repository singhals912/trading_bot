#!/bin/bash

# Deploy Optimized Trading Bot to AWS Docker Setup
set -e

# Configuration
AWS_HOST="54.91.93.69"
KEY_FILE="~/Downloads/trading-bot-key.pem"
REMOTE_DIR="/opt/trading_bot"
LOCAL_DIR="/Users/ss/Downloads/Code/trading_bot/optimized_trading_bot"

echo "🐳 Deploying Optimized Trading Bot to Docker..."

# Stop existing containers
echo "🛑 Stopping existing containers..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd $REMOTE_DIR && docker-compose down"

# Upload optimized files
echo "📤 Uploading optimized files..."

# Upload core application files
rsync -avz -e "ssh -i $KEY_FILE" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv/' \
    --exclude='logs/' \
    "$LOCAL_DIR/src/" ubuntu@$AWS_HOST:$REMOTE_DIR/src/

# Upload updated configuration
rsync -avz -e "ssh -i $KEY_FILE" \
    "$LOCAL_DIR/config/production.yaml" ubuntu@$AWS_HOST:$REMOTE_DIR/config/

# Rebuild and start containers
echo "🔄 Rebuilding and starting containers..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd $REMOTE_DIR && docker-compose build && docker-compose up -d"

# Wait for startup
sleep 10

# Check container status
echo "🔍 Checking container status..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd $REMOTE_DIR && docker-compose ps"

echo ""
echo "✅ Docker deployment completed!"
echo "🌐 Dashboard: http://$AWS_HOST:8080"
echo "📊 Monitor logs: ssh -i $KEY_FILE ubuntu@$AWS_HOST 'cd $REMOTE_DIR && docker-compose logs -f'"