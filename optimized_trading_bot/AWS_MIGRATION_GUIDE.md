# AWS Migration Guide - Automated Trading Bot Deployment

## 🚀 **One-Click Migration to AWS Free Tier**

This guide provides **maximum automation** to migrate your trading bot from OCI to AWS EC2 Free Tier with minimal manual intervention.

## **Prerequisites**

### 1. **AWS Account Setup**
- Create AWS account: https://aws.amazon.com/free/
- Verify email and phone number
- Add payment method (required but won't be charged for free tier)

### 2. **Install AWS CLI** (Automated)
The deployment script will automatically install AWS CLI if not present.

## **🎯 Super Simple 3-Step Deployment**

### **Step 1: Configure AWS Credentials (One-time)**
```bash
# Install AWS CLI (if not installed)
brew install awscli  # macOS

# Configure credentials
aws configure
```

**Enter when prompted:**
- AWS Access Key ID: (from AWS Console → Security Credentials)
- AWS Secret Access Key: (from AWS Console → Security Credentials)  
- Default region: `us-east-1`
- Default output format: `json`

### **Step 2: Run Automated Deployment**
```bash
# Navigate to your project directory
cd /Users/ss/Downloads/Code/trading_bot/optimized_trading_bot

# Make scripts executable
chmod +x aws_deploy_automation.sh
chmod +x aws_setup_trading_bot.sh
chmod +x aws_monitor.sh

# Run automated deployment (creates EC2 instance)
./aws_deploy_automation.sh
```

**This script automatically:**
- ✅ Creates EC2 instance (t3.micro - Free Tier)
- ✅ Sets up security groups (ports 22, 80, 8080)
- ✅ Creates SSH key pair
- ✅ Installs Docker and dependencies
- ✅ Gets public IP address
- ✅ Saves configuration for future use

### **Step 3: Deploy Trading Bot**
```bash
# Deploy and start trading bot (copies files, builds container)
./aws_setup_trading_bot.sh
```

**This script automatically:**
- ✅ Copies all project files to AWS
- ✅ Sets up environment variables
- ✅ Builds Docker container
- ✅ Starts trading bot
- ✅ Creates management scripts
- ✅ Verifies deployment

## **🎉 You're Done!**

Your trading bot will be accessible at the URL provided in the output.

## **📊 Monitoring & Management**

### **Interactive Management Tool**
```bash
# Run interactive management interface
./aws_monitor.sh
```

**Features:**
- ✅ Check instance/bot status
- ✅ Restart trading bot
- ✅ View real-time logs
- ✅ Performance metrics
- ✅ SSH access
- ✅ Auto-monitoring mode

### **Command Line Management**
```bash
# Quick status check
./aws_monitor.sh status

# Restart bot
./aws_monitor.sh restart

# View logs
./aws_monitor.sh logs

# Performance metrics
./aws_monitor.sh metrics

# SSH access
./aws_monitor.sh ssh

# Auto-monitor (refreshes every 60s)
./aws_monitor.sh monitor
```

### **Direct SSH Access**
```bash
# SSH command is saved in aws_deployment_config.txt
# Example:
ssh -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP
```

## **📋 Generated Files**

After running the deployment scripts, you'll have:

- `aws_deployment_config.txt` - Instance configuration
- `~/Downloads/trading-bot-key.pem` - SSH private key
- `aws_monitor.sh` - Management and monitoring tool

## **💰 AWS Free Tier Limits**

### **EC2 Free Tier (12 months)**
- **750 hours/month** of t2.micro or t3.micro instances
- **30 GB EBS storage**
- **15 GB data transfer out**

### **Always Free Services**
- **1 million Lambda requests/month**
- **1 GB CloudWatch logs**
- **5 GB S3 storage**

## **🔧 Management Commands**

### **On AWS Instance (after SSH)**
```bash
# Trading bot management
trading-bot-manage start      # Start bot
trading-bot-manage stop       # Stop bot
trading-bot-manage restart    # Restart bot
trading-bot-manage status     # Check status
trading-bot-manage logs       # View logs
trading-bot-manage health     # Health check

# Docker commands
docker ps                     # List containers
docker logs trading-bot       # View logs
docker restart trading-bot    # Restart container
docker stats trading-bot     # Resource usage
```

### **From Local Machine**
```bash
# Access dashboard
open http://YOUR_PUBLIC_IP

# SSH to instance
ssh -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP

# Monitor instance status
./aws_monitor.sh status

# Auto-restart if down
./aws_monitor.sh monitor
```

## **🚨 Troubleshooting**

### **Instance Won't Start**
```bash
# Check instance status
aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID

# Start instance if stopped
aws ec2 start-instances --instance-ids YOUR_INSTANCE_ID

# Or use monitoring script
./aws_monitor.sh status
```

### **Dashboard Not Accessible**
```bash
# Check security groups
aws ec2 describe-security-groups --group-names trading-bot-sg

# Test local access on instance
ssh -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP
curl http://localhost:80
```

### **Trading Bot Not Running**
```bash
# SSH to instance and check
ssh -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP
docker ps
docker logs trading-bot

# Restart if needed
docker restart trading-bot
```

### **SSH Connection Issues**
```bash
# Check key permissions
chmod 600 ~/Downloads/trading-bot-key.pem

# Verify instance is running
./aws_monitor.sh status

# Check security group allows SSH (port 22)
aws ec2 describe-security-groups --group-names trading-bot-sg
```

## **🔄 Updates & Maintenance**

### **Update Trading Bot Code**
```bash
# From local machine - re-run setup script
./aws_setup_trading_bot.sh

# Or manually sync files
rsync -avz -e "ssh -i ~/Downloads/trading-bot-key.pem" \
    --exclude='venv' --exclude='logs' \
    ./ ubuntu@YOUR_PUBLIC_IP:/opt/trading_bot/

# Rebuild container on AWS instance
ssh -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP
cd /opt/trading_bot
docker build -t trading_bot_trading-bot .
docker restart trading-bot
```

### **Backup Important Data**
```bash
# Backup configuration and logs
ssh -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP
tar -czf trading-bot-backup-$(date +%Y%m%d).tar.gz /opt/trading_bot/.env /opt/trading_bot/logs/

# Download backup to local machine
scp -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP:~/trading-bot-backup-*.tar.gz ./
```

## **💡 Advantages of AWS vs OCI**

### **AWS Free Tier Benefits**
- ✅ **More reliable** - No random shutdowns
- ✅ **750 hours/month** - Enough for continuous operation
- ✅ **Better documentation** and community support
- ✅ **Stable public IPs** during instance lifecycle
- ✅ **Superior monitoring** and alerting
- ✅ **12 months free** for new accounts

### **Performance Comparison**
| Feature | OCI Always Free | AWS Free Tier |
|---------|----------------|---------------|
| Reliability | ⚠️ Often stops | ✅ Very stable |
| CPU | 1 OCPU | 1-2 vCPU (burstable) |
| RAM | 1 GB | 1 GB |
| Storage | 50 GB | 30 GB |
| Duration | Forever | 12 months |
| Stability | ❌ Poor | ✅ Excellent |

## **📞 Support & Contact**

### **AWS Support**
- **Free Tier FAQ**: https://aws.amazon.com/free/faqs/
- **EC2 Documentation**: https://docs.aws.amazon.com/ec2/
- **AWS CLI Reference**: https://docs.aws.amazon.com/cli/

### **Monitoring Dashboard**
- **Main Dashboard**: http://YOUR_PUBLIC_IP
- **API Health**: http://YOUR_PUBLIC_IP/api/status
- **Metrics**: http://YOUR_PUBLIC_IP/api/metrics

### **Log Locations**
- **Trading Bot Logs**: `docker logs trading-bot`
- **System Logs**: `/var/log/syslog`
- **Application Logs**: `/opt/trading_bot/logs/`

---

## **🎯 Quick Reference Card**

```bash
# Deploy to AWS (one-time)
./aws_deploy_automation.sh
./aws_setup_trading_bot.sh

# Daily management
./aws_monitor.sh                    # Interactive menu
./aws_monitor.sh status             # Quick status
./aws_monitor.sh restart            # Restart bot
./aws_monitor.sh logs               # View logs

# SSH access
ssh -i ~/Downloads/trading-bot-key.pem ubuntu@YOUR_PUBLIC_IP

# Dashboard
open http://YOUR_PUBLIC_IP
```

**Your trading bot will be much more stable on AWS! 🚀**