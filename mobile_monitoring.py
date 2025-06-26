# mobile_monitoring.py
"""
Enhanced Mobile Monitoring Solution for Algo Trading Bot
Provides real-time bot status accessible from anywhere via web interface, SMS, and email alerts
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import traceback

# Web server imports
try:
    from flask import Flask, jsonify, render_template_string
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Notification imports
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class MobileMonitoring:
    """Enhanced mobile monitoring for trading bot with web interface and alerts"""
    
    def __init__(self, bot_instance=None, port=8080):
        self.bot = bot_instance
        self.port = port
        self.app = None
        self.monitoring_data = {}
        self.alert_config = self._load_alert_config()
        self.last_alert_times = {}
        self.status_history = []
        
        # Initialize monitoring
        self._initialize_monitoring()
        
        # Start background monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._continuous_monitoring, daemon=True)
        self.monitoring_thread.start()
        
        print("📱 Mobile Monitoring System initialized")
        print(f"🌐 Web interface will be available at: http://localhost:{port}")
        print("📊 Real-time status tracking active")
    
    def _load_alert_config(self) -> Dict:
        """Load alert configuration from environment variables"""
        return {
            'email': {
                'enabled': bool(os.getenv('EMAIL_ALERTS_ENABLED', 'True').lower() == 'true'),
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'sender_email': os.getenv('SENDER_EMAIL'),
                'sender_password': os.getenv('SENDER_PASSWORD'),
                'recipient_email': os.getenv('RECIPIENT_EMAIL'),
            },
            'sms': {
                'enabled': bool(os.getenv('SMS_ALERTS_ENABLED', 'False').lower() == 'true'),
                'twilio_sid': os.getenv('TWILIO_SID'),
                'twilio_token': os.getenv('TWILIO_TOKEN'),
                'from_number': os.getenv('TWILIO_FROM'),
                'to_number': os.getenv('RECIPIENT_PHONE'),
            },
            'alert_cooldown': 300,  # 5 minutes between similar alerts
        }
    
    def _initialize_monitoring(self):
        """Initialize monitoring data structure"""
        self.monitoring_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'starting',
            'uptime_start': datetime.now().isoformat(),
            'bot_version': 'v5.0',
            'system_health': {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_space': 0,
                'network_status': 'unknown'
            },
            'trading_status': {
                'market_hours': 'unknown',
                'active_positions': 0,
                'daily_pnl': 0,
                'total_trades_today': 0,
                'win_rate_today': 0,
                'account_equity': 0,
                'buying_power': 0,
                'last_trade_time': None
            },
            'alerts': {
                'active_alerts': [],
                'alert_count_today': 0,
                'last_alert_time': None
            },
            'performance': {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        }
    
    def _continuous_monitoring(self):
        """Background thread for continuous monitoring"""
        while self.monitoring_active:
            try:
                self._update_monitoring_data()
                self._check_alert_conditions()
                self._save_status_snapshot()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _update_monitoring_data(self):
        """Update all monitoring data"""
        try:
            self.monitoring_data['timestamp'] = datetime.now().isoformat()
            
            # Update system health
            self._update_system_health()
            
            # Update trading status
            self._update_trading_status()
            
            # Update bot status
            self._update_bot_status()
            
            # Save to files for mobile access
            self._save_monitoring_data()
            
        except Exception as e:
            print(f"Error updating monitoring data: {e}")
    
    def _update_system_health(self):
        """Update system health metrics"""
        try:
            import psutil
            
            self.monitoring_data['system_health'] = {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_space': psutil.disk_usage('/').percent,
                'network_status': 'connected' if self._check_internet_connection() else 'disconnected'
            }
        except ImportError:
            # Fallback if psutil not available
            self.monitoring_data['system_health'] = {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_space': 0,
                'network_status': 'unknown'
            }
    
    def _update_trading_status(self):
        """Update trading-specific status"""
        try:
            if self.bot:
                # Get account info
                account_info = self.bot.get_account_info()
                if account_info:
                    self.monitoring_data['trading_status'].update({
                        'account_equity': float(account_info.get('equity', 0)),
                        'buying_power': float(account_info.get('buying_power', 0)),
                        'daily_pnl': float(account_info.get('equity', 0)) - float(account_info.get('last_equity', account_info.get('equity', 0)))
                    })
                
                # Get positions
                positions = getattr(self.bot, 'positions', {})
                self.monitoring_data['trading_status']['active_positions'] = len(positions)
                
                # Calculate daily metrics
                self._calculate_daily_metrics()
                
                # Check market hours
                self.monitoring_data['trading_status']['market_hours'] = self._get_market_status()
                
        except Exception as e:
            print(f"Error updating trading status: {e}")
    
    def _update_bot_status(self):
        """Update bot operational status"""
        try:
            # Check if bot is responsive
            if self.bot and hasattr(self.bot, 'health_check'):
                health = self.bot.health_check()
                self.monitoring_data['status'] = 'running' if health else 'error'
            elif self.bot:
                self.monitoring_data['status'] = 'running'
            else:
                self.monitoring_data['status'] = 'disconnected'
                
            # Calculate uptime
            start_time = datetime.fromisoformat(self.monitoring_data['uptime_start'])
            uptime_seconds = (datetime.now() - start_time).total_seconds()
            self.monitoring_data['uptime_hours'] = round(uptime_seconds / 3600, 1)
            
        except Exception as e:
            print(f"Error updating bot status: {e}")
            self.monitoring_data['status'] = 'error'
    
    def _calculate_daily_metrics(self):
        """Calculate daily trading metrics"""
        try:
            # Load daily digest if available
            today_file = f"daily_digest_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(today_file):
                with open(today_file, 'r') as f:
                    daily_data = json.load(f)
                    
                self.monitoring_data['trading_status'].update({
                    'total_trades_today': daily_data.get('total_trades', 0),
                    'win_rate_today': daily_data.get('win_rate', 0)
                })
        except Exception as e:
            print(f"Error calculating daily metrics: {e}")
    
    def _get_market_status(self) -> str:
        """Determine current market status"""
        try:
            now = datetime.now()
            weekday = now.weekday()
            hour = now.hour
            
            # Simple market hours check (9:30 AM - 4:00 PM ET on weekdays)
            if weekday >= 5:  # Weekend
                return 'closed'
            elif 9 <= hour < 16:  # Market hours (simplified)
                return 'open'
            elif 4 <= hour < 9:  # Pre-market
                return 'pre_market'
            else:  # After hours
                return 'after_hours'
        except:
            return 'unknown'
    
    def _check_internet_connection(self) -> bool:
        """Check if internet connection is available"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False
    
    def _check_alert_conditions(self):
        """Check for conditions that should trigger alerts"""
        alerts = []
        
        try:
            # Check for significant P&L changes
            daily_pnl = self.monitoring_data['trading_status']['daily_pnl']
            if daily_pnl < -1000:  # $1000 loss
                alerts.append({
                    'type': 'critical',
                    'message': f'Significant daily loss: ${daily_pnl:,.2f}',
                    'time': datetime.now().isoformat()
                })
            
            # Check system health
            cpu = self.monitoring_data['system_health']['cpu_usage']
            memory = self.monitoring_data['system_health']['memory_usage']
            
            if cpu > 90:
                alerts.append({
                    'type': 'warning',
                    'message': f'High CPU usage: {cpu}%',
                    'time': datetime.now().isoformat()
                })
            
            if memory > 90:
                alerts.append({
                    'type': 'warning',
                    'message': f'High memory usage: {memory}%',
                    'time': datetime.now().isoformat()
                })
            
            # Check bot status
            if self.monitoring_data['status'] == 'error':
                alerts.append({
                    'type': 'critical',
                    'message': 'Trading bot has encountered an error',
                    'time': datetime.now().isoformat()
                })
            
            # Check network connectivity
            if self.monitoring_data['system_health']['network_status'] == 'disconnected':
                alerts.append({
                    'type': 'critical',
                    'message': 'Internet connection lost',
                    'time': datetime.now().isoformat()
                })
            
            # Process and send alerts
            for alert in alerts:
                self._process_alert(alert)
                
        except Exception as e:
            print(f"Error checking alert conditions: {e}")
    
    def _process_alert(self, alert: Dict):
        """Process and send an alert"""
        try:
            alert_key = f"{alert['type']}_{alert['message'][:50]}"
            current_time = datetime.now()
            
            # Check cooldown
            if alert_key in self.last_alert_times:
                last_time = self.last_alert_times[alert_key]
                if (current_time - last_time).seconds < self.alert_config['alert_cooldown']:
                    return  # Skip due to cooldown
            
            # Update alert tracking
            self.last_alert_times[alert_key] = current_time
            self.monitoring_data['alerts']['active_alerts'].append(alert)
            self.monitoring_data['alerts']['alert_count_today'] += 1
            self.monitoring_data['alerts']['last_alert_time'] = alert['time']
            
            # Send notifications
            if alert['type'] == 'critical':
                self._send_email_alert(alert)
                self._send_sms_alert(alert)
            elif alert['type'] == 'warning':
                self._send_email_alert(alert)
            
            print(f"🚨 Alert sent: {alert['message']}")
            
        except Exception as e:
            print(f"Error processing alert: {e}")
    
    def _send_email_alert(self, alert: Dict):
        """Send email alert"""
        try:
            if not self.alert_config['email']['enabled'] or not EMAIL_AVAILABLE:
                return
            
            config = self.alert_config['email']
            if not all([config['sender_email'], config['sender_password'], config['recipient_email']]):
                return
            
            msg = MimeMultipart()
            msg['From'] = config['sender_email']
            msg['To'] = config['recipient_email']
            msg['Subject'] = f"Trading Bot Alert - {alert['type'].upper()}"
            
            body = f"""
Trading Bot Alert

Type: {alert['type'].upper()}
Time: {alert['time']}
Message: {alert['message']}

Current Status:
- Bot Status: {self.monitoring_data['status']}
- Daily P&L: ${self.monitoring_data['trading_status']['daily_pnl']:,.2f}
- Active Positions: {self.monitoring_data['trading_status']['active_positions']}
- Account Equity: ${self.monitoring_data['trading_status']['account_equity']:,.2f}

System Health:
- CPU: {self.monitoring_data['system_health']['cpu_usage']}%
- Memory: {self.monitoring_data['system_health']['memory_usage']}%
- Network: {self.monitoring_data['system_health']['network_status']}

Check your dashboard for more details.
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.sendmail(config['sender_email'], config['recipient_email'], msg.as_string())
            server.quit()
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _send_sms_alert(self, alert: Dict):
        """Send SMS alert"""
        try:
            if not self.alert_config['sms']['enabled'] or not TWILIO_AVAILABLE:
                return
            
            config = self.alert_config['sms']
            if not all([config['twilio_sid'], config['twilio_token'], config['from_number'], config['to_number']]):
                return
            
            client = TwilioClient(config['twilio_sid'], config['twilio_token'])
            
            message_body = f"""
