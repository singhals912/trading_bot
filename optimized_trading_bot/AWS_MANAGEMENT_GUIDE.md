# AWS Trading Bot Management Guide

## **SSH Connection**
```bash
# Connect to your AWS EC2 instance
ssh -i /Users/ss/Downloads/trading-bot-key.pem ubuntu@54.91.93.69
```

## **Basic Container Management**

### **Start the Trading Bot**
```bash
# Start if container exists but is stopped
docker start trading-bot

# Or run fresh container (if doesn't exist)
docker run -d --name trading-bot --restart unless-stopped \
  -p 80:8080 -p 8080:8080 --env-file .env \
  -v /opt/trading_bot/data:/app/data \
  trading_bot_trading-bot:latest
```

### **Stop the Trading Bot**
```bash
# Graceful stop
docker stop trading-bot

# Force stop (if unresponsive)
docker kill trading-bot
```

### **Pause/Resume Trading Bot**
```bash
# Pause (stops execution but keeps container)
docker pause trading-bot

# Resume from pause
docker unpause trading-bot
```

### **Restart the Trading Bot**
```bash
# Restart existing container
docker restart trading-bot
```

## **Status & Monitoring**

### **Check Container Status**
```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# Detailed container info
docker inspect trading-bot

# Resource usage
docker stats trading-bot
```

### **View Logs**
```bash
# Real-time logs (follow)
docker logs trading-bot -f

# Last 50 lines
docker logs trading-bot --tail 50

# Logs with timestamps
docker logs trading-bot -t

# Logs since specific time
docker logs trading-bot --since="2025-06-28T20:00:00"
```

## **AWS Instance Management**

### **Check Instance Status**
```bash
# From your local machine
aws ec2 describe-instances --instance-ids i-065695c0be57280c1 --region us-east-1 \
  --query 'Reservations[0].Instances[0].State.Name' --output text

# Or use the monitoring script
./aws_monitor.sh status
```

### **Start/Stop AWS Instance**
```bash
# Stop instance (from local machine)
aws ec2 stop-instances --instance-ids i-065695c0be57280c1 --region us-east-1

# Start instance (from local machine)
aws ec2 start-instances --instance-ids i-065695c0be57280c1 --region us-east-1

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids i-065695c0be57280c1 --region us-east-1
```

### **Get Current Public IP**
```bash
# Get public IP (may change after restart)
aws ec2 describe-instances --instance-ids i-065695c0be57280c1 --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

## **Debugging**

### **Access Container Shell**
```bash
# Execute bash inside running container
docker exec -it trading-bot bash

# Run specific commands inside container
docker exec trading-bot ls -la /app
docker exec trading-bot cat /app/.env
docker exec trading-bot ps aux
```

### **Check Environment Variables**
```bash
# View all env vars in container
docker exec trading-bot env

# Check specific trading bot variables
docker exec trading-bot env | grep APCA
```

### **File System Access**
```bash
# Copy files from container to host
docker cp trading-bot:/app/logs/trading_bot.log ./

# Copy files from host to container
docker cp ./config.json trading-bot:/app/

# View container filesystem
docker exec trading-bot find /app -name "*.log"
```

### **Performance Debugging**
```bash
# Container resource usage
docker stats trading-bot --no-stream

# Process list inside container
docker exec trading-bot top

# Disk usage inside container
docker exec trading-bot df -h

# System resources on AWS instance
htop
free -h
df -h
```

## **Advanced Management**

### **Container Rebuild & Update**
```bash
# Stop and remove current container
docker stop trading-bot
docker rm trading-bot

# Rebuild image (if you updated code)
cd /opt/trading_bot
docker build -t trading_bot_trading-bot .

# Run new container
docker run -d --name trading-bot --restart unless-stopped \
  -p 80:8080 -p 8080:8080 --env-file .env \
  -v /opt/trading_bot/data:/app/data \
  trading_bot_trading-bot:latest
```

### **Code Updates from Local Machine**
```bash
# From your local machine - sync updated files
rsync -avz -e "ssh -i /Users/ss/Downloads/trading-bot-key.pem" \
    --exclude='venv' --exclude='logs/*' --exclude='__pycache__' \
    /Users/ss/Downloads/Code/trading_bot/optimized_trading_bot/ \
    ubuntu@54.91.93.69:/opt/trading_bot/

# Then SSH to AWS and rebuild
ssh -i /Users/ss/Downloads/trading-bot-key.pem ubuntu@54.91.93.69
cd /opt/trading_bot
docker stop trading-bot && docker rm trading-bot
docker build -t trading_bot_trading-bot .
docker run -d --name trading-bot --restart unless-stopped \
  -p 80:8080 -p 8080:8080 --env-file .env \
  -v /opt/trading_bot/data:/app/data \
  trading_bot_trading-bot:latest
```

### **Environment Variable Updates**
```bash
# Update .env file on AWS instance
nano /opt/trading_bot/.env

