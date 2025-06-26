# simple_mobile_dashboard.py
"""
Simple Mobile Dashboard for Trading Bot
Works with your existing bot setup
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import threading

class SimpleDashboard:
    """Simple dashboard that reads from your bot's existing files"""
    
    def __init__(self, port=8081):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Mobile dashboard"""
            return render_template_string(self.get_dashboard_html())
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for status"""
            return jsonify(self.get_bot_status())
        
        @self.app.route('/api/quick')
        def api_quick():
            """Quick status"""
            status = self.get_bot_status()
            return jsonify({
                'status': 'running' if status['files_found'] > 0 else 'unknown',
                'daily_pnl': status.get('daily_pnl', 0),
                'equity': status.get('equity', 0),
                'last_update': datetime.now().isoformat()
            })
    
    def get_bot_status(self):
        """Get bot status from existing files"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'files_found': 0,
            'daily_pnl': 0,
            'equity': 0,
            'positions': 0,
            'trades_today': 0,
            'bot_status': 'running',
            'uptime': 'unknown'
        }
        
        # Check bot_state.json
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    bot_data = json.load(f)
                status['files_found'] += 1
                status['daily_pnl'] = bot_data.get('daily_pnl', 0)
                status['positions'] = len(bot_data.get('positions', {}))
        except:
            pass
        
        # Check dashboard.json
        try:
            if os.path.exists('dashboard.json'):
                with open('dashboard.json', 'r') as f:
                    dash_data = json.load(f)
                status['files_found'] += 1
                status['equity'] = dash_data.get('account_equity', 0)
        except:
            pass
        
        # Check daily digest
        try:
            today_file = f"daily_digest_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(today_file):
                with open(today_file, 'r') as f:
                    daily_data = json.load(f)
                status['files_found'] += 1
                status['trades_today'] = daily_data.get('total_trades', 0)
        except:
            pass
        
        # Check log files for uptime
        try:
            log_file = Path('logs/algo_trading.log')
            if log_file.exists():
                status['files_found'] += 1
                # Get file modification time as rough uptime indicator
                mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                uptime_seconds = (datetime.now() - mod_time).total_seconds()
                status['uptime'] = f"{uptime_seconds/3600:.1f}h"
        except:
            pass
        
        return status
    
    def get_dashboard_html(self):
        """Get mobile dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff; padding: 20px; min-height: 100vh;
        }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .status-card { 
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 20px; margin-bottom: 20px; 
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .metric { 
            display: flex; justify-content: space-between; 
            margin: 15px 0; padding: 10px 0; 
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: rgba(255,255,255,0.8); }
        .metric-value { font-weight: bold; font-size: 1.1em; }
        .positive { color: #4ade80; }
        .negative { color: #f87171; }
        .status-running { color: #4ade80; }
        .status-error { color: #f87171; }
        .refresh-btn { 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white; border: none; padding: 15px 30px; 
            border-radius: 10px; width: 100%; margin-top: 20px; 
            font-size: 16px; font-weight: bold; cursor: pointer;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }
        .refresh-btn:hover { transform: translateY(-2px); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        @media (max-width: 480px) { .grid { grid-template-columns: 1fr; } }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Trading Bot Monitor</h1>
        <p id="lastUpdate" class="pulse">Connecting...</p>
    </div>
    
    <div class="status-card">
        <h3>🔋 Bot Status</h3>
        <div class="metric">
            <span class="metric-label">Status:</span>
            <span class="metric-value status-running" id="botStatus">RUNNING</span>
        </div>
        <div class="metric">
            <span class="metric-label">Uptime:</span>
            <span class="metric-value" id="uptime">Loading...</span>
        </div>
        <div class="metric">
            <span class="metric-label">Data Sources:</span>
            <span class="metric-value" id="dataSources">Loading...</span>
        </div>
    </div>
    
    <div class="grid">
        <div class="status-card">
            <h3>💰 Trading</h3>
            <div class="metric">
                <span class="metric-label">Daily P&L:</span>
                <span class="metric-value" id="dailyPnl">$0.00</span>
            </div>
            <div class="metric">
                <span class="metric-label">Account Equity:</span>
                <span class="metric-value" id="equity">$0.00</span>
            </div>
            <div class="metric">
                <span class="metric-label">Positions:</span>
                <span class="metric-value" id="positions">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Trades Today:</span>
                <span class="metric-value" id="tradesTotal">0</span>
            </div>
        </div>
        
        <div class="status-card">
            <h3>📊 Performance</h3>
            <div class="metric">
                <span class="metric-label">Mode:</span>
                <span class="metric-value">Paper Trading</span>
            </div>
            <div class="metric">
                <span class="metric-label">Strategy:</span>
                <span class="metric-value">Combined</span>
            </div>
            <div class="metric">
                <span class="metric-label">Capital:</span>
                <span class="metric-value">$20,000</span>
            </div>
            <div class="metric">
                <span class="metric-label">Risk/Trade:</span>
                <span class="metric-value">1.5%</span>
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
    
    <script>
        function refreshData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('lastUpdate').textContent = 'Error loading data';
                });
        }
        
        function updateDashboard(data) {
            const now = new Date().toLocaleTimeString();
            document.getElementById('lastUpdate').textContent = `Last update: ${now}`;
            
            // Update trading metrics
            const dailyPnl = data.daily_pnl || 0;
            const pnlElement = document.getElementById('dailyPnl');
            pnlElement.textContent = `$${dailyPnl.toFixed(2)}`;
            pnlElement.className = `metric-value ${dailyPnl >= 0 ? 'positive' : 'negative'}`;
            
            document.getElementById('equity').textContent = `$${(data.equity || 0).toLocaleString()}`;
            document.getElementById('positions').textContent = data.positions || 0;
            document.getElementById('tradesTotal').textContent = data.trades_today || 0;
            document.getElementById('uptime').textContent = data.uptime || 'Unknown';
            document.getElementById('dataSources').textContent = `${data.files_found} files active`;
            
            // Update status
            const statusElement = document.getElementById('botStatus');
            if (data.files_found > 0) {
                statusElement.textContent = 'RUNNING';
                statusElement.className = 'metric-value status-running';
            } else {
                statusElement.textContent = 'UNKNOWN';
                statusElement.className = 'metric-value status-error';
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
        '''
    
    def start(self):
        """Start the dashboard server"""
        print(f"🌐 Starting simple dashboard on port {self.port}...")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

def main():
    """Run the simple dashboard"""
    dashboard = SimpleDashboard(8181)
    dashboard.start()

if __name__ == "__main__":
    main()