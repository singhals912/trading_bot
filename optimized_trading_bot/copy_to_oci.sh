#!/bin/bash

# Script to copy trading bot files to OCI instance
# Run this from your local machine

# Configuration - UPDATE THESE VALUES
OCI_HOST="129.80.35.82"  # Your OCI instance IP
OCI_USER="ubuntu"       # SSH user
SSH_KEY_PATH=~/Downloads/ssh-key-2025-06-28.key  # Path to your SSH private key

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Copying trading bot to OCI instance...${NC}"

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH key not found at $SSH_KEY_PATH${NC}"
    echo "Please update SSH_KEY_PATH in this script or generate SSH keys"
    exit 1
fi

# Test SSH connection
echo -e "${YELLOW}🔍 Testing SSH connection...${NC}"
if ! ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 "$OCI_USER@$OCI_HOST" "echo 'SSH connection successful'"; then
    echo -e "${RED}❌ SSH connection failed${NC}"
    echo "Please check:"
    echo "  - OCI_HOST IP address: $OCI_HOST"
    echo "  - SSH key path: $SSH_KEY_PATH"
    echo "  - Security groups allow SSH (port 22)"
    exit 1
fi

# Copy deployment scripts first
echo -e "${YELLOW}📦 Copying deployment scripts...${NC}"
scp -i "$SSH_KEY_PATH" deploy_to_oci.sh setup_systemd_service.sh "$OCI_USER@$OCI_HOST:~/"

# Run initial deployment setup
echo -e "${YELLOW}⚙️ Running initial deployment setup...${NC}"
ssh -i "$SSH_KEY_PATH" "$OCI_USER@$OCI_HOST" "chmod +x ~/deploy_to_oci.sh && sudo ~/deploy_to_oci.sh"

# Copy main application files
echo -e "${YELLOW}📁 Copying application files...${NC}"

# Create list of files to copy (excluding sensitive and temporary files)
EXCLUDE_PATTERNS=(
    "--exclude=*.pyc"
    "--exclude=__pycache__"
    "--exclude=.git"
    "--exclude=.env"
    "--exclude=venv"
    "--exclude=logs/*"
    "--exclude=data/historical/*"
    "--exclude=*.log"
    "--exclude=.DS_Store"
    "--exclude=bot_state.json.backup"
)

# Copy files using rsync
rsync -avz -e "ssh -i $SSH_KEY_PATH" \
    "${EXCLUDE_PATTERNS[@]}" \
    --progress \
    ./ "$OCI_USER@$OCI_HOST:/tmp/trading_bot_files/"

# Move files to proper location and set permissions
echo -e "${YELLOW}🔧 Setting up file permissions...${NC}"
ssh -i "$SSH_KEY_PATH" "$OCI_USER@$OCI_HOST" << 'EOF'
    sudo cp -r /tmp/trading_bot_files/* /opt/trading_bot/
    sudo chown -R tradingbot:tradingbot /opt/trading_bot/
    sudo chmod +x /opt/trading_bot/*.py
    sudo chmod +x /opt/trading_bot/*.sh
    rm -rf /tmp/trading_bot_files/
EOF

# Setup systemd service
echo -e "${YELLOW}⚙️ Setting up systemd service...${NC}"
ssh -i "$SSH_KEY_PATH" "$OCI_USER@$OCI_HOST" "chmod +x ~/setup_systemd_service.sh && sudo ~/setup_systemd_service.sh"

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. SSH to your OCI instance:"
echo "   ssh -i $SSH_KEY_PATH $OCI_USER@$OCI_HOST"
echo ""
echo "2. Edit environment variables:"
echo "   sudo nano /opt/trading_bot/.env"
echo ""
echo "3. Start the trading bot:"
echo "   sudo systemctl start tradingbot"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status tradingbot"
echo ""
echo "5. Access dashboard:"
echo "   http://$OCI_HOST:8080"
echo ""
echo -e "${GREEN}🎉 Your trading bot is ready to run on OCI!${NC}"