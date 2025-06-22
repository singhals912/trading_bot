# ===============================================
# GRAFANA MONITORING SETUP FOR TRADING BOT
# ===============================================

"""
This creates a metrics exporter that feeds data to Grafana
Grafana will show real-time charts, alerts, and dashboards
"""

import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import threading
from pathlib import Path

class TradingBotMetricsExporter:
    """
    Exports trading bot metrics to formats that Grafana can read
    Supports: SQLite, JSON files, and Prometheus metrics
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger('MetricsExporter')
        
        # Create metrics database
        self.db_path = 'metrics.db'
        self.init_database()
        
        # Metrics collection interval
        self.collection_interval = 60  # 1 minute
        self.running = False
        
    def init_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_metrics (
                timestamp INTEGER PRIMARY KEY,
                daily_pnl REAL,
                total_equity REAL,
                positions_count INTEGER,
                win_rate REAL,
                total_trades INTEGER,
                system_health REAL,
                api_response_time REAL,
                memory_usage REAL,
                cpu_usage REAL
            )
        ''')
        
        # Create trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                price REAL,
                pnl REAL,
                strategy TEXT
            )
        ''')
        
        # Create positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                timestamp INTEGER,
                symbol TEXT,
                quantity REAL,
                entry_price REAL,
                current_price REAL,
                unrealized_pnl REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def collect_metrics(self) -> Dict:
        """Collect current metrics from the bot"""
        try:
            # Read from dashboard.json
            dashboard_data = {}
            if Path('dashboard.json').exists():
                with open('dashboard.json', 'r') as f:
                    dashboard_data = json.load(f)
            
            # Read bot state
            bot_state = {}
            if Path('bot_state.json').exists():
                with open('bot_state.json', 'r') as f:
                    bot_state = json.load(f)
            
            # System metrics
            import psutil
            process = None
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if 'python' in proc.info['name'] and any('main.py' in cmd for cmd in proc.info['cmdline']):
                        process = psutil.Process(proc.info['pid'])
                        break
            except:
                pass
            
            memory_usage = process.memory_info().rss / 1024 / 1024 if process else 0  # MB
            cpu_usage = process.cpu_percent() if process else 0
            
            # Compile metrics
            metrics = {
                'timestamp': int(time.time()),
                'daily_pnl': dashboard_data.get('daily_pnl', 0),
                'total_equity': dashboard_data.get('equity', 0),
                'positions_count': dashboard_data.get('positions', 0),
                'win_rate': dashboard_data.get('win_rate', 0),
                'total_trades': len(bot_state.get('trades', [])) if 'trades' in bot_state else dashboard_data.get('total_trades', 0),
                'system_health': 0.85,  # Placeholder - you can implement actual health scoring
                'api_response_time': 0.5,  # Placeholder - measure actual API response times
                'memory_usage': memory_usage,
                'cpu_usage': cpu_usage
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {str(e)}")
            return {}
    
    def store_metrics(self, metrics: Dict):
        """Store metrics in database"""
        if not metrics:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO bot_metrics 
                (timestamp, daily_pnl, total_equity, positions_count, win_rate, 
                 total_trades, system_health, api_response_time, memory_usage, cpu_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics['timestamp'],
                metrics['daily_pnl'],
                metrics['total_equity'],
                metrics['positions_count'],
                metrics['win_rate'],
                metrics['total_trades'],
                metrics['system_health'],
                metrics['api_response_time'],
                metrics['memory_usage'],
                metrics['cpu_usage']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {str(e)}")
    
    def export_prometheus_metrics(self, metrics: Dict):
        """Export metrics in Prometheus format"""
        try:
            prometheus_content = f"""# HELP trading_bot_daily_pnl Daily profit and loss
# TYPE trading_bot_daily_pnl gauge
trading_bot_daily_pnl {metrics['daily_pnl']}

# HELP trading_bot_equity Total account equity
# TYPE trading_bot_equity gauge
trading_bot_equity {metrics['total_equity']}

# HELP trading_bot_positions Number of open positions
# TYPE trading_bot_positions gauge
trading_bot_positions {metrics['positions_count']}

# HELP trading_bot_win_rate Win rate percentage
# TYPE trading_bot_win_rate gauge
trading_bot_win_rate {metrics['win_rate']}

# HELP trading_bot_total_trades Total number of trades
# TYPE trading_bot_total_trades counter
trading_bot_total_trades {metrics['total_trades']}

# HELP trading_bot_system_health System health score
# TYPE trading_bot_system_health gauge
trading_bot_system_health {metrics['system_health']}

# HELP trading_bot_memory_usage Memory usage in MB
# TYPE trading_bot_memory_usage gauge
trading_bot_memory_usage {metrics['memory_usage']}

