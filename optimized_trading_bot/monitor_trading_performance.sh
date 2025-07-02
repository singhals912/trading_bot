#!/bin/bash

# Monitor Trading Bot Performance
# This script provides real-time monitoring of the optimized trading bot

# Configuration
AWS_HOST="54.91.93.69"
KEY_FILE="/Users/ss/Downloads/trading-bot-key.pem"
REMOTE_DIR="/home/ubuntu/trading_bot"

echo "📊 Trading Bot Performance Monitor"
echo "=================================="

# Function to get bot status
get_bot_status() {
    ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "pgrep -f 'python.*main.py' | wc -l" 2>/dev/null
}

# Function to get dashboard data
get_dashboard_data() {
    ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "cat $REMOTE_DIR/dashboard.json 2>/dev/null | tail -20"
}

# Function to get recent trades
get_recent_trades() {
    ssh -i "$KEY_KEY" ubuntu@$AWS_HOST "tail -20 $REMOTE_DIR/logs/trades.log 2>/dev/null"
}

# Function to get signal activity
get_signal_activity() {
    ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "grep -E 'signal|Signal' $REMOTE_DIR/logs/trading_bot.log | tail -10 2>/dev/null"
}

# Function to get error count
get_error_count() {
    ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "grep -c ERROR $REMOTE_DIR/logs/trading_bot.log 2>/dev/null || echo 0"
}

# Main monitoring loop
while true; do
    clear
    echo "📊 Trading Bot Performance Monitor - $(date)"
    echo "=============================================="
    
    # Bot Status
    BOT_RUNNING=$(get_bot_status)
    if [ "$BOT_RUNNING" -gt 0 ]; then
        echo "🟢 Bot Status: RUNNING"
    else
        echo "🔴 Bot Status: STOPPED"
    fi
    
    # Dashboard URL
    echo "🌐 Dashboard: http://$AWS_HOST:8080"
    echo ""
    
    # Recent Dashboard Data
    echo "📈 Latest Performance Data:"
    echo "----------------------------"
    DASHBOARD_DATA=$(get_dashboard_data)
    if [ -n "$DASHBOARD_DATA" ]; then
        echo "$DASHBOARD_DATA" | grep -E '"timestamp"|"daily_pnl"|"positions"|"total_trades"|"performance_metrics"' | head -10
    else
        echo "No dashboard data available"
    fi
    echo ""
    
    # Signal Activity (last 5 signals)
    echo "🎯 Recent Signal Activity:"
    echo "--------------------------"
    SIGNALS=$(get_signal_activity)
    if [ -n "$SIGNALS" ]; then
        echo "$SIGNALS"
    else
        echo "No recent signal activity"
    fi
    echo ""
    
    # Error Count
    ERROR_COUNT=$(get_error_count)
    echo "⚠️  Error Count Today: $ERROR_COUNT"
    echo ""
    
    # Real-time log tail (last 5 lines)
    echo "📋 Live Log (last 5 lines):"
    echo "----------------------------"
    ssh -i "$KEY_FILE" ubuntu@$AWS_HOST "tail -5 $REMOTE_DIR/logs/trading_bot.log 2>/dev/null" || echo "Log file not accessible"
    
    echo ""
    echo "🔄 Refreshing in 30 seconds... (Ctrl+C to exit)"
    echo "💡 Tip: The bot should generate more signals with relaxed parameters"
    
    # Wait 30 seconds before refresh
    sleep 30
done