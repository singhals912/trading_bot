"""
Dashboard Web Server.

Provides a web-based dashboard for monitoring the trading bot's performance,
positions, and real-time metrics.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import time

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS


class DashboardServer:
    """
    Web dashboard server for trading bot monitoring.
    
    Serves real-time bot metrics, performance data, and position information
    via a web interface on localhost:8080.
    """
    
    def __init__(
        self,
        port: int = 8080,
        logger: Optional[logging.Logger] = None
    ):
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self.app = Flask(__name__)
        CORS(self.app)
        
        self._server_thread = None
        self._running = False
        
        # Dashboard data paths
        self.dashboard_data_path = "dashboard.json"
        self.status_history_path = "status_history.json"
        self.metrics_path = "metrics.prom"
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes for the dashboard."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template_string(self._get_dashboard_template())
        
        @self.app.route('/api/status')
        def api_status():
            """Get current bot status."""
            try:
                data = self._load_dashboard_data()
                return jsonify({
                    "status": "running" if data else "stopped",
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                })
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Get performance metrics."""
            try:
                data = self._load_dashboard_data()
                if data and "performance_metrics" in data:
                    return jsonify(data["performance_metrics"])
                return jsonify({})
            except Exception as e:
                self.logger.error(f"Error getting metrics: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/config')
        def api_config():
            """Get bot configuration."""
            try:
                data = self._load_dashboard_data()
                if data and "config" in data:
                    config = data["config"].copy()
                    # Include market regime in config response
                    if "market_regime" in data:
                        config["market_regime"] = data["market_regime"]
                    return jsonify(config)
                return jsonify({})
            except Exception as e:
                self.logger.error(f"Error getting config: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/test-email', methods=['POST'])
        def api_test_email():
            """Test email notification endpoint."""
            try:
                import os
                import asyncio
                from datetime import datetime
                
                # Simple test email using basic SMTP
                import smtplib
                from email.mime.text import MimeText
                from email.mime.multipart import MimeMultipart
                
                # Get email config from environment
                smtp_host = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
                smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
                username = os.getenv('EMAIL_USERNAME', 'singhals912@gmail.com')
                password = os.getenv('EMAIL_PASSWORD', 'xvny qotn gbmf macu')
                recipient = os.getenv('NOTIFICATION_EMAIL', 'singhals912@gmail.com')
                
                # Create test email
                msg = MimeMultipart()
                msg['Subject'] = "📧 Test Email from Trading Bot Dashboard"
                msg['From'] = username
                msg['To'] = recipient
                
                body = f"""
This is a test email sent from your Enhanced Trading Bot dashboard!

Test Details:
- Sent from: Dashboard API endpoint  
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
- Portfolio Value: $98,248.74
- Status: System Operational

If you're receiving this email, your notification system is working correctly! 🎉

You can now expect to receive email alerts for:
• Trade executions
• Risk threshold breaches  
• System startup/shutdown
• Significant P&L changes

Happy trading! 📈
                """.strip()
                
                msg.attach(MimeText(body, 'plain'))
                
                # Send email
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(username, password)
                    server.sendmail(username, [recipient], msg.as_string())
                
                self.logger.info(f"✅ Test email sent to {recipient}")
                
                return jsonify({
                    "success": True,
                    "message": "Test email sent successfully! Check your inbox.",
                    "recipient": recipient,
                    "smtp_host": smtp_host
                })
                    
            except Exception as e:
                self.logger.error(f"Error sending test email: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/history')
        def api_history():
            """Get status history."""
            try:
                if os.path.exists(self.status_history_path):
                    with open(self.status_history_path, 'r') as f:
                        history = json.load(f)
                    return jsonify(history[-50:])  # Last 50 entries
                return jsonify([])
            except Exception as e:
                self.logger.error(f"Error getting history: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/portfolio')
        def api_portfolio():
            """Get portfolio information."""
            try:
                data = self._load_dashboard_data()
                if data and "portfolio" in data:
                    return jsonify(data["portfolio"])
                # Return empty portfolio data if none exists (will be populated by real data)
                return jsonify({
                    "total_value": 0.0,
                    "cash": 0.0,
                    "positions": 0,
                    "daily_pnl": 0.0,
                    "total_pnl": 0.0,
                    "last_updated": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Error getting portfolio: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _load_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """Load dashboard data from JSON file."""
        try:
            if os.path.exists(self.dashboard_data_path):
                with open(self.dashboard_data_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"Error loading dashboard data: {e}")
            return None
    
    def start(self) -> None:
        """Start the dashboard server in a separate thread."""
        if self._running:
            self.logger.warning("Dashboard server is already running")
            return
        
        self.logger.info(f"🌐 Starting dashboard server on http://localhost:{self.port}")
        
        def run_server():
            try:
                self.app.run(
                    host='0.0.0.0',
                    port=self.port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                self.logger.error(f"Dashboard server error: {e}")
        
        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        self._running = True
        
        # Give server time to start
        time.sleep(1)
        self.logger.info(f"✅ Dashboard server started: http://localhost:{self.port}")
    
    def stop(self) -> None:
        """Stop the dashboard server."""
        if not self._running:
            return
        
        self.logger.info("🛑 Stopping dashboard server...")
        self._running = False
        
        # Note: Flask's built-in server doesn't have a clean shutdown method
        # In production, you'd use a proper WSGI server like Gunicorn
        self.logger.info("✅ Dashboard server stopped")
    
    def is_running(self) -> bool:
        """Check if dashboard server is running."""
        return self._running and self._server_thread and self._server_thread.is_alive()
    
    def _get_dashboard_template(self) -> str:
        """Get the HTML template for the dashboard."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Trading Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .status-badge { 
            display: inline-block; 
            padding: 5px 15px; 
            border-radius: 20px; 
            font-weight: bold;
        }
        .status-running { background: #28a745; }
        .status-stopped { background: #dc3545; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: rgba(255,255,255,0.1); 
            border-radius: 10px; 
            padding: 20px; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h3 { margin-bottom: 15px; color: #ffd700; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-value { font-weight: bold; color: #00ff88; }
        .error { color: #ff6b6b; }
        .refresh-btn { 
            background: #28a745; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 10px 5px;
        }
        .refresh-btn:hover { background: #218838; }
        .timestamp { font-size: 0.9em; color: #ccc; margin-top: 10px; }
        .regime-badge {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .regime-trending_up { background: #28a745; }
        .regime-trending_down { background: #dc3545; }
        .regime-choppy { background: #ffc107; color: #000; }
        .regime-high_volatility { background: #fd7e14; }
        .regime-crisis { background: #6f42c1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Enhanced Trading Bot Dashboard</h1>
            <span id="status-badge" class="status-badge">Loading...</span>
            <div style="margin-top: 10px;">
                <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
                <button class="refresh-btn" onclick="toggleAutoRefresh()">⏱️ Auto Refresh: <span id="auto-status">ON</span></button>
                <button class="refresh-btn" onclick="testEmail()" style="background: #007bff;">📧 Test Email</button>
            </div>
        </div>
        
        <div class="cards">
            <div class="card">
                <h3>📊 Performance Metrics</h3>
                <div id="performance-metrics">
                    <div class="metric">
                        <span>Signals Generated:</span>
                        <span class="metric-value" id="signals-generated">-</span>
                    </div>
                    <div class="metric">
                        <span>Trades Executed:</span>
                        <span class="metric-value" id="trades-executed">-</span>
                    </div>
                    <div class="metric">
                        <span>Total P&L:</span>
                        <span class="metric-value" id="total-pnl">-</span>
                    </div>
                    <div class="metric">
                        <span>Avg Signal Confidence:</span>
                        <span class="metric-value" id="avg-confidence">-</span>
                    </div>
                    <div class="metric">
                        <span>Runtime Hours:</span>
                        <span class="metric-value" id="runtime-hours">-</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🏛️ Market Regime & Config</h3>
                <div id="regime-config">
                    <div class="metric">
                        <span>Market Regime:</span>
                        <span id="market-regime" class="regime-badge">-</span>
                    </div>
                    <div class="metric">
                        <span>Strategy Type:</span>
                        <span class="metric-value" id="strategy-type">-</span>
                    </div>
                    <div class="metric">
                        <span>Min Confidence:</span>
                        <span class="metric-value" id="min-confidence">-</span>
                    </div>
                    <div class="metric">
                        <span>Max Positions:</span>
                        <span class="metric-value" id="max-positions">-</span>
                    </div>
                    <div class="metric">
                        <span>Paper Trading:</span>
                        <span class="metric-value" id="paper-trading">-</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>💰 Portfolio</h3>
                <div id="portfolio-info">
                    <div class="metric">
                        <span>Total Value:</span>
                        <span class="metric-value" id="portfolio-value">-</span>
                    </div>
                    <div class="metric">
                        <span>Cash:</span>
                        <span class="metric-value" id="portfolio-cash">-</span>
                    </div>
                    <div class="metric">
                        <span>Positions:</span>
                        <span class="metric-value" id="portfolio-positions">-</span>
                    </div>
                    <div class="metric">
                        <span>Daily P&L:</span>
                        <span class="metric-value" id="daily-pnl">-</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>📈 Recent Activity</h3>
                <div id="recent-activity">
                    <p>Loading recent activity...</p>
                </div>
            </div>
            
            <div class="card">
                <h3>🔧 System Status</h3>
                <div id="system-status">
                    <div class="metric">
                        <span>Bot Version:</span>
                        <span class="metric-value" id="bot-version">-</span>
                    </div>
                    <div class="metric">
                        <span>Last Update:</span>
                        <span class="metric-value" id="last-update">-</span>
                    </div>
                    <div class="metric">
                        <span>Regime Changes:</span>
                        <span class="metric-value" id="regime-changes">-</span>
                    </div>
                    <div class="metric">
                        <span>Signals Filtered:</span>
                        <span class="metric-value" id="signals-filtered">-</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="timestamp" id="last-refresh">
            Last refreshed: Never
        </div>
    </div>

    <script>
        let autoRefresh = true;
        let refreshInterval;
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(`/api/${endpoint}`);
                return await response.json();
            } catch (error) {
                console.error(`Error fetching ${endpoint}:`, error);
                return null;
            }
        }
        
        async function refreshData() {
            try {
                const [status, metrics, config, history, portfolio] = await Promise.all([
                    fetchData('status'),
                    fetchData('metrics'),
                    fetchData('config'),
                    fetchData('history'),
                    fetchData('portfolio')
                ]);
                
                updateStatus(status);
                updateMetrics(metrics);
                updateConfig(config);
                updateSystemStatus(status);
                updateActivity(history);
                updatePortfolio(portfolio);
                
                document.getElementById('last-refresh').textContent = 
                    `Last refreshed: ${new Date().toLocaleTimeString()}`;
                    
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        function updateStatus(status) {
            const badge = document.getElementById('status-badge');
            if (status && status.status === 'running') {
                badge.textContent = '🟢 RUNNING';
                badge.className = 'status-badge status-running';
            } else {
                badge.textContent = '🔴 STOPPED';
                badge.className = 'status-badge status-stopped';
            }
        }
        
        function updateMetrics(metrics) {
            if (!metrics) return;
            
            document.getElementById('signals-generated').textContent = metrics.signals_generated || 0;
            document.getElementById('trades-executed').textContent = metrics.trades_executed || 0;
            document.getElementById('total-pnl').textContent = 
                `$${(metrics.total_pnl || 0).toFixed(2)}`;
            document.getElementById('avg-confidence').textContent = 
                `${((metrics.avg_signal_confidence || 0) * 100).toFixed(1)}%`;
            document.getElementById('runtime-hours').textContent = 
                `${(metrics.runtime_hours || 0).toFixed(2)}h`;
        }
        
        function updateConfig(config) {
            if (!config) return;
            
            const regime = config.market_regime || 'unknown';
            const regimeBadge = document.getElementById('market-regime');
            regimeBadge.textContent = regime.toUpperCase();
            regimeBadge.className = `regime-badge regime-${regime}`;
            
            document.getElementById('strategy-type').textContent = config.strategy_type || '-';
            document.getElementById('min-confidence').textContent = 
                `${((config.min_confidence || 0) * 100).toFixed(0)}%`;
            document.getElementById('max-positions').textContent = config.max_positions || '-';
            document.getElementById('paper-trading').textContent = 
                config.paper_trading ? '✅ Yes' : '❌ No';
        }
        
        function updateSystemStatus(status) {
            if (!status || !status.data) return;
            
            document.getElementById('bot-version').textContent = status.data.bot_version || '-';
            document.getElementById('last-update').textContent = 
                new Date(status.data.timestamp).toLocaleTimeString();
            document.getElementById('regime-changes').textContent = 
                status.data.performance_metrics?.regime_changes || 0;
            document.getElementById('signals-filtered').textContent = 
                status.data.performance_metrics?.signals_filtered_out || 0;
        }
        
        function updatePortfolio(portfolio) {
            if (!portfolio) return;
            
            document.getElementById('portfolio-value').textContent = 
                `$${(portfolio.total_value || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('portfolio-cash').textContent = 
                `$${(portfolio.cash || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('portfolio-positions').textContent = 
                (portfolio.positions || []).length;
            
            const dailyPnl = portfolio.daily_pnl || 0;
            const pnlElement = document.getElementById('daily-pnl');
            pnlElement.textContent = `$${dailyPnl.toFixed(2)}`;
            pnlElement.style.color = dailyPnl >= 0 ? '#00ff88' : '#ff6b6b';
        }
        
        function updateActivity(history) {
            const container = document.getElementById('recent-activity');
            if (!history || history.length === 0) {
                container.innerHTML = '<p>No recent activity</p>';
                return;
            }
            
            const recentItems = history.slice(-5).reverse();
            container.innerHTML = recentItems.map(item => 
                `<div style="margin: 5px 0; font-size: 0.9em;">
                    ${new Date(item.timestamp).toLocaleTimeString()}: ${item.message || 'Activity logged'}
                </div>`
            ).join('');
        }
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            document.getElementById('auto-status').textContent = autoRefresh ? 'ON' : 'OFF';
            
            if (autoRefresh) {
                startAutoRefresh();
            } else {
                clearInterval(refreshInterval);
            }
        }
        
        function startAutoRefresh() {
            refreshInterval = setInterval(refreshData, 5000); // 5 seconds
        }
        
        // Test email function
        async function testEmail() {
            const button = event.target;
            const originalText = button.innerHTML;
            
            try {
                button.innerHTML = '⏳ Sending...';
                button.disabled = true;
                
                const response = await fetch('/api/test-email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    button.innerHTML = '✅ Email Sent!';
                    button.style.background = '#28a745';
                    alert(`✅ Test email sent successfully to ${result.recipient}!\n\nCheck your email inbox for the test notification.`);
                } else {
                    button.innerHTML = '❌ Failed';
                    button.style.background = '#dc3545';
                    alert(`❌ Failed to send email: ${result.error}`);
                }
                
            } catch (error) {
                button.innerHTML = '❌ Error';
                button.style.background = '#dc3545';
                alert(`❌ Error: ${error.message}`);
            }
            
            // Reset button after 3 seconds
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.background = '#007bff';
                button.disabled = false;
            }, 3000);
        }
        
        // Initial load
        refreshData();
        startAutoRefresh();
    </script>
</body>
</html>
        """


class NgrokTunnel:
    """
    Ngrok tunnel manager for exposing the dashboard remotely.
    """
    
    def __init__(
        self,
        port: int = 8080,
        logger: Optional[logging.Logger] = None
    ):
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self.tunnel_url = None
        self._tunnel_process = None
        
    def start_tunnel(self) -> Optional[str]:
        """Start ngrok tunnel and return the public URL."""
        try:
            import subprocess
            import json
            import requests
            import time
            
            # Check if ngrok is installed
            try:
                subprocess.run(['ngrok', 'version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("⚠️ ngrok not found. Install with: brew install ngrok (macOS) or download from ngrok.com")
                return None
            
            self.logger.info(f"🚇 Starting ngrok tunnel for port {self.port}...")
            
            # Start ngrok
            self._tunnel_process = subprocess.Popen([
                'ngrok', 'http', str(self.port), '--log', 'stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for tunnel to establish
            time.sleep(3)
            
            # Get tunnel URL from ngrok API
            try:
                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()
                    for tunnel in tunnels.get('tunnels', []):
                        if tunnel.get('proto') == 'https':
                            self.tunnel_url = tunnel.get('public_url')
                            self.logger.info(f"✅ Ngrok tunnel active: {self.tunnel_url}")
                            return self.tunnel_url
                
            except requests.RequestException:
                self.logger.warning("Could not connect to ngrok API")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to start ngrok tunnel: {e}")
            return None
    
    def stop_tunnel(self) -> None:
        """Stop the ngrok tunnel."""
        if self._tunnel_process:
            self.logger.info("🛑 Stopping ngrok tunnel...")
            self._tunnel_process.terminate()
            self._tunnel_process = None
            self.tunnel_url = None
            self.logger.info("✅ Ngrok tunnel stopped")
    
    def get_tunnel_url(self) -> Optional[str]:
        """Get the current tunnel URL."""
        return self.tunnel_url
    
    def is_active(self) -> bool:
        """Check if tunnel is active."""
        return self._tunnel_process is not None and self._tunnel_process.poll() is None