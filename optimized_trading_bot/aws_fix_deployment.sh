#!/bin/bash
# AWS Trading Bot - Fix Deployment Issues
# This script fixes the common 4-5 hour shutdown issue

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🔧 AWS Trading Bot - Deployment Fix${NC}"
echo "============================================"

# Read deployment config if it exists
if [ -f "aws_deployment_config.txt" ]; then
    source aws_deployment_config.txt
    echo -e "${BLUE}📋 Using existing deployment config${NC}"
    echo "Instance: $INSTANCE_ID"
    echo "Public IP: $PUBLIC_IP"
else
    echo -e "${RED}❌ aws_deployment_config.txt not found${NC}"
    echo "Please run aws_deploy_automation.sh first"
    exit 1
fi

# Function to run commands on EC2
run_remote() {
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "$1"
}

# Function to copy files to EC2
copy_to_ec2() {
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no "$1" ubuntu@$PUBLIC_IP:"$2"
}

echo -e "${BLUE}📋 Step 1: Stopping existing containers...${NC}"
run_remote "cd /opt/trading_bot && docker-compose down || true"

echo -e "${BLUE}📋 Step 2: Copying optimized configuration...${NC}"
copy_to_ec2 "docker-compose.prod.yml" "/opt/trading_bot/docker-compose.yml"
copy_to_ec2 "Dockerfile" "/opt/trading_bot/Dockerfile"

# Create optimized environment file
echo -e "${BLUE}📋 Step 3: Creating optimized environment...${NC}"
cat > /tmp/.env.prod << 'EOF'
# Production Environment Variables
PAPER_TRADING=true
LOG_LEVEL=INFO
MAX_POSITIONS=2
DAILY_LOSS_LIMIT=0.02
POSITION_SIZE_PERCENT=0.05

# Memory optimization
MALLOC_ARENA_MAX=2
PYTHONOPTIMIZE=1
PYTHONUNBUFFERED=1

# API Keys (add your actual keys)
APCA_API_KEY_ID=your_alpaca_api_key
APCA_API_SECRET_KEY=your_alpaca_secret_key

# Optional - Add if you have them
EMAIL_SENDER=
EMAIL_PASSWORD=
EMAIL_RECIPIENT=
TWILIO_SID=
TWILIO_TOKEN=
TWILIO_FROM=
PHONE_NUMBER=
EOF

copy_to_ec2 "/tmp/.env.prod" "/opt/trading_bot/.env"

echo -e "${BLUE}📋 Step 4: Setting up system monitoring...${NC}"
cat > /tmp/setup_monitoring.sh << 'EOF'
#!/bin/bash
# Setup system monitoring and memory management

# Create swap file for memory relief
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize system for low memory
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Create monitoring scripts
mkdir -p ~/scripts

# Memory monitor script
cat > ~/scripts/memory_monitor.sh << 'SCRIPT'
#!/bin/bash
while true; do
    MEMORY_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
    if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
        echo "$(date): High memory usage: ${MEMORY_USAGE}%" >> ~/logs/memory.log
        # Restart containers if memory too high
        if (( $(echo "$MEMORY_USAGE > 95" | bc -l) )); then
            echo "$(date): Critical memory usage, restarting containers" >> ~/logs/memory.log
            cd /opt/trading_bot && docker-compose restart trading-bot
        fi
    fi
    sleep 60
done
SCRIPT

chmod +x ~/scripts/memory_monitor.sh

# Health check script
cat > ~/scripts/health_check.sh << 'SCRIPT'
#!/bin/bash
cd /opt/trading_bot

# Check if trading bot container is running
if ! docker-compose ps trading-bot | grep -q "Up"; then
    echo "$(date): Trading bot container down, restarting..." >> ~/logs/health.log
    docker-compose up -d trading-bot
fi

# Check if dashboard is accessible
if ! curl -s -f http://localhost:8080/health > /dev/null; then
    echo "$(date): Dashboard not accessible, restarting container..." >> ~/logs/health.log
    docker-compose restart trading-bot
fi

# Check log file size and rotate if needed
if [ -f logs/algo_trading.log ] && [ $(stat -f%z logs/algo_trading.log 2>/dev/null || stat -c%s logs/algo_trading.log 2>/dev/null) -gt 52428800 ]; then
    mv logs/algo_trading.log logs/algo_trading.log.old
    touch logs/algo_trading.log
fi
SCRIPT

chmod +x ~/scripts/health_check.sh

# Create systemd service for monitoring
sudo tee /etc/systemd/system/trading-bot-monitor.service > /dev/null << 'SERVICE'
[Unit]
Description=Trading Bot Memory Monitor
After=docker.service

[Service]
Type=simple
User=ubuntu
ExecStart=/home/ubuntu/scripts/memory_monitor.sh
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
SERVICE

# Create cron jobs
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/scripts/health_check.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 */6 * * * cd /opt/trading_bot && docker system prune -f") | crontab -

# Create log directories
mkdir -p ~/logs /opt/trading_bot/logs

# Enable and start monitoring service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot-monitor.service
sudo systemctl start trading-bot-monitor.service

echo "System monitoring setup complete"
EOF

copy_to_ec2 "/tmp/setup_monitoring.sh" "/home/ubuntu/setup_monitoring.sh"
run_remote "chmod +x /home/ubuntu/setup_monitoring.sh && /home/ubuntu/setup_monitoring.sh"

echo -e "${BLUE}📋 Step 5: Starting optimized trading bot...${NC}"
run_remote "cd /opt/trading_bot && docker-compose up -d"

echo -e "${BLUE}📋 Step 6: Waiting for services to start...${NC}"
sleep 30

# Verify deployment
echo -e "${BLUE}📋 Step 7: Verifying deployment...${NC}"
if run_remote "curl -s http://localhost:8080/health" > /dev/null; then
    echo -e "${GREEN}✅ Trading bot is running successfully${NC}"
else
    echo -e "${YELLOW}⚠️ Dashboard not yet accessible, checking container status...${NC}"
    run_remote "cd /opt/trading_bot && docker-compose ps"
fi

# Clean up temp files
rm -f /tmp/.env.prod /tmp/setup_monitoring.sh

echo ""
echo "============================================"
echo -e "${GREEN}🎉 Deployment Fix Complete!${NC}"
echo "============================================"
echo -e "${BLUE}Key Improvements:${NC}"
echo "  ✅ Memory limits set (512MB for bot)"
echo "  ✅ Swap file created (1GB)"
echo "  ✅ Auto-restart policies enabled"
echo "  ✅ Memory monitoring active"
echo "  ✅ Health checks every 5 minutes"
echo "  ✅ Log rotation enabled"
echo ""
echo -e "${BLUE}Monitoring:${NC}"
echo "  Dashboard: http://$PUBLIC_IP:8080"
echo "  Logs: ssh -i $KEY_FILE ubuntu@$PUBLIC_IP 'tail -f /opt/trading_bot/logs/algo_trading.log'"
echo "  Memory: ssh -i $KEY_FILE ubuntu@$PUBLIC_IP 'tail -f ~/logs/memory.log'"
echo "  Health: ssh -i $KEY_FILE ubuntu@$PUBLIC_IP 'tail -f ~/logs/health.log'"
echo ""
echo -e "${GREEN}The bot should now run continuously without the 4-5 hour shutdown issue!${NC}"