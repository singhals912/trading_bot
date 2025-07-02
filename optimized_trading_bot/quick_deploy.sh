#!/bin/bash

# Quick Deploy - Upload optimized files and start new bot instance
# This script doesn't try to kill existing processes

set -e

# Configuration
AWS_HOST="54.91.93.69"
KEY_FILE="/Users/ss/Downloads/trading-bot-key.pem"
REMOTE_DIR="/home/ubuntu/trading_bot"
LOCAL_DIR="/Users/ss/Downloads/Code/trading_bot/optimized_trading_bot"

echo "🚀 Quick Deploy - Optimized Trading Bot"

# Create remote directory structure
echo "📁 Setting up remote directories..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "mkdir -p $REMOTE_DIR/{src,config,logs,data}"

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

# Upload requirements
rsync -avz -e "ssh -i $KEY_FILE" \
    "$LOCAL_DIR/requirements.txt" ubuntu@$AWS_HOST:$REMOTE_DIR/ || true

# Install dependencies
echo "📦 Installing dependencies..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd $REMOTE_DIR && pip install -r requirements.txt || pip3 install -r requirements.txt || true"

# Start new bot instance
echo "🚀 Starting optimized bot..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd $REMOTE_DIR && nohup python src/main.py --config config/production.yaml --paper-trading > logs/optimized_bot_$(date +%H%M%S).log 2>&1 &"

sleep 3

# Check status
BOT_COUNT=$(ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "pgrep -f 'python.*main.py' | wc -l")
echo "✅ Bot instances running: $BOT_COUNT"
echo "🌐 Dashboard: http://$AWS_HOST:8080"

echo ""
echo "🎉 Quick deployment completed!"
echo "📊 Monitor with: ./monitor_trading_performance.sh"