# HELP trading_bot_cpu_usage CPU usage percentage
# TYPE trading_bot_cpu_usage gauge
trading_bot_cpu_usage {metrics['cpu_usage']}
"""
            
            with open('metrics.prom', 'w') as f:
                f.write(prometheus_content)
                
        except Exception as e:
            self.logger.error(f"Failed to export Prometheus metrics: {str(e)}")
    
    def export_json_metrics(self, metrics: Dict):
        """Export metrics as JSON for simple HTTP endpoint"""
        try:
            with open('metrics.json', 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to export JSON metrics: {str(e)}")
    
    def start_collection(self):
        """Start metrics collection in background thread"""
        self.running = True
        
        def collection_loop():
            while self.running:
                try:
                    metrics = self.collect_metrics()
                    if metrics:
                        self.store_metrics(metrics)
                        self.export_prometheus_metrics(metrics)
                        self.export_json_metrics(metrics)
                        self.logger.debug(f"Metrics collected: {metrics['timestamp']}")
                except Exception as e:
                    self.logger.error(f"Metrics collection error: {str(e)}")
                
                time.sleep(self.collection_interval)
        
        thread = threading.Thread(target=collection_loop, daemon=True)
        thread.start()
        self.logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        self.logger.info("Metrics collection stopped")

# ===============================================
# GRAFANA DOCKER SETUP SCRIPT
# ===============================================

DOCKER_COMPOSE_CONTENT = '''version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    container_name: trading-bot-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=trading123
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: trading-bot-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: trading-bot-node-exporter
    ports:
      - "9100:9100"
    restart: unless-stopped

volumes:
  grafana-storage:
  prometheus-data:
'''

PROMETHEUS_CONFIG = '''global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'trading-bot'
    static_configs:
      - targets: ['host.docker.internal:8000']
    scrape_interval: 30s
    metrics_path: '/metrics'

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
'''

GRAFANA_DATASOURCE = '''{
  "apiVersion": 1,
  "datasources": [
    {
      "name": "Prometheus",
      "type": "prometheus",
      "url": "http://prometheus:9090",
      "access": "proxy",
      "isDefault": true
    }
  ]
}'''

GRAFANA_DASHBOARD = '''{
  "dashboard": {
    "id": null,
    "title": "Trading Bot Dashboard",
    "tags": ["trading", "bot"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Daily P&L",
        "type": "stat",
        "targets": [
          {
            "expr": "trading_bot_daily_pnl",
            "legendFormat": "Daily P&L"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD",
            "thresholds": {
              "steps": [
                {"color": "red", "value": -1000},
                {"color": "yellow", "value": 0},
                {"color": "green", "value": 500}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "title": "Account Equity",
        "type": "timeseries",
        "targets": [
          {
            "expr": "trading_bot_equity",
            "legendFormat": "Total Equity"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD"
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0}
      },
      {
        "title": "Active Positions",
        "type": "stat",
        "targets": [
          {
            "expr": "trading_bot_positions",
            "legendFormat": "Positions"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
      },
      {
        "title": "Win Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "trading_bot_win_rate",
            "legendFormat": "Win Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 50},
                {"color": "green", "value": 65}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "title": "System Health",
        "type": "timeseries",
        "targets": [
          {
            "expr": "trading_bot_system_health",
            "legendFormat": "Health Score"
          },
          {
            "expr": "trading_bot_memory_usage",
            "legendFormat": "Memory (MB)"
          },
          {
            "expr": "trading_bot_cpu_usage",
            "legendFormat": "CPU %"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "refresh": "30s"
  }
}'''

def setup_grafana_monitoring():
    """Setup Grafana monitoring for trading bot"""
    
    # Create directories
    Path('grafana/dashboards').mkdir(parents=True, exist_ok=True)
    Path('grafana/datasources').mkdir(parents=True, exist_ok=True)
    
    # Write configuration files
    with open('docker-compose.yml', 'w') as f:
        f.write(DOCKER_COMPOSE_CONTENT)
    
    with open('prometheus.yml', 'w') as f:
        f.write(PROMETHEUS_CONFIG)
    
    with open('grafana/datasources/prometheus.yml', 'w') as f:
        f.write(GRAFANA_DATASOURCE)
    
    with open('grafana/dashboards/trading-bot.json', 'w') as f:
        f.write(GRAFANA_DASHBOARD)
    
    print("✅ Grafana configuration files created!")
    print("\nNext steps:")
    print("1. Install Docker Desktop")
    print("2. Run: docker-compose up -d")
    print("3. Open http://localhost:3000")
    print("4. Login with admin/trading123")
    print("5. Import the trading bot dashboard")

# ===============================================
# SIMPLE HTTP METRICS SERVER
# ===============================================

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class MetricsHTTPHandler(BaseHTTPRequestHandler):
    """Simple HTTP server to serve metrics to Prometheus"""
    
    def do_GET(self):
        if self.path == '/metrics':
            try:
                with open('metrics.prom', 'r') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.send_error(404, "Metrics not found")
        else:
            self.send_error(404, "Not found")
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_metrics_server(port=8000):
    """Start HTTP server for metrics"""
    server = HTTPServer(('localhost', port), MetricsHTTPHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"✅ Metrics server started on http://localhost:{port}/metrics")
    return server

# ===============================================
# INTEGRATION WITH MAIN BOT
# ===============================================

# ADD THIS TO YOUR main.py in the AutonomousTradingBot.__init__ method:

"""
# Initialize metrics exporter
try:
    from metrics_exporter import TradingBotMetricsExporter, start_metrics_server
    
    self.metrics_exporter = TradingBotMetricsExporter(self)
    self.metrics_exporter.start_collection()
    
    # Start HTTP server for Prometheus
    self.metrics_server = start_metrics_server(port=8000)
    
    self.logger.info("Metrics exporter and HTTP server started")
except Exception as e:
    self.logger.warning(f"Failed to start metrics exporter: {str(e)}")
    self.metrics_exporter = None
"""

if __name__ == "__main__":
    setup_grafana_monitoring()
    
    # Test metrics collection
    exporter = TradingBotMetricsExporter()
    metrics = exporter.collect_metrics()
    print("Sample metrics:", metrics)
    
    exporter.start_collection()
    start_metrics_server()
    
    print("Metrics collection started. Check metrics.json and metrics.prom files.")
    print("Run docker-compose up -d to start Grafana")