# Restart container to pick up changes
docker restart trading-bot
```

## **Monitoring Scripts**

### **Management Script Usage (On AWS Instance)**
```bash
# Use the pre-installed management script
trading-bot-manage start      # Start bot
trading-bot-manage stop       # Stop bot
trading-bot-manage restart    # Restart bot
trading-bot-manage status     # Check status
trading-bot-manage logs       # View logs
trading-bot-manage health     # Health check
```

### **Local Monitoring Script**
```bash
# From your local machine
./aws_monitor.sh              # Interactive menu
./aws_monitor.sh status       # Quick status
./aws_monitor.sh restart      # Restart bot
./aws_monitor.sh logs         # View logs
./aws_monitor.sh metrics      # Performance metrics
./aws_monitor.sh ssh          # SSH to instance
./aws_monitor.sh monitor      # Auto-monitoring (60s intervals)
```

## **Network & Security**

### **Security Group Management**
```bash
# List security groups
aws ec2 describe-security-groups --group-names trading-bot-sg --region us-east-1

# Add new port (e.g., 443 for HTTPS)
aws ec2 authorize-security-group-ingress \
  --group-name trading-bot-sg \
  --protocol tcp --port 443 --cidr 0.0.0.0/0 \
  --region us-east-1

# Remove port access
aws ec2 revoke-security-group-ingress \
  --group-name trading-bot-sg \
  --protocol tcp --port 8080 --cidr 0.0.0.0/0 \
  --region us-east-1
```

### **Network Diagnostics**
```bash
# Test dashboard connectivity
curl -I http://54.91.93.69
curl -I http://54.91.93.69/api/status

# Check port bindings on AWS instance
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8080

# Test from inside container
docker exec trading-bot curl -I http://localhost:8080
```

## **Backup & Recovery**

### **Backup Procedures**
```bash
# Backup configuration and data
tar -czf trading-bot-backup-$(date +%Y%m%d).tar.gz \
  /opt/trading_bot/.env \
  /opt/trading_bot/config/ \
  /opt/trading_bot/data/ \
  /opt/trading_bot/logs/

# Backup Docker image
docker save trading_bot_trading-bot:latest > trading-bot-image-$(date +%Y%m%d).tar

# Download backup to local machine
scp -i /Users/ss/Downloads/trading-bot-key.pem \
  ubuntu@54.91.93.69:~/trading-bot-backup-*.tar.gz ./
```

### **Create AMI Snapshot**
```bash
# From local machine - create AMI backup
aws ec2 create-image \
  --instance-id i-065695c0be57280c1 \
  --name "trading-bot-backup-$(date +%Y%m%d)" \
  --description "Trading bot AMI backup" \
  --region us-east-1
```

### **Restore Procedures**
```bash
# Restore from backup
tar -xzf trading-bot-backup-YYYYMMDD.tar.gz -C /

# Restore Docker image
docker load < trading-bot-image-YYYYMMDD.tar

# Restart services
docker restart trading-bot
```

## **Cost Management**

### **Monitor AWS Costs**
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=2025-06-01,End=2025-06-30 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --region us-east-1

# Set up billing alerts (replace with your email)
aws sns create-topic --name trading-bot-billing-alerts --region us-east-1
```

### **Free Tier Usage**
```bash
# Monitor EC2 usage
aws ec2 describe-instances --region us-east-1 \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,LaunchTime]'

# Check EBS volume usage
aws ec2 describe-volumes --region us-east-1
```

## **Troubleshooting**

### **Container Won't Start**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check container logs for errors
docker logs trading-bot

# Check system resources
free -h
df -h

# Rebuild container from scratch
docker stop trading-bot && docker rm trading-bot
docker rmi trading_bot_trading-bot
docker build -t trading_bot_trading-bot .
```

### **Dashboard Not Accessible**
```bash
# Test local access first
curl -I http://localhost:80

# Check if container is running
docker ps | grep trading-bot

# Check security groups
aws ec2 describe-security-groups --group-names trading-bot-sg --region us-east-1

# Check if AWS instance has public IP
aws ec2 describe-instances --instance-ids i-065695c0be57280c1 --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress'
```

### **High Memory Usage**
```bash
# Check container memory usage
docker stats trading-bot --no-stream

# Check system memory
free -h

# Restart container if memory leak
docker restart trading-bot

# Add memory limits to container
docker run -d --name trading-bot --restart unless-stopped \
  --memory="800m" --cpus="0.8" \
  -p 80:8080 -p 8080:8080 --env-file .env \
  trading_bot_trading-bot:latest
```

### **API Connection Issues**
```bash
# Test API connectivity from container
docker exec trading-bot curl -I https://paper-api.alpaca.markets

# Check environment variables
docker exec trading-bot env | grep APCA

# Verify API credentials format
docker exec trading-bot python -c "
import os
print('API Key loaded:', bool(os.getenv('APCA_API_KEY_ID')))
print('Secret loaded:', bool(os.getenv('APCA_API_SECRET_KEY')))
print('Base URL:', os.getenv('APCA_API_BASE_URL'))
"
```

## **Performance Optimization**

### **Container Optimization**
```bash
# Run with optimized settings
docker run -d --name trading-bot --restart unless-stopped \
  --memory="800m" --cpus="0.8" \
  --ulimit nofile=65536:65536 \
  -p 80:8080 -p 8080:8080 --env-file .env \
  -v /opt/trading_bot/data:/app/data \
  trading_bot_trading-bot:latest
