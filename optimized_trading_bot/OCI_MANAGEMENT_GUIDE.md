# Trading Bot Management Guide for OCI

## **SSH Connection**
```bash
# Connect to your OCI instance
ssh -i ~/Downloads/ssh-key-2025-06-28.key ubuntu@129.80.35.82
```

## **Basic Container Management**

### **Start the Trading Bot**
```bash
# Start if container exists but is stopped
sudo docker start trading-bot

# Or run fresh container (if doesn't exist)
sudo docker run -d --name trading-bot -p 80:8080 \
  -e APCA_API_KEY_ID=PK6Y4XBDRDJHJ8ZKF81B \
  -e APCA_API_SECRET_KEY=s9Yw8MdroJlbR4eKA8IdNzfy2e6pZiYF3swivgzy \
  -e APCA_API_BASE_URL=https://paper-api.alpaca.markets \
  trading_bot_trading-bot:latest
```

### **Stop the Trading Bot**
```bash
# Graceful stop
sudo docker stop trading-bot

# Force stop (if unresponsive)
sudo docker kill trading-bot
```

### **Pause/Resume Trading Bot**
```bash
# Pause (stops execution but keeps container)
sudo docker pause trading-bot

# Resume from pause
sudo docker unpause trading-bot
```

### **Restart the Trading Bot**
```bash
# Restart existing container
sudo docker restart trading-bot
```

## **Status & Monitoring**

### **Check Container Status**
```bash
# View running containers
sudo docker ps

# View all containers (including stopped)
sudo docker ps -a

# Detailed container info
sudo docker inspect trading-bot

# Resource usage
sudo docker stats trading-bot
```

### **View Logs**
```bash
# Real-time logs (follow)
sudo docker logs trading-bot -f

# Last 50 lines
sudo docker logs trading-bot --tail 50

# Logs with timestamps
sudo docker logs trading-bot -t

# Logs since specific time
sudo docker logs trading-bot --since="2025-06-28T19:00:00"
```

## **Debugging**

### **Access Container Shell**
```bash
# Execute bash inside running container
sudo docker exec -it trading-bot bash

# Run specific commands inside container
sudo docker exec trading-bot ls -la /app
sudo docker exec trading-bot cat /app/.env
sudo docker exec trading-bot ps aux
```

### **Check Environment Variables**
```bash
# View all env vars in container
sudo docker exec trading-bot env

# Check specific trading bot variables
sudo docker exec trading-bot env | grep APCA
```

### **File System Access**
```bash
# Copy files from container to host
sudo docker cp trading-bot:/app/logs/trading_bot.log ./

# Copy files from host to container
sudo docker cp ./config.json trading-bot:/app/

# View container filesystem
sudo docker exec trading-bot find /app -name "*.log"
```

### **Performance Debugging**
```bash
# Container resource usage
sudo docker stats trading-bot --no-stream

# Process list inside container
sudo docker exec trading-bot top

# Disk usage inside container
sudo docker exec trading-bot df -h
```

## **Advanced Management**

### **Container Rebuild & Update**
```bash
# Stop and remove current container
sudo docker stop trading-bot
sudo docker rm trading-bot

# Rebuild image (if you updated code)
cd /opt/trading_bot
sudo docker build -t trading_bot_trading-bot .

# Run new container
sudo docker run -d --name trading-bot -p 80:8080 \
  -e APCA_API_KEY_ID=PK6Y4XBDRDJHJ8ZKF81B \
  -e APCA_API_SECRET_KEY=s9Yw8MdroJlbR4eKA8IdNzfy2e6pZiYF3swivgzy \
  -e APCA_API_BASE_URL=https://paper-api.alpaca.markets \
  trading_bot_trading-bot:latest
```

### **Backup & Recovery**
```bash
# Export container as image
sudo docker commit trading-bot trading-bot-backup:$(date +%Y%m%d)

# Save image to file
sudo docker save trading-bot-backup:$(date +%Y%m%d) > trading-bot-backup.tar

# Load image from file
sudo docker load < trading-bot-backup.tar
```

### **Configuration Updates**
```bash
# Update environment variables without rebuilding
sudo docker stop trading-bot
sudo docker rm trading-bot

# Run with new environment variables
sudo docker run -d --name trading-bot -p 80:8080 \
  -e APCA_API_KEY_ID=YOUR_NEW_KEY \
  -e APCA_API_SECRET_KEY=YOUR_NEW_SECRET \
  -e APCA_API_BASE_URL=https://paper-api.alpaca.markets \
  -e LOG_LEVEL=DEBUG \
  trading_bot_trading-bot:latest
```

## **Troubleshooting Commands**

### **Network Issues**
```bash
# Test dashboard accessibility
curl -I http://localhost:80
curl -I http://129.80.35.82

# Check port bindings
sudo docker port trading-bot
```

### **Container Won't Start**
```bash
# Check Docker daemon
sudo systemctl status docker

# View detailed error logs
sudo docker logs trading-bot

# Run container interactively for debugging
sudo docker run -it --rm trading_bot_trading-bot bash
```

### **Clean Up**
```bash
# Remove stopped containers
sudo docker container prune

# Remove unused images
sudo docker image prune

# Remove all unused Docker objects
sudo docker system prune -a
```

## **Quick Reference Commands**

### **Daily Management**
```bash
# Quick status check
sudo docker ps | grep trading-bot && echo "✅ Running" || echo "❌ Stopped"

# Quick log check
sudo docker logs trading-bot --tail 10

# Quick restart
sudo docker restart trading-bot
```

### **Dashboard Access**
- **URL**: http://129.80.35.82
- **API Status**: http://129.80.35.82/api/status
- **Health Check**: `curl http://129.80.35.82/api/status`

