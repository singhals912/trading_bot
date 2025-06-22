#!/bin/bash

# Fixed status script - properly reads files instead of interfering with bot
echo "=== TRADING BOT STATUS CHECK ==="
echo "Current Time: $(date)"
echo ""

# Check if bot process is running
echo "📊 BOT PROCESS:"
BOT_PID=$(pgrep -f "python.*main.py" 2>/dev/null)
if [ ! -z "$BOT_PID" ]; then
    echo "✅ Bot is running (PID: $BOT_PID)"
    echo "   Memory usage: $(ps -o rss= -p $BOT_PID 2>/dev/null | awk '{print int($1/1024)" MB"}' || echo 'N/A')"
    echo "   CPU usage: $(ps -o %cpu= -p $BOT_PID 2>/dev/null | awk '{print $1"%"}' || echo 'N/A')"
else
    echo "❌ Bot is NOT running"
fi
echo ""

# Check dashboard file
echo "📈 LATEST DASHBOARD:"
if [ -f "dashboard.json" ]; then
    DASHBOARD_AGE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" dashboard.json 2>/dev/null || stat -c "%y" dashboard.json 2>/dev/null || echo "unknown")
    echo "✅ Dashboard exists (updated: $DASHBOARD_AGE)"
    
    # Extract key metrics safely
    if command -v python3 >/dev/null 2>&1; then
        DAILY_PNL=$(python3 -c "
import json, sys
try:
    with open('dashboard.json', 'r') as f:
        data = json.load(f)
    print(f\"\${data.get('daily_pnl', 0):.2f}\")
except:
    print('N/A')
" 2>/dev/null)
        
        POSITIONS=$(python3 -c "
import json, sys
try:
    with open('dashboard.json', 'r') as f:
        data = json.load(f)
    print(data.get('positions', 0))
except:
    print('N/A')
" 2>/dev/null)
        
        EQUITY=$(python3 -c "
import json, sys
try:
    with open('dashboard.json', 'r') as f:
        data = json.load(f)
    print(f\"\${data.get('equity', 0):,.2f}\")
except:
    print('N/A')
" 2>/dev/null)
        
        echo "   Daily P&L: $DAILY_PNL"
        echo "   Active Positions: $POSITIONS"
        echo "   Total Equity: $EQUITY"
    else
        echo "   (Python not available for parsing)"
    fi
else
    echo "❌ No dashboard.json found"
fi
echo ""

# Check bot state
echo "💾 BOT STATE:"
if [ -f "bot_state.json" ]; then
    STATE_AGE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" bot_state.json 2>/dev/null || stat -c "%y" bot_state.json 2>/dev/null || echo "unknown")
    echo "✅ Bot state exists (updated: $STATE_AGE)"
else
    echo "❌ No bot_state.json found"
fi
echo ""

# Check recent log activity (last 5 minutes only)
echo "📝 RECENT LOG ACTIVITY (last 5 minutes):"
if [ -f "logs/algo_trading.log" ]; then
    # Get logs from last 5 minutes
    RECENT_LOGS=$(tail -50 logs/algo_trading.log | grep "$(date -v-5M '+%Y-%m-%d %H:%M' 2>/dev/null || date -d '5 minutes ago' '+%Y-%m-%d %H:%M' 2>/dev/null || date '+%Y-%m-%d %H:%M')")
    
    if [ ! -z "$RECENT_LOGS" ]; then
        echo "✅ Recent activity detected:"
        echo "$RECENT_LOGS" | tail -3 | sed 's/^/   /'
    else
        echo "⚠️ No activity in last 5 minutes"
        echo "   Last log entry:"
        tail -1 logs/algo_trading.log | sed 's/^/   /'
    fi
else
    echo "❌ No main log file found"
fi
echo ""

# Check for errors (today only)
echo "🚨 ERROR CHECK:"
if [ -f "logs/errors.log" ]; then
    TODAY=$(date '+%Y-%m-%d')
    TODAY_ERRORS=$(grep "$TODAY" logs/errors.log 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$TODAY_ERRORS" -eq 0 ]; then
        echo "✅ No errors logged today"
    else
        echo "⚠️ $TODAY_ERRORS errors logged today"
        echo "   Most recent error:"
        grep "$TODAY" logs/errors.log | tail -1 | sed 's/^/   /'
    fi
else
    echo "✅ No error log found"
fi
echo ""

# Market session check
echo "🕐 MARKET SESSION:"
HOUR=$(date '+%H' | sed 's/^0//')
if [ $HOUR -ge 4 ] && [ $HOUR -lt 9 ]; then
    echo "🌅 Pre-market session (4:00-9:30 AM ET)"
elif [ $HOUR -ge 9 ] && [ $HOUR -lt 16 ]; then
    echo "📈 Regular market hours (9:30 AM-4:00 PM ET)"
elif [ $HOUR -ge 16 ] && [ $HOUR -lt 20 ]; then
    echo "🌆 After-hours session (4:00-8:00 PM ET)"
else
    echo "🌙 Market closed"
fi
echo ""

# Quick file system check
echo "💽 SYSTEM CHECK:"
DISK_USAGE=$(df . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "⚠️ Disk usage high: ${DISK_USAGE}%"
else
    echo "✅ Disk usage: ${DISK_USAGE}%"
fi

# Check if files are being updated
DASHBOARD_MINS_OLD="unknown"
if [ -f "dashboard.json" ]; then
    if command -v stat >/dev/null 2>&1; then
        DASHBOARD_MINS_OLD=$(echo "($(date +%s) - $(stat -f %m dashboard.json 2>/dev/null || stat -c %Y dashboard.json 2>/dev/null || echo 0)) / 60" | bc 2>/dev/null || echo "unknown")
    fi
fi

if [ "$DASHBOARD_MINS_OLD" != "unknown" ] && [ "$DASHBOARD_MINS_OLD" -gt 15 ]; then
    echo "⚠️ Dashboard last updated $DASHBOARD_MINS_OLD minutes ago"
else
    echo "✅ Files being updated regularly"
fi

echo ""
echo "=== END STATUS CHECK ==="