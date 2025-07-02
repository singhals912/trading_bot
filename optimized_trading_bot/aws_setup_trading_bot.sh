#!/bin/bash

# AWS Trading Bot Setup Script
# This script sets up the trading bot on the AWS EC2 instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Trading Bot on AWS EC2${NC}"
echo "================================================="

# Read configuration
if [ ! -f "aws_deployment_config.txt" ]; then
    echo -e "${RED}❌ Configuration file not found. Run aws_deploy_automation.sh first.${NC}"
    exit 1
fi

source aws_deployment_config.txt

echo -e "${BLUE}📋 Configuration loaded:${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  SSH Key: $KEY_FILE"

# Step 1: Test SSH connection
echo -e "${BLUE}📋 Step 1: Testing SSH connection...${NC}"
if ! ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "echo 'SSH connection successful'" &> /dev/null; then
    echo -e "${RED}❌ SSH connection failed. Please check your instance.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Step 2: Copy project files to AWS
echo -e "${BLUE}📋 Step 2: Copying project files to AWS...${NC}"

# Create exclusion file for rsync
cat > /tmp/rsync_exclude << 'EOF'
venv/
logs/
__pycache__/
*.pyc
.git/
.DS_Store
*.log
data/historical/
node_modules/
.env.local
EOF

rsync -avz -e "ssh -i $KEY_FILE -o StrictHostKeyChecking=no" \
    --exclude-from=/tmp/rsync_exclude \
    --progress \
    ./ ubuntu@$PUBLIC_IP:/opt/trading_bot/

echo -e "${GREEN}✅ Project files copied successfully${NC}"

# Step 3: Set up environment and permissions
echo -e "${BLUE}📋 Step 3: Setting up environment and permissions...${NC}"

ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << 'EOF'
    # Set ownership
    sudo chown -R ubuntu:ubuntu /opt/trading_bot/
    
    # Make scripts executable
    chmod +x /opt/trading_bot/*.sh
    
    # Create .env file with correct permissions
    cat > /opt/trading_bot/.env << 'ENVFILE'
APCA_API_KEY_ID=PK6Y4XBDRDJHJ8ZKF81B
APCA_API_SECRET_KEY=s9Yw8MdroJlbR4eKA8IdNzfy2e6pZiYF3swivgzy
APCA_API_BASE_URL=https://paper-api.alpaca.markets
MOBILE_MONITORING_PORT=8080
REMOTE_ACCESS_ENABLED=True
LOG_TO_STDOUT=true
LOG_LEVEL=INFO
ENVFILE
    
    # Create necessary directories
    mkdir -p /opt/trading_bot/{logs,data/historical,data/ml_models,data/news,data/economic,data/fundamental,data/realtime}
    
    # Set proper permissions
    chmod 755 /opt/trading_bot/logs
    chmod 600 /opt/trading_bot/.env
EOF

echo -e "${GREEN}✅ Environment setup completed${NC}"

# Step 4: Build and start Docker container
echo -e "${BLUE}📋 Step 4: Building and starting Docker container...${NC}"

ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << 'EOF'
    cd /opt/trading_bot
    
    # Wait for Docker to be ready
    echo "Waiting for Docker service to be ready..."
    while ! docker ps &> /dev/null; do
        sleep 2
    done
    
    # Stop any existing containers
    docker stop trading-bot 2>/dev/null || true
    docker rm trading-bot 2>/dev/null || true
    
    # Build the Docker image
    echo "Building Docker image..."
    docker build -t trading_bot_trading-bot .
    
    # Run the container
    echo "Starting trading bot container..."
    docker run -d \
        --name trading-bot \
        --restart unless-stopped \
        -p 80:8080 \
        -p 8080:8080 \
        --env-file .env \
        -v /opt/trading_bot/data:/app/data \
        trading_bot_trading-bot:latest
    
    # Wait for container to start
    sleep 10
    
    # Check container status
    docker ps | grep trading-bot
EOF

echo -e "${GREEN}✅ Docker container started successfully${NC}"

# Step 5: Verify deployment
echo -e "${BLUE}📋 Step 5: Verifying deployment...${NC}"

# Test local access on the server
echo "Testing local access..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "curl -f -s http://localhost:80 > /dev/null" && \
    echo -e "${GREEN}✅ Local dashboard access: OK${NC}" || \
    echo -e "${RED}❌ Local dashboard access: FAILED${NC}"

# Test external access
echo "Testing external access..."
if curl -f -s "http://$PUBLIC_IP" > /dev/null; then
    echo -e "${GREEN}✅ External dashboard access: OK${NC}"
else
    echo -e "${YELLOW}⚠️ External access may take a few more minutes${NC}"
fi

# Step 6: Check logs
echo -e "${BLUE}📋 Step 6: Checking initial logs...${NC}"
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "docker logs trading-bot --tail 10"

# Step 7: Create management scripts on AWS instance
echo -e "${BLUE}📋 Step 7: Creating management scripts...${NC}"

ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << 'EOF'
    # Create trading bot management script
    sudo tee /usr/local/bin/trading-bot-manage << 'SCRIPT'
#!/bin/bash
case "$1" in
    start)   docker start trading-bot ;;
    stop)    docker stop trading-bot ;;
    restart) docker restart trading-bot ;;
    status)  docker ps | grep trading-bot && docker logs trading-bot --tail 5 ;;
    logs)    docker logs trading-bot -f ;;
    shell)   docker exec -it trading-bot bash ;;
    health)  curl -s http://localhost:80/api/status | python3 -m json.tool ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs|shell|health}" ;;
esac
SCRIPT
    
    sudo chmod +x /usr/local/bin/trading-bot-manage
    
    # Create health check cron job
    (crontab -l 2>/dev/null || echo ""; echo "*/5 * * * * /usr/local/bin/trading-bot-manage health > /dev/null 2>&1") | crontab -
EOF

echo -e "${GREEN}✅ Management scripts created${NC}"

# Clean up temp files
rm -f /tmp/rsync_exclude

echo ""
echo "================================================================="
echo -e "${GREEN}🎉 Trading Bot Successfully Deployed on AWS!${NC}"
echo "================================================================="
echo -e "${BLUE}Access Information:${NC}"
echo "  Dashboard URL: http://$PUBLIC_IP"
echo "  SSH Access: ssh -i $KEY_FILE ubuntu@$PUBLIC_IP"
echo ""
echo -e "${BLUE}Management Commands (on AWS instance):${NC}"
echo "  trading-bot-manage start    # Start the bot"
echo "  trading-bot-manage stop     # Stop the bot"
echo "  trading-bot-manage restart  # Restart the bot"
echo "  trading-bot-manage status   # Check status"
echo "  trading-bot-manage logs     # View logs"
echo "  trading-bot-manage health   # Health check"
echo ""
echo -e "${BLUE}Instance Details:${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  Region: $REGION"
echo "  Instance Type: t3.micro (Free Tier)"
echo ""
echo -e "${GREEN}Your trading bot is now running on AWS! 🚀${NC}"
echo -e "${YELLOW}Remember: AWS Free Tier includes 750 hours/month for 12 months${NC}"