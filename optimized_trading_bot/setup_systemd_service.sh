#!/bin/bash

# SystemD Service Setup for Trading Bot on OCI
# Run this after deploying the code to /opt/trading_bot

set -e

echo "⚙️ Setting up SystemD service for trading bot..."

# Create systemd service file
sudo tee /etc/systemd/system/tradingbot.service > /dev/null << 'EOF'
[Unit]
Description=Algorithmic Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tradingbot
Group=tradingbot
WorkingDirectory=/opt/trading_bot
Environment=PATH=/opt/trading_bot/venv/bin
ExecStart=/opt/trading_bot/venv/bin/python start_bot_remote_monitoring.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/trading_bot/logs/systemd.log
StandardError=append:/opt/trading_bot/logs/systemd_error.log

# Resource limits
MemoryMax=2G
CPUQuota=80%

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/trading_bot

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "🚀 Enabling trading bot service..."
sudo systemctl enable tradingbot.service

echo "📊 Creating monitoring script..."
sudo tee /usr/local/bin/check_tradingbot.sh > /dev/null << 'EOF'
#!/bin/bash

# Trading Bot Health Check Script

echo "🤖 Trading Bot Status Report"
echo "============================"
echo "Date: $(date)"
echo ""

# Service status
echo "📊 Service Status:"
sudo systemctl status tradingbot.service --no-pager -l
echo ""

# Process info
echo "🔍 Process Information:"
ps aux | grep -E "(python|trading)" | grep -v grep || echo "No trading processes found"
echo ""

# Resource usage
echo "💾 Resource Usage:"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo ""

# Recent logs
echo "📝 Recent Logs (last 20 lines):"
tail -20 /opt/trading_bot/logs/systemd.log 2>/dev/null || echo "No systemd logs found"
echo ""

# Bot state
echo "🎯 Bot State:"
if [ -f /opt/trading_bot/bot_state.json ]; then
    cat /opt/trading_bot/bot_state.json | python3 -m json.tool 2>/dev/null || cat /opt/trading_bot/bot_state.json
else
    echo "No bot state file found"
fi
EOF

chmod +x /usr/local/bin/check_tradingbot.sh

echo "⏰ Setting up monitoring cron job..."
(crontab -l 2>/dev/null || echo "") | grep -v check_tradingbot || {
    (crontab -l 2>/dev/null || echo ""; echo "*/5 * * * * /usr/local/bin/check_tradingbot.sh >> /opt/trading_bot/logs/health_check.log 2>&1") | crontab -
}

echo "🔥 Creating firewall rules for dashboard access..."
# Allow SSH (port 22) and dashboard (port 8080)
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw --force enable

echo "✅ SystemD service setup complete!"
echo ""
echo "🎮 Service Management Commands:"
echo "  Start:   sudo systemctl start tradingbot"
echo "  Stop:    sudo systemctl stop tradingbot"
echo "  Restart: sudo systemctl restart tradingbot"
echo "  Status:  sudo systemctl status tradingbot"
echo "  Logs:    sudo journalctl -u tradingbot -f"
echo ""
echo "📊 Monitoring Commands:"
echo "  Health:  /usr/local/bin/check_tradingbot.sh"
echo "  Logs:    tail -f /opt/trading_bot/logs/systemd.log"
echo ""
echo "🌐 Dashboard Access:"
echo "  URL: http://$(curl -s ifconfig.me):8080"
echo "  Local: http://localhost:8080"
echo ""