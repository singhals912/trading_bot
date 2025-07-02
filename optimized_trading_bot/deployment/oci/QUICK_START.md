# 🚀 OCI Quick Start Guide

Deploy your Enhanced Trading Bot to Oracle Cloud Infrastructure in 15 minutes!

## 📋 Prerequisites
- OCI Always Free account (sign up at https://cloud.oracle.com)
- Your Alpaca API credentials
- SSH client (Terminal on Mac/Linux, PuTTY on Windows)

## ⚡ Quick Deployment

### 1. Create OCI Instance (5 minutes)
1. **Login to OCI Console** → **Compute** → **Instances** → **Create Instance**
2. **Configuration:**
   - Name: `trading-bot`
   - Image: `Canonical Ubuntu 22.04`
   - Shape: `VM.Standard.E2.1.Micro` (Always Free)
   - Network: Default VCN, Public subnet, Assign public IP
   - SSH: Upload your public key or generate new
3. **Security List:** Add ingress rule for port 8080 (TCP, 0.0.0.0/0)
4. **Create Instance** → Wait 2-3 minutes for provisioning

### 2. Setup Instance (5 minutes)
```bash
# Connect to your instance
ssh ubuntu@<YOUR_INSTANCE_PUBLIC_IP>

# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/your-repo/main/deployment/oci/setup-instance.sh | bash

# Logout and login again (for Docker group)
exit
ssh ubuntu@<YOUR_INSTANCE_PUBLIC_IP>
```

### 3. Upload Your Bot (2 minutes)
```bash
# Option A: Git clone (if you have a public repo)
cd ~/trading-bot
git clone https://github.com/your-username/your-trading-bot.git .

# Option B: SCP upload from your local machine
# Run this from your local machine:
scp -r /Users/ss/Downloads/Code/trading_bot/optimized_trading_bot/* ubuntu@<PUBLIC_IP>:~/trading-bot/
```

### 4. Configure & Deploy (3 minutes)
```bash
# On the OCI instance
cd ~/trading-bot

# Configure your API credentials
cp .env.example .env
nano .env  # Add your Alpaca API keys

# Deploy in production mode
./deployment/oci/deploy.sh production
```

## 🎉 That's It!

Your trading bot is now running 24/7 on OCI Always Free!

**Access your dashboard:** `http://<YOUR_PUBLIC_IP>:8080`

## 🔧 Management Commands

```bash
# Check status
./status.sh

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f

# Restart bot
sudo systemctl restart trading-bot

# Stop bot
sudo systemctl stop trading-bot

# Update bot (after code changes)
git pull
./deployment/oci/deploy.sh production
```

## 🛠️ Troubleshooting

**Can't access dashboard?**
- Check security list has port 8080 open
- Verify instance is running: `docker ps`

**Bot not starting?**
- Check logs: `docker-compose logs trading-bot`
- Verify .env file has correct API keys

**Out of memory?**
- Check resource usage: `free -h`
- Restart with: `sudo systemctl restart trading-bot`

## 💰 Cost Monitoring

✅ **Always Free Resources Used:**
- 1 Micro compute instance (2 available)
- ~50GB storage (200GB available)
- Minimal network usage

Your bot runs **completely free forever**! 🎯

## 🔒 Security Notes

- SSH key authentication (no passwords)
- Firewall configured (only ports 22, 8080 open)
- Non-root user in containers
- Regular security updates via auto-update

## 📈 Next Steps

1. **Monitor Performance:** Check dashboard regularly
2. **Set Alerts:** Configure email notifications for trades
3. **Backup Strategy:** Data automatically backed up to persistent storage
4. **Scale Up:** Add second Always Free instance for redundancy

Your Enhanced Trading Bot is now running professionally in the cloud! 🚀