```

### **System Optimization**
```bash
# Enable swap if running out of memory
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## **Automated Monitoring**

### **Health Check Cron Job**
```bash
# Add to crontab for automated monitoring
(crontab -l 2>/dev/null || echo ""; echo "*/5 * * * * curl -f http://localhost:80/api/status > /dev/null 2>&1 || docker restart trading-bot") | crontab -
```

### **Log Rotation**
```bash
# Set up log rotation
sudo tee /etc/logrotate.d/docker-trading-bot > /dev/null << 'EOF'
/var/lib/docker/containers/*/*.log {
    rotate 5
    daily
    compress
    size 50M
    missingok
    delaycompress
    copytruncate
}
EOF
```

## **Dashboard Access**

### **URLs**
- **Main Dashboard**: http://54.91.93.69
- **API Status**: http://54.91.93.69/api/status
- **Health Check**: http://54.91.93.69/api/health
- **Metrics**: http://54.91.93.69/api/metrics

### **API Testing**
```bash
# Test all endpoints
curl http://54.91.93.69/api/status
curl http://54.91.93.69/api/metrics
curl http://54.91.93.69/api/portfolio
curl http://54.91.93.69/api/config
```

## **Quick Reference Commands**

### **Daily Operations**
```bash
# Quick status check
docker ps | grep trading-bot && echo "✅ Running" || echo "❌ Stopped"

# Quick restart
docker restart trading-bot

# Quick log check
docker logs trading-bot --tail 20

# Quick health check
curl -s http://54.91.93.69/api/status | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"Status: {data.get('status', 'Unknown')}\")
    print(f\"Uptime: {data.get('uptime', 'Unknown')}\")
except:
    print('API not responding')
"
```

### **Emergency Procedures**
```bash
# Emergency stop everything
docker kill trading-bot
docker rm trading-bot

# Emergency restart
docker restart trading-bot

# Emergency instance reboot (from local machine)
aws ec2 reboot-instances --instance-ids i-065695c0be57280c1 --region us-east-1
```

## **Important File Locations**

### **On AWS Instance**
- **Project Directory**: `/opt/trading_bot/`
- **Environment File**: `/opt/trading_bot/.env`
- **Source Code**: `/opt/trading_bot/src/`
- **Configuration**: `/opt/trading_bot/config/`
- **Data Directory**: `/opt/trading_bot/data/`
- **Management Script**: `/usr/local/bin/trading-bot-manage`

### **Inside Container**
- **Application Root**: `/app/`
- **Source Code**: `/app/src/`
- **Logs**: `/app/logs/` (if logging to files)
- **Data**: `/app/data/`
- **Configuration**: `/app/config/`

### **On Local Machine**
- **SSH Key**: `/Users/ss/Downloads/trading-bot-key.pem`
- **Project Directory**: `/Users/ss/Downloads/Code/trading_bot/optimized_trading_bot/`
- **AWS Config**: `aws_deployment_config.txt`
- **Monitoring Script**: `./aws_monitor.sh`

## **AWS Free Tier Monitoring**

### **Usage Limits**
- **EC2**: 750 hours/month (31 days × 24 hours = 744 hours)
- **EBS**: 30 GB General Purpose SSD
- **Data Transfer**: 15 GB/month outbound
- **Duration**: 12 months from account creation

### **Usage Monitoring**
```bash
# Check instance uptime
aws ec2 describe-instances --instance-ids i-065695c0be57280c1 --region us-east-1 \
  --query 'Reservations[0].Instances[0].LaunchTime'

# Monitor data transfer (check AWS billing dashboard)
# Monitor EBS usage
aws ec2 describe-volumes --region us-east-1
```

## **Security Best Practices**

### **SSH Key Security**
```bash
# Ensure proper key permissions
chmod 600 /Users/ss/Downloads/trading-bot-key.pem

# Backup SSH key securely
cp /Users/ss/Downloads/trading-bot-key.pem ~/Documents/aws-keys-backup/
```

### **Environment Variables Security**
```bash
# Never expose API keys in logs
docker logs trading-bot | grep -v "APCA"

# Regularly rotate API keys (in Alpaca dashboard)
# Update .env file with new keys
# Restart container: docker restart trading-bot
```

## **Support & Documentation**

### **AWS Resources**
- **EC2 User Guide**: https://docs.aws.amazon.com/ec2/
- **AWS CLI Reference**: https://docs.aws.amazon.com/cli/
- **Free Tier FAQ**: https://aws.amazon.com/free/faqs/

### **Monitoring URLs**
- **Dashboard**: http://54.91.93.69
- **AWS Console**: https://console.aws.amazon.com/ec2/
- **Alpaca Dashboard**: https://app.alpaca.markets/

---

**📖 Save this guide for easy reference when managing your trading bot on AWS!**

**🚀 Your trading bot is now running reliably on AWS Free Tier!**