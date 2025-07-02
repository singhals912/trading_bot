#!/bin/bash

# OCI Deployment Script for Trading Bot
# Run this script on your OCI Ubuntu instance

set -e

echo "🚀 Starting OCI deployment for trading bot..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3.11 python3.11-pip python3.11-venv git curl wget

# Create trading bot user (optional but recommended)
echo "👤 Creating trading bot user..."
sudo useradd -m -s /bin/bash tradingbot || echo "User tradingbot already exists"

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/trading_bot
sudo chown tradingbot:tradingbot /opt/trading_bot

# Switch to trading bot user for remaining operations
echo "🔄 Switching to tradingbot user context..."

# Create the deployment continuation script
cat > /tmp/deploy_continue.sh << 'EOF'
#!/bin/bash
set -e

echo "📥 Cloning/copying trading bot code..."
cd /opt/trading_bot

# If using git (replace with your repository URL)
# git clone https://github.com/yourusername/trading_bot.git .

# For now, we'll create the directory structure
# You'll need to copy your files here manually or via scp

echo "🐍 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

echo "📦 Installing Python requirements..."
# We'll create a basic requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    cat > requirements.txt << 'REQUIREMENTS'
alpaca-trade-api>=3.0.0
numpy>=1.21.0
pandas>=1.3.0
yfinance>=0.2.0
requests>=2.28.0
python-dotenv>=0.19.0
scikit-learn>=1.1.0
matplotlib>=3.5.0
flask>=2.2.0
pyngrok>=6.0.0
twilio>=7.16.0
REQUIREMENTS
fi

pip install -r requirements.txt

echo "⚙️ Creating environment configuration..."
cat > .env << 'ENVFILE'
# Alpaca API Configuration
APCA_API_KEY_ID=your_alpaca_api_key_here
APCA_API_SECRET_KEY=your_alpaca_secret_key_here
APCA_API_BASE_URL=https://paper-api.alpaca.markets

# Remote Monitoring
MOBILE_MONITORING_PORT=8080
REMOTE_ACCESS_ENABLED=True

# Email Alerts (optional)
EMAIL_SENDER=
EMAIL_PASSWORD=
EMAIL_RECIPIENT=

# SMS Alerts (optional)
TWILIO_SID=
TWILIO_TOKEN=
TWILIO_FROM=
PHONE_NUMBER=

# Data Sources (optional)
ALPHA_VANTAGE_KEY=
FRED_API_KEY=
NEWS_API_KEY=
ENVFILE

echo "📁 Creating necessary directories..."
mkdir -p logs data/historical data/ml_models data/news data/economic data/fundamental data/realtime config

echo "🔧 Setting up log rotation..."
sudo tee /etc/logrotate.d/tradingbot > /dev/null << 'LOGROTATE'
/opt/trading_bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
LOGROTATE

echo "✅ Basic setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy your trading bot files to /opt/trading_bot/"
echo "2. Update the .env file with your actual API keys"
echo "3. Run the systemd service setup script"
echo ""
EOF

# Make the continuation script executable and run it as tradingbot user
chmod +x /tmp/deploy_continue.sh
sudo -u tradingbot bash /tmp/deploy_continue.sh

echo "✅ Initial deployment setup complete!"
echo ""
echo "🔑 IMPORTANT: You need to:"
echo "1. Copy your trading bot files to /opt/trading_bot/ using scp or rsync"
echo "2. Edit /opt/trading_bot/.env with your actual API keys"
echo "3. Run the systemd service setup (next script)"
echo ""
echo "📁 Application directory: /opt/trading_bot"
echo "👤 Application user: tradingbot"
echo ""