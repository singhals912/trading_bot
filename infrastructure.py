# infrastructure_setup.py
"""
Cost-optimized infrastructure for <$10/day operation
Hybrid approach: Local + Cloud backup
"""

import os
import json
import subprocess
from typing import Dict, Optional
from datetime import datetime, timedelta

class HybridInfrastructure:
    """
    Hybrid infrastructure management
    - Primary: Local MacBook execution
    - Backup: GCP Compute Engine (preemptible)
    - Cost: ~$5-8/day
    """
    
    def __init__(self):
        self.config = {
            'local': {
                'enabled': True,
                'health_check_interval': 300,  # 5 minutes
                'auto_restart': True
            },
            'gcp': {
                'enabled': False,  # Enable only as backup
                'project_id': 'your-project-id',
                'zone': 'us-central1-a',
                'instance_type': 'e2-micro',  # Free tier eligible
                'preemptible': True,  # 80% cheaper
                'max_daily_cost': 5.0
            }
        }
        
    def setup_local_environment(self):
        """Setup MacBook for 24/7 operation"""
        setup_script = """
#!/bin/bash

# Keep Mac awake
caffeinate -d -i -s &

# Setup LaunchAgent for auto-start
cat > ~/Library/LaunchAgents/com.trading.bot.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$HOME/trading_bot/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/trading_bot/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/trading_bot/logs/stderr.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.trading.bot.plist

# Setup monitoring
pip install psutil schedule twilio

echo "Local environment setup complete"
"""
        
        with open('setup_local.sh', 'w') as f:
            f.write(setup_script)
        
        subprocess.run(['chmod', '+x', 'setup_local.sh'])
        print("Run ./setup_local.sh to complete local setup")

class CostOptimizedDataManager:
    """
    Minimize data costs while maintaining quality
    """
    
    def __init__(self):
        self.data_sources = {
            'primary': {
                'provider': 'alpaca',  # Free with account
                'cost': 0,
                'limits': {'requests_per_minute': 200}
            },
            'backup': {
                'provider': 'yahoo_finance',  # Free
                'cost': 0,
                'limits': {'requests_per_minute': 60}
            },
            'premium': {
                'provider': 'polygon',  # $9/month for stocks
                'cost': 0.30,  # per day
                'enabled': False
            }
        }
        
    def get_optimized_data(self, symbol: str, data_type: str):
        """Get data from most cost-effective source"""
        # Try free sources first
        for source_name, source_config in self.data_sources.items():
            if source_config['cost'] == 0:
                try:
                    return self._fetch_from_source(source_name, symbol, data_type)
                except:
                    continue
                    
        # Fall back to paid if necessary
        if self.data_sources['premium']['enabled']:
            return self._fetch_from_source('premium', symbol, data_type)
            
    def _fetch_from_source(self, source: str, symbol: str, data_type: str):
        """Fetch data from specific source"""
        if source == 'alpaca':
            # Use existing Alpaca client
            pass
        elif source == 'yahoo_finance':
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            if data_type == 'quote':
                return ticker.info
            elif data_type == 'history':
                return ticker.history(period='1d')

class ResourceMonitor:
    """Monitor and optimize resource usage"""
    
    def __init__(self):
        self.metrics = {
            'cpu_percent': [],
            'memory_mb': [],
            'network_mb': [],
            'api_calls': 0,
            'estimated_cost': 0.0
        }
        
    def optimize_resources(self):
        """Optimize resource usage to minimize costs"""
        import psutil
        import gc
        
        # Get current usage
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=1)
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Optimize if needed
        if memory_mb > 500:  # If using >500MB
            gc.collect()  # Force garbage collection
            
        if cpu_percent > 80:  # If CPU >80%
            # Reduce processing frequency
            return 'throttle'
            
        return 'normal'

class BackupManager:
    """Manage automated backups with minimal cost"""
    
    def __init__(self):
        self.backup_config = {
            'local': {
                'path': '~/trading_bot_backups',
                'retention_days': 7
            },
            'cloud': {
                'provider': 'google_drive',  # Free 15GB
                'path': '/TradingBot/backups',
                'critical_only': True  # Only backup critical data
            }
        }
        
    def backup_critical_data(self):
        """Backup only critical data to minimize storage"""
        critical_files = [
            'positions.json',
            'trades.log',
            'config.json',
            'performance_*.json'
        ]
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'positions': self._get_positions(),
            'recent_trades': self._get_recent_trades(),
            'config': self._get_config()
        }
        
        # Compress and save
        import gzip
        backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
        
        with gzip.open(backup_path, 'wt') as f:
            json.dump(backup_data, f)
            
        # Upload to cloud if size is small
        if os.path.getsize(backup_path) < 10 * 1024 * 1024:  # <10MB
            self._upload_to_cloud(backup_path)

# Terraform configuration for GCP (when needed)
TERRAFORM_CONFIG = """
# main.tf - Minimal GCP setup for <$10/day

variable "project_id" {
  default = "your-trading-bot-project"
}

resource "google_compute_instance" "trading_bot_backup" {
  name         = "trading-bot-backup"
  machine_type = "e2-micro"  # 0.25 vCPU, 1GB RAM - ~$6/month
  zone         = "us-central1-a"
  
  # Use preemptible for 80% discount
  scheduling {
    preemptible       = true
    automatic_restart = false
  }
  
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 10  # Minimum size
    }
  }
  
  network_interface {
    network = "default"
    access_config {}  # Ephemeral IP
  }
  
  # Only run during market hours to save costs
  metadata_startup_script = <<-EOF
    #!/bin/bash
    # Check if market hours (9:30 AM - 4:00 PM ET)
    HOUR=$(date +%H)
    if [ $HOUR -ge 9 ] && [ $HOUR -lt 16 ]; then
      cd /home/trading_bot
      python3 main.py
    else
      # Shutdown to save costs
      sudo shutdown -h now
    fi
  EOF
}

# Cloud Scheduler to start/stop instance
resource "google_cloud_scheduler_job" "start_trading_bot" {
  name     = "start-trading-bot"
  schedule = "25 9 * * MON-FRI"  # 9:25 AM ET weekdays
  
  http_target {
    uri         = "https://compute.googleapis.com/compute/v1/projects/${var.project_id}/zones/us-central1-a/instances/trading-bot-backup/start"
    http_method = "POST"
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}

# Budget alert
resource "google_billing_budget" "trading_bot_budget" {
  billing_account = var.billing_account
  display_name    = "Trading Bot Daily Budget"
  
  budget_filter {
    projects = ["projects/${var.project_id}"]
  }
  
  amount {
    specified_amount {
      currency_code = "USD"
      units         = "10"  # $10 daily limit
    }
  }
  
  threshold_rules {
    threshold_percent = 0.8  # Alert at 80%
  }
}
"""

def estimate_daily_cost():
    """Estimate infrastructure costs"""
    costs = {
        'local_electricity': 0.50,  # MacBook M1 ~30W continuous
        'gcp_backup': 3.00,  # Preemptible e2-micro for 6 hours
        'data_api': 0.30,  # Polygon if needed
        'monitoring': 0.00,  # Free tier services
        'storage': 0.10,  # Minimal cloud storage
    }
    
    total = sum(costs.values())
    print(f"Estimated daily cost: ${total:.2f}")
    print("Breakdown:")
    for item, cost in costs.items():
        print(f"  {item}: ${cost:.2f}")
        
    return total