#!/bin/bash

# Deploy Optimized Trading Bot to AWS
# This script uploads the optimized bot files and restarts the service

set -e

# Configuration
AWS_HOST="54.91.93.69"
KEY_FILE="/Users/ss/Downloads/trading-bot-key.pem"
REMOTE_DIR="/home/ubuntu/trading_bot"
LOCAL_DIR="/Users/ss/Downloads/Code/trading_bot/optimized_trading_bot"

echo "🚀 Deploying Optimized Trading Bot to AWS..."

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found: $KEY_FILE"
    echo "🔍 Looking for key files in Downloads..."
    ls -la /Users/ss/Downloads/*key*.pem 2>/dev/null || echo "No .pem files found"
    exit 1
fi

echo "✅ Key file found: $KEY_FILE"

# Stop existing bot
echo "🛑 Stopping existing trading bot..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "sudo pkill -f 'python.*main.py' || pkill -f 'python.*main.py' || true"
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "sudo pkill -f 'python.*enhanced_trading_bot' || pkill -f 'python.*enhanced_trading_bot' || true"
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "sudo pkill -f 'trading' || pkill -f 'trading' || true"

# Wait a moment for processes to stop
sleep 3

# Check if any trading processes are still running
REMAINING_PROCESSES=$(ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "pgrep -f 'python.*' | wc -l" 2>/dev/null || echo "0")
if [ "$REMAINING_PROCESSES" -gt 0 ]; then
    echo "⚠️  Some processes still running, but continuing deployment..."
fi

# Create backup of current deployment
echo "💾 Creating backup..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd /home/ubuntu && tar -czf trading_bot_backup_$(date +%Y%m%d_%H%M%S).tar.gz trading_bot/ || true"

# Upload optimized files
echo "📤 Uploading optimized bot files..."

# Upload core application files
rsync -avz -e "ssh -i $KEY_FILE" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv/' \
    --exclude='logs/' \
    --exclude='data/cache/' \
    "$LOCAL_DIR/src/" ubuntu@$AWS_HOST:$REMOTE_DIR/src/

# Upload updated configuration
rsync -avz -e "ssh -i $KEY_FILE" \
    "$LOCAL_DIR/config/production.yaml" ubuntu@$AWS_HOST:$REMOTE_DIR/config/

# Upload requirements if changed
rsync -avz -e "ssh -i $KEY_FILE" \
    "$LOCAL_DIR/requirements.txt" ubuntu@$AWS_HOST:$REMOTE_DIR/

# Upload main entry point
rsync -avz -e "ssh -i $KEY_FILE" \
    "$LOCAL_DIR/src/main.py" ubuntu@$AWS_HOST:$REMOTE_DIR/

# Install/update dependencies
echo "📦 Installing dependencies..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd $REMOTE_DIR && pip install -r requirements.txt"

# Create logs directory if it doesn't exist
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "mkdir -p $REMOTE_DIR/logs"

# Set environment variables for paper trading
echo "⚙️ Setting up environment..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "echo 'export PAPER_TRADING=true' >> ~/.bashrc"

# Start the optimized bot
echo "🚀 Starting optimized trading bot..."
ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cd $REMOTE_DIR && nohup python src/main.py --config config/production.yaml --paper-trading > logs/bot_startup.log 2>&1 &"

# Wait a moment for startup
sleep 5

# Check if bot started successfully
echo "🔍 Checking bot status..."
BOT_STATUS=$(ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "pgrep -f 'python.*main.py' | wc -l")

if [ "$BOT_STATUS" -gt 0 ]; then
    echo "✅ Trading bot started successfully!"
    echo "🌐 Dashboard should be available at: http://$AWS_HOST:8080"
    echo "📊 Monitor logs with: ssh -i $KEY_FILE ubuntu@$AWS_HOST 'tail -f $REMOTE_DIR/logs/trading_bot.log'"
    
    # Show last few log lines
    echo ""
    echo "📋 Recent log entries:"
    ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "tail -10 $REMOTE_DIR/logs/bot_startup.log"
    
else
    echo "❌ Failed to start trading bot. Check logs:"
    ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "tail -20 $REMOTE_DIR/logs/bot_startup.log"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "📈 The optimized bot should start trading with relaxed parameters"
echo "🔄 Monitor for 1-2 hours to see trading activity"
echo ""
echo "Useful commands:"
echo "  Monitor live: ssh -i $KEY_FILE ubuntu@$AWS_HOST 'tail -f $REMOTE_DIR/logs/trading_bot.log'"
echo "  Check status: ssh -i $KEY_FILE ubuntu@$AWS_HOST 'pgrep -f python.*main.py'"
echo "  Dashboard: http://$AWS_HOST:8080"