### **Emergency Stop**
```bash
# Emergency shutdown
sudo docker kill trading-bot
sudo docker rm trading-bot
```

## **Automation Scripts**

### **Create a Management Script**
```bash
# Create management script
sudo tee /usr/local/bin/trading-bot-manage << 'EOF'
#!/bin/bash
case "$1" in
    start)   sudo docker start trading-bot ;;
    stop)    sudo docker stop trading-bot ;;
    restart) sudo docker restart trading-bot ;;
    status)  sudo docker ps | grep trading-bot ;;
    logs)    sudo docker logs trading-bot -f ;;
    shell)   sudo docker exec -it trading-bot bash ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs|shell}" ;;
esac
EOF

sudo chmod +x /usr/local/bin/trading-bot-manage

# Use it like:
# trading-bot-manage start
# trading-bot-manage logs
# trading-bot-manage status
```

## **File Locations on OCI**

### **Important Paths**
- **Project Directory**: `/opt/trading_bot/`
- **Environment File**: `/opt/trading_bot/.env`
- **Docker Compose**: `/opt/trading_bot/docker-compose.yml`
- **Source Code**: `/opt/trading_bot/src/`
- **Configuration**: `/opt/trading_bot/config/`

### **Log Locations**
- **Container Logs**: `sudo docker logs trading-bot`
- **Application Logs**: Inside container at `/app/logs/`
- **System Logs**: `/var/log/syslog`

## **Performance Monitoring**

### **System Resources**
```bash
# Monitor system resources
htop

# Disk usage
df -h

# Memory usage
free -h

# Network connections
sudo netstat -tlnp | grep :80
```

### **Trading Bot Metrics**
```bash
# Check trading bot health
curl http://localhost:80/api/status

# Get performance metrics
curl http://localhost:80/api/metrics

# View portfolio status
curl http://localhost:80/api/portfolio
```

## **Security Best Practices**

### **Environment Variables**
```bash
# Never expose API keys in logs
sudo docker exec trading-bot env | grep APCA | sed 's/=.*/=***HIDDEN***/'

# Verify environment variables are loaded correctly
sudo docker exec trading-bot python -c "
import os
print('API Key loaded:', bool(os.getenv('APCA_API_KEY_ID')))
print('Secret loaded:', bool(os.getenv('APCA_API_SECRET_KEY')))
"
```

### **Access Control**
```bash
# Check who can access the dashboard
sudo ufw status

# Review Docker security
sudo docker exec trading-bot whoami
sudo docker exec trading-bot id
```

## **Backup Procedures**

### **Regular Backups**
```bash
# Backup configuration
sudo tar -czf trading-bot-config-$(date +%Y%m%d).tar.gz /opt/trading_bot/.env /opt/trading_bot/config/

# Backup container state
sudo docker export trading-bot > trading-bot-export-$(date +%Y%m%d).tar

# Backup database (if using)
sudo docker exec trading-bot-postgres pg_dump -U postgres trading_db > trading-db-backup-$(date +%Y%m%d).sql
```

### **Restore Procedures**
```bash
# Restore from backup
sudo docker stop trading-bot
sudo docker rm trading-bot
sudo docker import trading-bot-export-YYYYMMDD.tar trading-bot-restored
sudo docker run -d --name trading-bot trading-bot-restored
```

## **Deployment Updates**

### **Update Trading Bot Code**
```bash
# 1. Copy new code to OCI (from local machine)
rsync -avz -e "ssh -i ~/Downloads/ssh-key-2025-06-28.key" \
    --exclude='venv' --exclude='logs/*' --exclude='__pycache__' \
    /Users/ss/Downloads/Code/trading_bot/optimized_trading_bot/ \
    ubuntu@129.80.35.82:/opt/trading_bot/

# 2. Rebuild and restart (on OCI instance)
cd /opt/trading_bot
sudo docker stop trading-bot
sudo docker rm trading-bot
sudo docker build -t trading_bot_trading-bot .
sudo docker run -d --name trading-bot -p 80:8080 \
  -e APCA_API_KEY_ID=PK6Y4XBDRDJHJ8ZKF81B \
  -e APCA_API_SECRET_KEY=s9Yw8MdroJlbR4eKA8IdNzfy2e6pZiYF3swivgzy \
  -e APCA_API_BASE_URL=https://paper-api.alpaca.markets \
  trading_bot_trading-bot:latest
```

## **Common Issues & Solutions**

### **Container Won't Start**
```bash
# Check if port is already in use
sudo netstat -tlnp | grep :80

# Check Docker logs for errors
sudo docker logs trading-bot

# Verify image exists
sudo docker images | grep trading_bot
```

### **Dashboard Not Accessible**
```bash
# Test local access first
curl http://localhost:80

# Check firewall rules
sudo ufw status

# Verify container is binding to all interfaces
sudo docker exec trading-bot netstat -tlnp | grep :8080
```

### **API Connection Issues**
```bash
# Test API connectivity from container
sudo docker exec trading-bot curl -I https://paper-api.alpaca.markets

# Check environment variables
sudo docker exec trading-bot env | grep APCA

# Verify API credentials format
sudo docker exec trading-bot python -c "
import os
print('Key format OK:', len(os.getenv('APCA_API_KEY_ID', '')) > 10)
print('Secret format OK:', len(os.getenv('APCA_API_SECRET_KEY', '')) > 20)
"
```

## **Contact & Support**

### **Log Analysis**
When reporting issues, always include:
```bash
# System info
uname -a
sudo docker version
sudo docker ps -a

# Recent logs
sudo docker logs trading-bot --tail 100

# Container inspection
sudo docker inspect trading-bot
```

---

**Save this guide for easy reference when managing your trading bot on Oracle Cloud Infrastructure!**