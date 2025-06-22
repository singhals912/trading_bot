import json
import time
import sqlite3
from datetime import datetime
from pathlib import Path
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

class TradingBotMetricsExporter:
    def __init__(self):
        self.logger = logging.getLogger('MetricsExporter')
        self.running = False
        
    def collect_metrics(self):
        """Collect metrics from bot files"""
        try:
            # Read dashboard.json
            dashboard_data = {}
            if Path('dashboard.json').exists():
                with open('dashboard.json', 'r') as f:
                    dashboard_data = json.load(f)
            
            # Read bot_state.json
            bot_state = {}
            if Path('bot_state.json').exists():
                with open('bot_state.json', 'r') as f:
                    bot_state = json.load(f)
            
            # Get system metrics
            try:
                import psutil
                memory_mb = psutil.virtual_memory().used / 1024 / 1024
                cpu_percent = psutil.cpu_percent()
            except:
                memory_mb = 0
                cpu_percent = 0
            
            # Compile metrics
            metrics = {
                'daily_pnl': dashboard_data.get('daily_pnl', 0),
                'total_equity': dashboard_data.get('equity', 50000),  # Default if missing
                'positions_count': dashboard_data.get('positions', 0),
                'win_rate': dashboard_data.get('win_rate', 0),
                'total_trades': dashboard_data.get('total_trades', 0),
                'system_health': 85.0,  # Can be improved with actual health calculation
                'memory_usage_mb': memory_mb,
                'cpu_usage_percent': cpu_percent,
                'timestamp': time.time()
            }
            
            return metrics
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return {
                'daily_pnl': 0, 'total_equity': 50000, 'positions_count': 0,
                'win_rate': 0, 'total_trades': 0, 'system_health': 0,
                'memory_usage_mb': 0, 'cpu_usage_percent': 0, 'timestamp': time.time()
            }
    
    def export_prometheus_metrics(self, metrics):
        """Export in Prometheus format"""
        prometheus_content = f"""# Trading Bot Metrics
trading_bot_daily_pnl {metrics['daily_pnl']}
trading_bot_equity {metrics['total_equity']}
trading_bot_positions {metrics['positions_count']}
trading_bot_win_rate {metrics['win_rate']}
trading_bot_total_trades {metrics['total_trades']}
trading_bot_system_health {metrics['system_health']}
trading_bot_memory_usage_mb {metrics['memory_usage_mb']}
trading_bot_cpu_usage_percent {metrics['cpu_usage_percent']}
"""
        
        with open('metrics.prom', 'w') as f:
            f.write(prometheus_content)
    
    def start_collection(self):
        """Start collecting metrics every 30 seconds"""
        self.running = True
        
        def collection_loop():
            while self.running:
                try:
                    metrics = self.collect_metrics()
                    self.export_prometheus_metrics(metrics)
                    print(f"✅ Metrics updated: P&L=${metrics['daily_pnl']:.2f}, Positions={metrics['positions_count']}")
                except Exception as e:
                    print(f"❌ Metrics error: {e}")
                time.sleep(30)  # Update every 30 seconds
        
        thread = threading.Thread(target=collection_loop, daemon=True)
        thread.start()
        print("🚀 Metrics collection started")

class MetricsHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            try:
                with open('metrics.prom', 'r') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.send_error(404, "Metrics file not found")
        else:
            self.send_error(404, "Not found")
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

def start_metrics_server(port=8000):
    """Start HTTP server for Prometheus to scrape"""
    try:
        server = HTTPServer(('0.0.0.0', port), MetricsHTTPHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"🌐 Metrics server started on http://localhost:{port}/metrics")
        return server
    except Exception as e:
        print(f"❌ Failed to start metrics server: {e}")
        return None

if __name__ == "__main__":
    # Test the metrics collection
    exporter = TradingBotMetricsExporter()
    metrics = exporter.collect_metrics()
    print("📊 Sample metrics:", metrics)
    
    # Start collection and server
    exporter.start_collection()
    start_metrics_server()
    
    print("✅ Metrics system ready!")
    print("📊 Check http://localhost:8000/metrics to see Prometheus format")
    
    # Keep running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("🛑 Metrics exporter stopped")