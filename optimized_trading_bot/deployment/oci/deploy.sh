#!/bin/bash

# OCI Deployment Script for Trading Bot
# Usage: ./deploy.sh [production|development]

set -e

ENVIRONMENT="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "🚀 Deploying Trading Bot to OCI"
echo "📦 Environment: $ENVIRONMENT"
echo "📁 Project Root: $PROJECT_ROOT"
echo ""

# Check if we're on the OCI instance
if [ ! -f /etc/oracle-cloud-agent/plugins/oci-utils/oci-utils.conf ]; then
    echo "⚠️  This script should be run on the OCI instance"
    echo "💡 Run this on your OCI Ubuntu instance after setup"
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API credentials:"
    echo "   nano .env"
    echo ""
    echo "Required variables:"
    echo "   ALPACA_API_KEY=your_key_here"
    echo "   ALPACA_SECRET_KEY=your_secret_here"
    echo "   ALPACA_PAPER_TRADING=true"
    echo ""
    read -p "Press Enter after configuring .env file..."
fi

# Create required directories
echo "📁 Creating directories..."
mkdir -p logs data backups config

# Set proper permissions
sudo chown -R ubuntu:ubuntu logs data backups config
chmod 755 logs data backups config

# Install system dependencies if needed
echo "🔧 Checking system dependencies..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt update
    sudo apt install -y docker-compose
fi

# Configure firewall
echo "🔒 Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw --force enable
    sudo ufw allow 22/tcp comment 'SSH'
    sudo ufw allow 8080/tcp comment 'Trading Bot Dashboard'
    sudo ufw reload
fi

# Build and deploy
echo "🏗️  Building and deploying..."
cd docker

if [ "$ENVIRONMENT" = "production" ]; then
    # Production deployment
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml build --no-cache
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to start
    sleep 30
    
    # Check health
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "🏥 Health Check:"
    if curl -f http://localhost:8080/api/status &>/dev/null; then
        echo "✅ Trading Bot is healthy and running"
    else
        echo "❌ Trading Bot health check failed"
        echo "📋 Checking logs..."
        docker-compose -f docker-compose.prod.yml logs --tail=50 trading-bot
    fi
    
else
    # Development deployment
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    # Wait for services to start
    sleep 30
    
    # Check health
    docker-compose ps
    
    echo ""
    echo "🏥 Health Check:"
    if curl -f http://localhost:8080/api/status &>/dev/null; then
        echo "✅ Trading Bot is healthy and running"
    else
        echo "❌ Trading Bot health check failed"
        echo "📋 Checking logs..."
        docker-compose logs --tail=50 trading-bot
    fi
fi

# Get instance public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata | grep -o '"publicIp":"[^"]*' | cut -d'"' -f4)

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "🌐 Access your Trading Bot:"
echo "   Dashboard: http://$PUBLIC_IP:8080"
echo "   API Status: http://$PUBLIC_IP:8080/api/status"
echo ""
echo "📊 Monitor your bot:"
echo "   docker-compose logs -f trading-bot"
echo "   curl http://localhost:8080/api/status"
echo ""
echo "🛑 To stop the bot:"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "   docker-compose -f docker-compose.prod.yml down"
else
    echo "   docker-compose down"
fi
echo ""

# Create systemd service for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚙️  Setting up systemd service..."
    
    sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=Enhanced Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_ROOT/docker
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable trading-bot
    
    echo "✅ Systemd service created and enabled"
    echo "   Service will auto-start on boot"
    echo "   Control with: sudo systemctl [start|stop|restart|status] trading-bot"
fi

echo ""
echo "🎯 Your Enhanced Trading Bot is now running 24/7 on OCI Always Free!"