🚨 Trading Bot Alert

{alert['message']}

Status: {self.monitoring_data['status']}
P&L: ${self.monitoring_data['trading_status']['daily_pnl']:,.2f}
Positions: {self.monitoring_data['trading_status']['active_positions']}

Time: {alert['time']}
"""
            
            client.messages.create(
                body=message_body,
                from_=config['from_number'],
                to=config['to_number']
            )
            
        except Exception as e:
            print(f"Failed to send SMS alert: {e}")
    
    def _save_status_snapshot(self):
        """Save status snapshot for history"""
        try:
            snapshot = {
                'timestamp': self.monitoring_data['timestamp'],
                'status': self.monitoring_data['status'],
                'daily_pnl': self.monitoring_data['trading_status']['daily_pnl'],
                'positions': self.monitoring_data['trading_status']['active_positions'],
                'equity': self.monitoring_data['trading_status']['account_equity']
            }
            
            self.status_history.append(snapshot)
            
            # Keep only last 100 snapshots
            if len(self.status_history) > 100:
                self.status_history.pop(0)
                
        except Exception as e:
            print(f"Error saving status snapshot: {e}")
    
    def _save_monitoring_data(self):
        """Save monitoring data to JSON files"""
        try:
            # Save main monitoring data
            with open('mobile_monitoring.json', 'w') as f:
                json.dump(self.monitoring_data, f, indent=2, default=str)
            
            # Save status history
            with open('status_history.json', 'w') as f:
                json.dump(self.status_history, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving monitoring data: {e}")
    
    def start_web_server(self):
        """Start Flask web server for mobile dashboard"""
        if not FLASK_AVAILABLE:
            print("❌ Flask not available. Install with: pip install flask flask-cors")
            return
        
        self.app = Flask(__name__)
        CORS(self.app)
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for current status"""
            return jsonify(self.monitoring_data)
        
        @self.app.route('/api/history')
        def api_history():
            """API endpoint for status history"""
            return jsonify(self.status_history)
        
        @self.app.route('/api/quick_status')
        def api_quick_status():
            """Quick status for mobile widgets"""
            return jsonify({
                'status': self.monitoring_data['status'],
                'daily_pnl': self.monitoring_data['trading_status']['daily_pnl'],
                'positions': self.monitoring_data['trading_status']['active_positions'],
                'equity': self.monitoring_data['trading_status']['account_equity'],
                'last_update': self.monitoring_data['timestamp']
            })
        
        @self.app.route('/')
        def dashboard():
            """Mobile-friendly dashboard"""
            return render_template_string(self._get_mobile_dashboard_html())
        
        try:
            print(f"🌐 Starting web server on port {self.port}...")
            self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
        except Exception as e:
            print(f"Failed to start web server: {e}")
    
    def _get_mobile_dashboard_html(self) -> str:
        """Get mobile-optimized dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Mobile Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a; color: #fff; padding: 10px;
        }
        .header { text-align: center; margin-bottom: 20px; }
        .status-card { 
            background: #2d2d2d; border-radius: 10px; padding: 15px; 
            margin-bottom: 15px; border-left: 4px solid #4CAF50;
        }
        .status-card.warning { border-left-color: #FF9800; }
        .status-card.error { border-left-color: #f44336; }
        .metric { display: flex; justify-content: space-between; margin: 8px 0; }
        .metric-label { color: #ccc; }
        .metric-value { font-weight: bold; }
        .positive { color: #4CAF50; }
        .negative { color: #f44336; }
        .refresh-btn { 
            background: #4CAF50; color: white; border: none; 
            padding: 10px 20px; border-radius: 5px; width: 100%;
            margin-top: 20px; font-size: 16px;
        }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        @media (max-width: 480px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Trading Bot Monitor</h1>
        <p id="lastUpdate">Last Update: Loading...</p>
    </div>
    
    <div class="status-card" id="mainStatus">
        <h3>Bot Status</h3>
        <div class="metric">
            <span class="metric-label">Status:</span>
            <span class="metric-value" id="botStatus">Loading...</span>
        </div>
        <div class="metric">
            <span class="metric-label">Uptime:</span>
            <span class="metric-value" id="uptime">Loading...</span>
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
                <span class="metric-label">Positions:</span>
                <span class="metric-value" id="positions">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Equity:</span>
                <span class="metric-value" id="equity">$0.00</span>
            </div>
            <div class="metric">
                <span class="metric-label">Trades Today:</span>
                <span class="metric-value" id="tradesTotal">0</span>
            </div>
        </div>
        
        <div class="status-card">
            <h3>⚙️ System</h3>
            <div class="metric">
                <span class="metric-label">CPU:</span>
                <span class="metric-value" id="cpu">0%</span>
            </div>
            <div class="metric">
                <span class="metric-label">Memory:</span>
                <span class="metric-value" id="memory">0%</span>
            </div>
            <div class="metric">
                <span class="metric-label">Network:</span>
                <span class="metric-value" id="network">Unknown</span>
            </div>
            <div class="metric">
                <span class="metric-label">Market:</span>
                <span class="metric-value" id="market">Unknown</span>
            </div>
        </div>
    </div>
    
    <div class="status-card" id="alertsCard" style="display: none;">
        <h3>🚨 Active Alerts</h3>
        <div id="alertsList"></div>
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
            // Update timestamp
            const lastUpdate = new Date(data.timestamp).toLocaleString();
            document.getElementById('lastUpdate').textContent = `Last Update: ${lastUpdate}`;
            
            // Update bot status
            const statusElement = document.getElementById('botStatus');
            statusElement.textContent = data.status.toUpperCase();
            
            const mainCard = document.getElementById('mainStatus');
            mainCard.className = 'status-card';
            if (data.status === 'error') mainCard.className += ' error';
            else if (data.status === 'warning') mainCard.className += ' warning';
            
            // Update uptime
            document.getElementById('uptime').textContent = `${data.uptime_hours || 0}h`;
            
            // Update trading metrics
            const dailyPnl = data.trading_status.daily_pnl || 0;
            const pnlElement = document.getElementById('dailyPnl');
            pnlElement.textContent = `$${dailyPnl.toFixed(2)}`;
            pnlElement.className = `metric-value ${dailyPnl >= 0 ? 'positive' : 'negative'}`;
            
            document.getElementById('positions').textContent = data.trading_status.active_positions || 0;
            document.getElementById('equity').textContent = `$${(data.trading_status.account_equity || 0).toLocaleString()}`;
            document.getElementById('tradesTotal').textContent = data.trading_status.total_trades_today || 0;
            
            // Update system metrics
            document.getElementById('cpu').textContent = `${data.system_health.cpu_usage || 0}%`;
            document.getElementById('memory').textContent = `${data.system_health.memory_usage || 0}%`;
            document.getElementById('network').textContent = data.system_health.network_status || 'Unknown';
            document.getElementById('market').textContent = data.trading_status.market_hours || 'Unknown';
            
            // Update alerts
            const alerts = data.alerts.active_alerts || [];
            const alertsCard = document.getElementById('alertsCard');
            if (alerts.length > 0) {
                alertsCard.style.display = 'block';
                const alertsList = document.getElementById('alertsList');
                alertsList.innerHTML = alerts.slice(-5).map(alert => 
                    `<div class="metric">
                        <span>${alert.message}</span>
                        <span>${new Date(alert.time).toLocaleTimeString()}</span>
                    </div>`
                ).join('');
            } else {
                alertsCard.style.display = 'none';
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
    
    def get_quick_status_text(self) -> str:
        """Get quick status as text for SMS or simple display"""
        try:
            status = self.monitoring_data['status'].upper()
            pnl = self.monitoring_data['trading_status']['daily_pnl']
            positions = self.monitoring_data['trading_status']['active_positions']
            equity = self.monitoring_data['trading_status']['account_equity']
            
            return f"""
