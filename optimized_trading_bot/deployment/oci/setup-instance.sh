#!/bin/bash

# OCI Instance Setup Script
# Run this first on your new OCI Ubuntu instance

set -e

echo "🏗️  Setting up OCI instance for Trading Bot deployment"
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential tools
echo "🔧 Installing essential tools..."
sudo apt install -y \
    curl \
    wget \
    git \
    htop \
    nano \
    ufw \
    unzip \
    build-essential

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    sudo systemctl enable docker
    sudo systemctl start docker
    rm get-docker.sh
    echo "✅ Docker installed successfully"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt install -y docker-compose
    echo "✅ Docker Compose installed successfully"
else
    echo "✅ Docker Compose already installed"
fi

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 8080/tcp comment 'Trading Bot Dashboard'
sudo ufw reload
echo "✅ Firewall configured"

# Create application directory
echo "📁 Creating application directory..."
mkdir -p ~/trading-bot
cd ~/trading-bot

# Clone repository (you'll need to replace this with your actual repo)
echo "📥 Repository setup..."
echo "ℹ️  You'll need to either:"
echo "   1. Clone your repository: git clone <your-repo-url> ."
echo "   2. Upload your files using scp"
echo ""
echo "Example SCP upload from your local machine:"
echo "   scp -r /local/path/to/trading_bot/* ubuntu@$(curl -s http://169.254.169.254/opc/v1/instance/metadata | grep -o '\"publicIp\":\"[^\"]*' | cut -d'\"' -f4):~/trading-bot/"
echo ""

# Create directory structure
mkdir -p logs data backups config

# Set permissions
chmod 755 logs data backups config

# Get public IP for reference
PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata | grep -o '"publicIp":"[^"]*' | cut -d'"' -f4)

echo ""
echo "🎉 OCI Instance setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Upload your trading bot code to ~/trading-bot/"
echo "2. Configure your .env file with API credentials"
echo "3. Run the deployment script: ./deployment/oci/deploy.sh production"
echo ""
echo "🌐 Your instance details:"
echo "   Public IP: $PUBLIC_IP"
echo "   SSH: ssh ubuntu@$PUBLIC_IP"
echo "   Future Dashboard: http://$PUBLIC_IP:8080"
echo ""
echo "💡 Remember to logout and login again to apply Docker group membership:"
echo "   exit"
echo "   ssh ubuntu@$PUBLIC_IP"
echo ""

# Create a simple status script
cat > ~/status.sh << 'EOF'
#!/bin/bash
echo "🖥️  System Status:"
echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')% used"
echo "   Memory: $(free -h | awk 'NR==2{printf "%.1f%%, %s/%s", $3*100/$2, $3, $2}')"
echo "   Disk: $(df -h / | awk 'NR==2{printf "%s used, %s available (%s used)", $3, $4, $5}')"
echo ""
echo "🐳 Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🔗 Quick Links:"
PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata | grep -o '"publicIp":"[^"]*' | cut -d'"' -f4)
echo "   Dashboard: http://$PUBLIC_IP:8080"
echo "   API Status: http://$PUBLIC_IP:8080/api/status"
EOF

chmod +x ~/status.sh

echo "✅ Created status script: ~/status.sh"
echo "   Run './status.sh' anytime to check system status"