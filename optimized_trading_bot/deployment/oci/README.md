# OCI Always Free Deployment Guide

Deploy your Enhanced Trading Bot on Oracle Cloud Infrastructure's Always Free tier for 24/7 operation.

## 🎯 Why OCI Always Free?

- **Truly Free Forever** - No credit card expiration concerns
- **2 AMD Compute instances** - 1/8 OCPU, 1GB RAM each
- **200GB Block Storage** - Persistent storage
- **10GB Object Storage** - For backups
- **Always Free Networking** - Load balancer, VCN
- **No time limits** - Runs indefinitely

## 🚀 Step-by-Step Deployment

### 1. Create OCI Account
1. Go to https://cloud.oracle.com
2. Sign up for Always Free account
3. Complete identity verification
4. Choose your home region (closest to you)

### 2. Create Compute Instance

#### In OCI Console:
1. **Compute** → **Instances** → **Create Instance**
2. **Instance Configuration:**
   - Name: `trading-bot-server`
   - Image: `Canonical Ubuntu 22.04`
   - Shape: `VM.Standard.E2.1.Micro` (Always Free)
   - OCPU: 1/8, Memory: 1GB
3. **Networking:**
   - VCN: Use default or create new
   - Subnet: Public subnet
   - Public IP: Assign public IPv4
4. **SSH Keys:**
   - Upload your SSH public key
   - Or generate new key pair
5. **Boot Volume:**
   - Size: 50GB (Always Free eligible)

### 3. Configure Security Rules

#### Add Ingress Rules:
1. **VCN** → **Security Lists** → **Default Security List**
2. **Add Ingress Rules:**
   ```
   Source CIDR: 0.0.0.0/0
   IP Protocol: TCP
   Destination Port: 8080 (Dashboard)
   Description: Trading Bot Dashboard
   
   Source CIDR: 0.0.0.0/0
   IP Protocol: TCP  
   Destination Port: 22 (SSH)
   Description: SSH Access
   ```

### 4. Connect to Instance

```bash
# Replace with your instance's public IP
ssh ubuntu@<PUBLIC_IP>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
sudo systemctl enable docker

# Install Docker Compose
sudo apt install docker-compose -y

# Logout and login to apply docker group
exit
ssh ubuntu@<PUBLIC_IP>
```

### 5. Deploy Trading Bot

```bash
# Clone your repository (or upload files)
git clone <your-repo-url> trading-bot
cd trading-bot

# Or upload via scp:
# scp -r /local/path/to/trading_bot ubuntu@<PUBLIC_IP>:~/

# Create environment file
cp .env.example .env
nano .env  # Configure your API keys

# Create required directories
mkdir -p logs data backups

# Deploy with Docker Compose
cd docker
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

## 🔧 Production Configuration

### Environment Variables (.env):
```bash
# Trading Configuration
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_PAPER_TRADING=true
ENVIRONMENT=production

# Monitoring
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Dashboard
DASHBOARD_PORT=8080
ENABLE_DASHBOARD=true

# Optional: Database (if using)
POSTGRES_PASSWORD=secure_password_here
REDIS_PASSWORD=secure_redis_password
```

### Docker Compose for Production:
```yaml
# docker/docker-compose.prod.yml
version: '3.8'

services:
  trading-bot:
    build:
      context: ..
      dockerfile: docker/Dockerfile
      target: production
    container_name: trading-bot-prod
    restart: unless-stopped
    environment:
      - PYTHONPATH=/app/src:/app
      - ENVIRONMENT=production
    env_file:
      - ../.env
    ports:
      - "8080:8080"
    volumes:
      - ../logs:/app/logs
      - ../data:/app/data
      - ../backups:/app/backups
      - ../.env:/app/.env:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### System Service (Optional):
```bash
# Create systemd service for auto-start
sudo nano /etc/systemd/system/trading-bot.service
```

```ini
[Unit]
Description=Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/home/ubuntu/trading-bot/docker
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Enable service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

## 🔒 Security Best Practices

### 1. Firewall Configuration:
```bash
# Configure UFW
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 8080/tcp # Dashboard
sudo ufw status
```

### 2. SSH Key Security:
```bash
# Disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### 3. SSL/TLS (Optional):
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

## 📊 Monitoring & Maintenance

### View Logs:
```bash
# Real-time logs
docker-compose logs -f trading-bot

# System logs
journalctl -u trading-bot -f
```

### Resource Monitoring:
```bash
# System resources
htop
df -h
docker stats

# Trading bot specific
curl http://localhost:8080/api/status
```

### Backup Strategy:
```bash
# Create backup script
nano ~/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"

# Backup trading data
tar -czf "$BACKUP_DIR/trading_data_$DATE.tar.gz" \
  /home/ubuntu/trading-bot/logs \
  /home/ubuntu/trading-bot/data \
  /home/ubuntu/trading-bot/.env

# Keep only last 7 days
find $BACKUP_DIR -name "trading_data_*.tar.gz" -mtime +7 -delete

echo "Backup completed: trading_data_$DATE.tar.gz"
```

```bash
# Make executable and add to cron
chmod +x ~/backup.sh
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup.sh
```

## 🌐 Access Your Bot

### Dashboard URLs:
- **Direct IP**: `http://<PUBLIC_IP>:8080`
- **API**: `http://<PUBLIC_IP>:8080/api/status`

### Optional Domain Setup:
1. Register free domain (Freenom, etc.)
2. Point A record to your OCI instance IP
3. Access via `http://yourdomain.com:8080`

## 💰 Cost Management

### Always Free Limits:
- ✅ **Compute**: 2 micro instances (this uses 1)
- ✅ **Storage**: 200GB total (using ~50GB)
- ✅ **Network**: 10TB outbound/month
- ✅ **Monitoring**: Basic metrics included

### Monitoring Usage:
- **OCI Console** → **Governance** → **Limits and Usage**
- Check Always Free resource consumption
- Set up billing alerts (though should remain $0)

## 🚨 Troubleshooting

### Common Issues:

**Instance won't start:**
```bash
# Check instance logs in OCI Console
# Verify Always Free shape selection
```

**Can't connect via SSH:**
```bash
# Check security list rules
# Verify SSH key pair
# Check public IP assignment
```

**Dashboard not accessible:**
```bash
# Check ingress rules for port 8080
# Verify container is running: docker ps
# Check logs: docker-compose logs trading-bot
```

**Bot stops unexpectedly:**
```bash
# Check system resources: free -h
# Review logs for errors
# Verify environment variables
```

This setup gives you a production-ready, always-on trading bot for **absolutely free**! 🎯