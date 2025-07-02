# OCI Environment Setup Guide

## Required Environment Variables

Edit `/opt/trading_bot/.env` on your OCI instance with these values:

### Essential (Required)
```bash
# Alpaca API Configuration
APCA_API_KEY_ID=your_alpaca_api_key_here
APCA_API_SECRET_KEY=your_alpaca_secret_key_here
APCA_API_BASE_URL=https://paper-api.alpaca.markets

# Remote Monitoring
MOBILE_MONITORING_PORT=8080
REMOTE_ACCESS_ENABLED=True
```

### Optional (Enhanced Features)
```bash
# Email Alerts
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=alerts@yourdomain.com

# SMS Alerts (Twilio)
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_FROM=+1234567890
PHONE_NUMBER=+1987654321

# Data Sources
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_api_key
NEWS_API_KEY=your_news_api_key
```

## OCI Security Groups Configuration

### Required Ingress Rules
- **SSH**: Port 22 (Source: Your IP/32)
- **Dashboard**: Port 8080 (Source: Your IP/32 or 0.0.0.0/0 for public access)

### Optional Ports
- **HTTP**: Port 80 (if using reverse proxy)
- **HTTPS**: Port 443 (if using SSL)

## OCI Instance Requirements

### Minimum Specifications
- **Shape**: VM.Standard.E2.1.Micro (Always Free)
- **CPU**: 1 OCPU
- **Memory**: 1GB RAM
- **Storage**: 50GB Boot Volume

### Recommended Specifications
- **Shape**: VM.Standard2.1 or VM.Standard.E3.Flex
- **CPU**: 1-2 OCPUs
- **Memory**: 8-16GB RAM
- **Storage**: 100GB+ Boot Volume

## Post-Deployment Security Hardening

### 1. SSH Key Authentication Only
```bash
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### 2. Fail2Ban Installation
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 3. Automatic Security Updates
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. Firewall Configuration
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw enable
```

## Monitoring and Maintenance

### Log Locations
- **System Logs**: `/opt/trading_bot/logs/systemd.log`
- **Error Logs**: `/opt/trading_bot/logs/systemd_error.log`
- **Health Checks**: `/opt/trading_bot/logs/health_check.log`

### Maintenance Commands
```bash
# Service management
sudo systemctl start|stop|restart|status tradingbot

# Log monitoring
tail -f /opt/trading_bot/logs/systemd.log
sudo journalctl -u tradingbot -f

# Health check
/usr/local/bin/check_tradingbot.sh

# Resource monitoring
htop
df -h
free -h
```

### Backup Strategy
```bash
# Daily backup of bot state and config
0 2 * * * tar -czf /home/ubuntu/backup_$(date +\%Y\%m\%d).tar.gz /opt/trading_bot/bot_state.json /opt/trading_bot/config/ /opt/trading_bot/.env
```