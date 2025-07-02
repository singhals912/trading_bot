#!/bin/bash

# Optimized Trading Bot - Setup Script
# This script sets up the trading bot environment and dependencies

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
   exit 1
fi

log "🚀 Starting Optimized Trading Bot Setup"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    log "✅ Python $python_version is compatible"
else
    error "❌ Python 3.8+ is required. Found: $python_version"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    error "❌ pip3 is not installed"
    exit 1
fi

# Create project directory structure if not exists
log "📁 Creating directory structure..."
mkdir -p logs
mkdir -p data/{cache,historical,realtime}
mkdir -p backups/{daily,critical}
mkdir -p config/environments

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log "🐍 Creating Python virtual environment..."
    python3 -m venv venv
else
    log "✅ Virtual environment already exists"
fi

# Activate virtual environment
log "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
log "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
log "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log "📝 Creating .env file from template..."
    cp .env.example .env
    warn "⚠️ Please edit .env file with your API credentials before running the bot"
else
    log "✅ .env file already exists"
fi

# Set up logging directory with proper permissions
log "📋 Setting up logging..."
chmod 755 logs
touch logs/trading_bot.log
touch logs/errors.log
touch logs/trades.log

# Create systemd service file (optional)
create_systemd_service() {
    read -p "Do you want to create a systemd service for auto-start? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "⚙️ Creating systemd service..."
        
        cat > trading-bot.service << EOF
[Unit]
Description=Optimized Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python -m src.main --config config/production.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        info "📄 Service file created: trading-bot.service"
        info "To install: sudo mv trading-bot.service /etc/systemd/system/"
        info "To enable: sudo systemctl enable trading-bot"
        info "To start: sudo systemctl start trading-bot"
    fi
}

# Install system dependencies (optional)
install_system_deps() {
    if command -v apt-get &> /dev/null; then
        log "🔧 Installing system dependencies (Ubuntu/Debian)..."
        sudo apt-get update
        sudo apt-get install -y redis-server postgresql-client build-essential
    elif command -v yum &> /dev/null; then
        log "🔧 Installing system dependencies (CentOS/RHEL)..."
        sudo yum install -y redis postgresql build-essential
    elif command -v brew &> /dev/null; then
        log "🔧 Installing system dependencies (macOS)..."
        brew install redis postgresql
    else
        warn "⚠️ Could not detect package manager. Please install Redis and PostgreSQL manually."
    fi
}

# Check for system dependencies
check_system_deps() {
    log "🔍 Checking system dependencies..."
    
    deps_missing=false
    
    if ! command -v redis-server &> /dev/null; then
        warn "❌ Redis not found (optional but recommended for caching)"
        deps_missing=true
    else
        log "✅ Redis found"
    fi
    
    if ! command -v psql &> /dev/null; then
        warn "❌ PostgreSQL client not found (optional)"
        deps_missing=true
    else
        log "✅ PostgreSQL client found"
    fi
    
    if $deps_missing; then
        read -p "Do you want to install missing system dependencies? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_system_deps
        fi
    fi
}

# Validate configuration
validate_config() {
    log "✅ Validating configuration..."
    if python3 -m src.main --validate-config --config config/production.yaml; then
        log "✅ Configuration validation passed"
    else
        error "❌ Configuration validation failed"
        exit 1
    fi
}

# Run tests
run_tests() {
    read -p "Do you want to run the test suite? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "🧪 Running test suite..."
        if python3 -m pytest tests/ -v; then
            log "✅ All tests passed"
        else
            error "❌ Some tests failed"
            exit 1
        fi
    fi
}

# Main setup flow
main() {
    check_system_deps
    
    # Validate environment file
    if [ -f ".env" ]; then
        log "🔍 Checking .env file..."
        if grep -q "your_alpaca_api_key_id_here" .env; then
            warn "⚠️ Please update your API credentials in .env file"
        fi
    fi
    
    # Validate configuration if possible
    if [ -f "config/production.yaml" ]; then
        validate_config
    fi
    
    run_tests
    create_systemd_service
    
    log "🎉 Setup completed successfully!"
    echo
    info "📋 Next steps:"
    info "1. Edit .env file with your API credentials"
    info "2. Review config/production.yaml settings"  
    info "3. Run: python -m src.main --config config/production.yaml"
    info "4. Monitor dashboard at: http://localhost:8080"
    echo
    warn "⚠️ Important Security Notes:"
    warn "- Always test with paper trading first (PAPER_TRADING=true)"
    warn "- Never commit .env file to version control"
    warn "- Use strong passwords for production deployments"
    warn "- Enable notifications for critical events"
    echo
    log "📚 Documentation: See README.md for detailed usage instructions"
}

# Run main function
main

# Set executable permissions for other scripts
chmod +x scripts/*.sh

log "🔒 Setup script completed. Virtual environment is ready."