🤖 Bot: {status}
💰 P&L: ${pnl:,.2f}
📊 Positions: {positions}
💼 Equity: ${equity:,.2f}
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        except Exception as e:
            return f"Error getting status: {e}"
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        print("📱 Mobile monitoring stopped")


def setup_mobile_monitoring(bot_instance, port=8080):
    """Quick setup function for mobile monitoring"""
    try:
        monitor = MobileMonitoring(bot_instance, port)
        
        # Start web server in a separate thread
        server_thread = threading.Thread(target=monitor.start_web_server, daemon=True)
        server_thread.start()
        
        print(f"""
📱 Mobile Monitoring Setup Complete!

🌐 Web Dashboard: http://localhost:{port}
📊 API Endpoints:
   - Status: http://localhost:{port}/api/status
   - History: http://localhost:{port}/api/history
   - Quick: http://localhost:{port}/api/quick_status

📧 Email Alerts: {'✅ Enabled' if monitor.alert_config['email']['enabled'] else '❌ Disabled'}
📱 SMS Alerts: {'✅ Enabled' if monitor.alert_config['sms']['enabled'] else '❌ Disabled'}

To access from your phone:
1. Connect to the same WiFi network
2. Use your Mac's IP address: http://YOUR_MAC_IP:{port}
3. Or set up port forwarding for remote access

Status files saved to:
- mobile_monitoring.json (current status)
- status_history.json (historical data)
        """)
        
        return monitor
        
    except Exception as e:
        print(f"❌ Failed to setup mobile monitoring: {e}")
        return None


# Command line usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Mobile Monitoring for Trading Bot')
    parser.add_argument('--port', type=int, default=8080, help='Web server port')
    parser.add_argument('--test', action='store_true', help='Test mode without bot instance')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Running in test mode...")
        monitor = MobileMonitoring(None, args.port)
        monitor.start_web_server()
    else:
        print("Use setup_mobile_monitoring(bot_instance) from your main bot script")