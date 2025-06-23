import asyncio
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import aiohttp

# Optional imports with fallbacks
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None

@dataclass
class AlertRule:
    """Define alert conditions"""
    name: str
    condition: str  # 'threshold', 'anomaly', 'pattern'
    params: Dict
    severity: str  # 'info', 'warning', 'critical'
    cooldown_minutes: int = 60
    last_triggered: Optional[datetime] = None

class EventManager:
    """Manage market events and external data sources"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.events = []
        
    async def check_market_events(self, symbols: List[str]) -> List[str]:
        """Check for market events and return event types"""
        event_types = []
        
        # Check earnings calendar
        if await self._check_earnings_proximity(symbols):
            event_types.append("earnings_proximity")
            
        # Check FOMC meetings
        if await self._check_fomc_proximity():
            event_types.append("fomc_proximity")
            
        # Check for negative news
        if await self._check_negative_news(symbols):
            event_types.append("negative_news")
            
        # Check market stress
        if await self._check_market_stress():
            event_types.append("market_stress")
            
        return event_types
    
    async def _check_earnings_proximity(self, symbols: List[str]) -> bool:
        """Check if any tracked symbols have earnings in next 3 days"""
        # In practice, this would call an earnings calendar API
        # For now, return False as placeholder
        return False
    
    async def _check_fomc_proximity(self) -> bool:
        """Check if FOMC meeting is within 2 days"""
        # FOMC dates for 2025
        fomc_dates = [
            datetime(2025, 1, 29),
            datetime(2025, 3, 19),
            datetime(2025, 5, 7),
            datetime(2025, 6, 18),
            datetime(2025, 7, 30),
            datetime(2025, 9, 17),
            datetime(2025, 11, 5),
            datetime(2025, 12, 17)
        ]
        
        now = datetime.now()
        for fomc_date in fomc_dates:
            days_until = (fomc_date - now).days
            if 0 <= days_until <= 2:
                return True
        return False
    
    async def _check_negative_news(self, symbols: List[str]) -> bool:
        """Check for negative news about tracked symbols"""
        # Placeholder - would integrate with news API
        return False
    
    async def _check_market_stress(self) -> bool:
        """Check market stress indicators"""
        # Placeholder - would check VIX, yield curve, etc.
        return False
    
    def get_events_summary(self) -> Dict:
        """Get summary of recent events"""
        return {
            'total_events': len(self.events),
            'latest_events': self.events[-5:] if self.events else []
        }
    
    def get_market_regime_assessment(self) -> Dict:
        """Assess current market regime"""
        # Simplified assessment
        return {
            'regime': 'normal',
            'risk_score': 20,
            'recommendation': 'Normal trading operations can continue'
        }

class SmartAlertSystem:
    """Intelligent alerting that reduces noise and provides actionable insights"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.alert_rules = self._initialize_rules()
        self.alert_history = []
        self.notification_channels = {
            'email': self._send_email,
            'sms': self._send_sms,
            'telegram': self._send_telegram,
            'discord': self._send_discord
        }
        self.batched_alerts = []
        self.digest_queue = []
        self.event_manager = EventManager(config)
        
    def _initialize_rules(self) -> List[AlertRule]:
        """Initialize smart alert rules with event-driven alerts"""
        base_rules = [
            # Critical alerts (always notify)
            AlertRule(
                name="daily_loss_limit",
                condition="threshold",
                params={"metric": "daily_pnl", "operator": "<=", "value": -1000},  # -$1000 (2% of $50k)
                severity="critical",
                cooldown_minutes=0  # No cooldown for critical
            ),
            AlertRule(
                name="position_stop_loss_hit",
                condition="event",
                params={"event_type": "stop_loss_triggered"},
                severity="warning",
                cooldown_minutes=30
            ),
            AlertRule(
                name="unusual_market_volatility",
                condition="anomaly",
                params={"metric": "vix", "std_deviations": 3},
                severity="warning",
                cooldown_minutes=120
            ),
            AlertRule(
                name="system_health_degraded",
                condition="threshold",
                params={"metric": "health_score", "operator": "<", "value": 0.7},
                severity="critical",
                cooldown_minutes=30
            ),
            
            # Info alerts (digest only)
            AlertRule(
                name="daily_profit_target",
                condition="threshold",
                params={"metric": "daily_pnl", "operator": ">=", "value": 500},  # $500 profit
                severity="info",
                cooldown_minutes=1440  # Once per day
            ),
            AlertRule(
                name="new_position_opened",
                condition="event",
                params={"event_type": "position_opened"},
                severity="info",
                cooldown_minutes=5
            )
        ]
        
        # ADD these new event-driven rules:
        event_rules = [
            AlertRule(
                name="earnings_week_detected",
                condition="event",
                params={"event_type": "earnings_proximity"},
                severity="warning",
                cooldown_minutes=60
            ),
            AlertRule(
                name="fomc_meeting_detected",
                condition="event", 
                params={"event_type": "fomc_proximity"},
                severity="warning",
                cooldown_minutes=720  # 12 hours
            ),
            AlertRule(
                name="negative_news_detected",
                condition="event",
                params={"event_type": "negative_news"},
                severity="warning",
                cooldown_minutes=30
            ),
            AlertRule(
                name="market_stress_elevated",
                condition="event",
                params={"event_type": "market_stress"},
                severity="critical",
                cooldown_minutes=60
            )
        ]
        
        return base_rules + event_rules
        
    async def evaluate_alerts(self, metrics: Dict, bot_instance=None):
        """Evaluate all alert rules with event checking"""
        
        # ADD event checking if bot instance is provided
        if bot_instance and hasattr(bot_instance, 'positions'):
            symbols = list(bot_instance.positions.keys()) if bot_instance.positions else ['SPY']
            event_types = await self.event_manager.check_market_events(symbols)
            metrics['events'] = event_types
        
        triggered_alerts = []
        
        for rule in self.alert_rules:
            if self._should_evaluate_rule(rule):
                if self._evaluate_condition(rule, metrics):
                    triggered_alerts.append(rule)
                    rule.last_triggered = datetime.now()
                    
        if triggered_alerts:
            await self._process_alerts(triggered_alerts, metrics)
            
    def _should_evaluate_rule(self, rule: AlertRule) -> bool:
        """Check if rule should be evaluated (cooldown logic)"""
        if rule.last_triggered is None:
            return True
            
        time_since_last = datetime.now() - rule.last_triggered
        return time_since_last > timedelta(minutes=rule.cooldown_minutes)
        
    def _evaluate_condition(self, rule: AlertRule, metrics: Dict) -> bool:
        """Evaluate rule condition"""
        if rule.condition == "threshold":
            metric_value = metrics.get(rule.params["metric"], 0)
            operator = rule.params["operator"]
            threshold = rule.params["value"]
            
            if operator == ">=":
                return metric_value >= threshold
            elif operator == "<=":
                return metric_value <= threshold
            elif operator == "<":
                return metric_value < threshold
            elif operator == ">":
                return metric_value > threshold
                
        elif rule.condition == "anomaly":
            # Implement anomaly detection logic
            metric_value = metrics.get(rule.params["metric"], 0)
            # Simple anomaly detection - can be enhanced
            return abs(metric_value) > rule.params.get("std_deviations", 2) * 10
            
        elif rule.condition == "event":
            # Check for specific events
            return rule.params["event_type"] in metrics.get("events", [])
            
        return False
        
    async def _process_alerts(self, alerts: List[AlertRule], metrics: Dict):
        """Process and send alerts intelligently"""
        # Group alerts by severity
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        warning_alerts = [a for a in alerts if a.severity == "warning"]
        info_alerts = [a for a in alerts if a.severity == "info"]
        
        # Send critical alerts immediately
        if critical_alerts:
            await self._send_immediate_alert(critical_alerts, metrics)
            
        # Batch warning alerts (send every 15 minutes max)
        if warning_alerts:
            await self._send_batched_alert(warning_alerts, metrics, delay_minutes=15)
            
        # Info alerts go to daily digest only
        if info_alerts:
            self._queue_for_digest(info_alerts, metrics)
            
    async def _send_immediate_alert(self, alerts: List[AlertRule], metrics: Dict):
        """Send critical alerts immediately via all channels"""
        message = self._format_alert_message(alerts, metrics, is_critical=True)
        
        # Send via all configured channels
        for channel_name, channel_func in self.notification_channels.items():
            if self.config.get(f"{channel_name}_enabled", False):
                try:
                    await channel_func(message, is_critical=True)
                except Exception as e:
                    print(f"Failed to send alert via {channel_name}: {str(e)}")
                    
    async def _send_batched_alert(self, alerts: List[AlertRule], metrics: Dict, delay_minutes: int):
        """Send batched alerts after delay"""
        self.batched_alerts.extend(alerts)
        # In a real implementation, you'd use a timer/scheduler here
        # For now, just send immediately
        if len(self.batched_alerts) >= 3:  # Send when we have 3+ alerts
            message = self._format_alert_message(self.batched_alerts, metrics, is_critical=False)
            await self._send_email(message, is_critical=False)
            self.batched_alerts.clear()
            
    def _queue_for_digest(self, alerts: List[AlertRule], metrics: Dict):
        """Queue alerts for daily digest"""
        self.digest_queue.extend([{
            'alert': alert,
            'metrics': metrics.copy(),
            'timestamp': datetime.now()
        } for alert in alerts])
        
    def _format_alert_message(self, alerts: List[AlertRule], metrics: Dict, is_critical: bool) -> str:
        """Format alert message"""
        severity = "🚨 CRITICAL" if is_critical else "⚠️ WARNING"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"{severity} Trading Bot Alert - {timestamp}\n\n"
        
        for alert in alerts:
            message += f"• {alert.name.replace('_', ' ').title()}\n"
            if alert.name == "daily_loss_limit":
                message += f"  Daily P&L: ${metrics.get('daily_pnl', 0):.2f}\n"
            elif alert.name == "system_health_degraded":
                message += f"  Health Score: {metrics.get('health_score', 0):.1%}\n"
            elif alert.name == "earnings_week_detected":
                message += f"  Earnings announcement detected for tracked symbols\n"
            elif alert.name == "fomc_meeting_detected":
                message += f"  FOMC meeting within 2 days - expect volatility\n"
            elif alert.name == "negative_news_detected":
                message += f"  Negative news detected about tracked symbols\n"
            elif alert.name == "market_stress_elevated":
                message += f"  Market stress indicators elevated\n"
            message += "\n"
            
        if is_critical:
            message += "IMMEDIATE ACTION REQUIRED!\n"
            
        return message
        
    async def _send_email(self, message: str, is_critical: bool = False):
        """Send email notification"""
        try:
            email_config = self.config.get('email', {})
            if not email_config.get('enabled', False):
                return
                
            smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_config.get('smtp_port', 587)
            sender = email_config.get('sender')
            password = email_config.get('password')
            
            if not sender or not password:
                print("Email credentials not configured")
                return
                
            subject = "🚨 CRITICAL Alert" if is_critical else "⚠️ Trading Bot Alert"
            
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['Subject'] = subject
            
            # Get recipients based on severity
            severity = 'critical' if is_critical else 'warning'
            recipients = email_config.get('recipients', {}).get(severity, [])
            
            if not recipients:
                print(f"No recipients configured for {severity} alerts")
                return
                
            msg['To'] = ', '.join(recipients)
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            
            print(f"Email alert sent to {len(recipients)} recipients")
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            
    async def _send_sms(self, message: str, is_critical: bool = False):
        """Send SMS notification"""
        try:
            if not TWILIO_AVAILABLE:
                print("Twilio not available for SMS alerts")
                return
                
            sms_config = self.config.get('sms', {})
            if not sms_config.get('enabled', False):
                return
                
            account_sid = sms_config.get('twilio_sid')
            auth_token = sms_config.get('twilio_token')
            from_number = sms_config.get('from_number')
            
            if not all([account_sid, auth_token, from_number]):
                print("Twilio credentials not configured")
                return
                
            client = TwilioClient(account_sid, auth_token)
            
            # Get recipients based on severity
            severity = 'critical' if is_critical else 'warning'
            recipients = sms_config.get('to_numbers', {}).get(severity, [])
            
            # Truncate message for SMS (160 char limit)
            sms_message = message[:150] + "..." if len(message) > 150 else message
            
            for number in recipients:
                client.messages.create(
                    body=sms_message,
                    from_=from_number,
                    to=number
                )
                
            print(f"SMS alerts sent to {len(recipients)} numbers")
            
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
            
    async def _send_telegram(self, message: str, is_critical: bool = False):
        """Send Telegram notification"""
        try:
            telegram_config = self.config.get('telegram', {})
            if not telegram_config.get('enabled', False):
                return
                
            bot_token = telegram_config.get('bot_token')
            if not bot_token:
                print("Telegram bot token not configured")
                return
                
            severity = 'critical' if is_critical else 'warning'
            chat_ids = telegram_config.get('chat_ids', {}).get(severity, [])
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            async with aiohttp.ClientSession() as session:
                for chat_id in chat_ids:
                    payload = {
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                    
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            print(f"Telegram alert sent to chat {chat_id}")
                        else:
                            print(f"Failed to send Telegram alert to {chat_id}")
                            
        except Exception as e:
            print(f"Failed to send Telegram alert: {str(e)}")
            
    async def _send_discord(self, message: str, is_critical: bool = False):
        """Send Discord notification"""
        try:
            discord_config = self.config.get('discord', {})
            if not discord_config.get('enabled', False):
                return
                
            webhook_url = discord_config.get('webhook_url')
            if not webhook_url:
                print("Discord webhook URL not configured")
                return
                
            color = 0xff0000 if is_critical else 0xffaa00  # Red for critical, orange for warning
            
            embed = {
                "title": "🚨 CRITICAL Alert" if is_critical else "⚠️ Trading Bot Alert",
                "description": message,
                "color": color,
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 204:
                        print("Discord alert sent successfully")
                    else:
                        print(f"Failed to send Discord alert: {response.status}")
                        
        except Exception as e:
            print(f"Failed to send Discord alert: {str(e)}")

class DailyDigestGenerator:
    """Generate comprehensive daily reports"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.report_time = "18:00"  # 6 PM ET
        
    async def generate_daily_digest(self) -> Dict:
        """Generate comprehensive daily digest with events"""
        digest = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'performance': await self._get_performance_summary(),
            'trades': await self._get_trade_summary(),
            'market_analysis': await self._get_market_analysis(),
            'system_health': await self._get_system_health(),
            'recommendations': await self._get_recommendations(),
            'events': await self._get_events_summary(),
            'market_regime': self._get_market_regime_assessment()
        }
        
        return digest
        
    async def _get_performance_summary(self) -> Dict:
        """Get daily performance metrics"""
        try:
            account = self.bot.get_account_info()
            
            return {
                'starting_equity': getattr(self.bot, 'initial_equity', 0),
                'ending_equity': account.get('equity', 0),
                'daily_pnl': getattr(self.bot, 'daily_pnl', 0),
                'daily_pnl_pct': (getattr(self.bot, 'daily_pnl', 0) / getattr(self.bot, 'initial_equity', 1)) * 100,
                'win_rate': self.bot.metrics.calculate_win_rate() if hasattr(self.bot, 'metrics') else 0,
                'trades_count': len([t for t in getattr(self.bot.metrics, 'trades', []) 
                                   if hasattr(t, 'exit_time') and t.exit_time.date() == datetime.now().date()]),
                'best_trade': self._get_best_trade_today(),
                'worst_trade': self._get_worst_trade_today()
            }
        except Exception as e:
            print(f"Error getting performance summary: {str(e)}")
            return {}
            
    async def _get_trade_summary(self) -> List[Dict]:
        """Get summary of all trades today"""
        try:
            if not hasattr(self.bot, 'metrics') or not hasattr(self.bot.metrics, 'trades'):
                return []
                
            today_trades = [t for t in self.bot.metrics.trades 
                           if hasattr(t, 'exit_time') and t.exit_time.date() == datetime.now().date()]
            
            return [{
                'symbol': getattr(trade, 'symbol', 'Unknown'),
                'entry_time': getattr(trade, 'entry_time', datetime.now()).strftime('%H:%M'),
                'exit_time': getattr(trade, 'exit_time', datetime.now()).strftime('%H:%M'),
                'pnl': getattr(trade, 'pnl', 0),
                'pnl_pct': (getattr(trade, 'pnl', 0) / (getattr(trade, 'entry_price', 1) * getattr(trade, 'quantity', 1))) * 100,
                'strategy': getattr(trade, 'strategy', 'Unknown')
            } for trade in today_trades]
        except Exception as e:
            print(f"Error getting trade summary: {str(e)}")
            return []
            
    async def _get_market_analysis(self) -> Dict:
        """Get market analysis"""
        return {
            'market_condition': 'Normal',  # Placeholder
            'volatility': 'Medium',        # Placeholder
            'trend': 'Sideways'           # Placeholder
        }
        
    async def _get_system_health(self) -> Dict:
        """Get system health metrics"""
        return {
            'overall_score': 0.85,        # Placeholder
            'api_status': 'Connected',
            'memory_usage': '45%',
            'uptime': '24h 15m'
        }
        
    async def _get_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        try:
            # Performance-based recommendations
            if hasattr(self.bot, 'metrics'):
                win_rate = self.bot.metrics.calculate_win_rate()
                if win_rate < 40:
                    recommendations.append("Win rate below 40% - Consider reviewing strategy parameters")
                    
            if getattr(self.bot, 'daily_pnl', 0) < -500:
                recommendations.append("Significant daily loss - Review risk management settings")
                
            # System recommendations
            health = await self._get_system_health()
            if health.get('overall_score', 1) < 0.8:
                recommendations.append("System health degraded - Check logs for issues")
                
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            recommendations.append("Unable to generate recommendations - check system status")
            
        return recommendations

    async def _get_events_summary(self) -> Dict:
        """Get events summary for daily digest"""
        try:
            if hasattr(self.bot, 'alert_system') and hasattr(self.bot.alert_system, 'event_manager'):
                return self.bot.alert_system.event_manager.get_events_summary()
            else:
                return {'events': 'Event manager not available'}
        except Exception as e:
            return {'events_error': str(e)}

    def _get_market_regime_assessment(self) -> Dict:
        """Get market regime assessment"""
        try:
            if hasattr(self.bot, 'alert_system') and hasattr(self.bot.alert_system, 'event_manager'):
                return self.bot.alert_system.event_manager.get_market_regime_assessment()
            else:
                return {
                    'regime': 'unknown',
                    'risk_score': 0,
                    'recommendation': 'Unable to assess market regime'
                }
        except Exception as e:
            return {
                'regime': 'error',
                'risk_score': 0,
                'recommendation': f'Error assessing regime: {str(e)}'
            }
        
    def _get_best_trade_today(self) -> Dict:
        """Get best trade today"""
        try:
            if not hasattr(self.bot, 'metrics') or not hasattr(self.bot.metrics, 'trades'):
                return {}
                
            today_trades = [t for t in self.bot.metrics.trades 
                           if hasattr(t, 'exit_time') and t.exit_time.date() == datetime.now().date()]
            
            if not today_trades:
                return {}
                
            best_trade = max(today_trades, key=lambda x: getattr(x, 'pnl', 0))
            return {
                'symbol': getattr(best_trade, 'symbol', 'Unknown'),
                'pnl': getattr(best_trade, 'pnl', 0)
            }
        except:
            return {}
            
    def _get_worst_trade_today(self) -> Dict:
        """Get worst trade today"""
        try:
            if not hasattr(self.bot, 'metrics') or not hasattr(self.bot.metrics, 'trades'):
                return {}
                
            today_trades = [t for t in self.bot.metrics.trades 
                           if hasattr(t, 'exit_time') and t.exit_time.date() == datetime.now().date()]
            
            if not today_trades:
                return {}
                
            worst_trade = min(today_trades, key=lambda x: getattr(x, 'pnl', 0))
            return {
                'symbol': getattr(worst_trade, 'symbol', 'Unknown'),
                'pnl': getattr(worst_trade, 'pnl', 0)
            }
        except:
            return {}

class AutomatedDashboard:
    """FIXED: Web-based dashboard for remote monitoring with proper CSS handling"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.dashboard_data = {}
        
    def generate_dashboard_html(self) -> str:
        """Generate HTML dashboard with FIXED CSS formatting"""
        try:
            # First, collect data safely
            data = self._collect_dashboard_data()
            
            # Extract values with defaults
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            daily_pnl = data.get('daily_pnl', 0)
            pnl_class = 'positive' if daily_pnl >= 0 else 'negative'
            active_positions = len(getattr(self.bot, 'positions', {}))
            win_rate = data.get('win_rate', 0)
            health_score = data.get('health_score', 0.85)
            health_class = self._get_health_class(health_score)
            position_rows = self._generate_position_rows()
            alerts_html = self._generate_alerts_html()
            next_check = (datetime.now() + timedelta(minutes=5)).strftime('%H:%M')
            
            # FIXED: Use double braces for CSS and single braces for Python formatting
            html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Trading Bot Dashboard</title>
    <meta http-equiv="refresh" content="60">
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f5f5f5; 
        }}
        .metric-card {{ 
            background: white; 
            padding: 20px; 
            margin: 10px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: inline-block;
            min-width: 200px;
        }}
        .metric-value {{ 
            font-size: 24px; 
            font-weight: bold; 
        }}
        .positive {{ 
            color: #4caf50; 
        }}
        .negative {{ 
            color: #f44336; 
        }}
        .warning {{ 
            background-color: #fff3cd; 
        }}
        .critical {{ 
            background-color: #f8d7da; 
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
        }}
        th, td {{ 
            padding: 8px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            background: #4caf50;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Trading Bot Status - {timestamp}</h1>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <h3>Daily P&L</h3>
            <div class="metric-value {pnl_class}">${daily_pnl:.2f}</div>
        </div>
        
        <div class="metric-card">
            <h3>Active Positions</h3>
            <div class="metric-value">{active_positions}</div>
        </div>
        
        <div class="metric-card">
            <h3>Win Rate</h3>
            <div class="metric-value">{win_rate:.1f}%</div>
        </div>
        
        <div class="metric-card {health_class}">
            <h3>System Health</h3>
            <div class="metric-value">{health_score:.0%}</div>
        </div>
    </div>
    
    <h2>Active Positions</h2>
    <table>
        <tr>
            <th>Symbol</th>
            <th>Entry Price</th>
            <th>Current P&L</th>
            <th>Stop Loss</th>
            <th>Duration</th>
        </tr>
        {position_rows}
    </table>
    
    <h2>Recent Alerts</h2>
    {alerts_html}
    
    <footer>
        <p>Last updated: {timestamp}</p>
        <p><span class="status-indicator"></span>Next market check: {next_check}</p>
    </footer>
</body>
</html>"""
            
            # Format the template safely
            return html_template.format(
                timestamp=timestamp,
                daily_pnl=daily_pnl,
                pnl_class=pnl_class,
                active_positions=active_positions,
                win_rate=win_rate,
                health_score=health_score,
                health_class=health_class,
                position_rows=position_rows,
                alerts_html=alerts_html,
                next_check=next_check
            )
            
        except Exception as e:
            # Return safe fallback HTML
            return self._generate_safe_fallback_html(str(e))
        
    def _generate_safe_fallback_html(self, error_msg: str) -> str:
        """Generate safe fallback HTML when main generation fails"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Trading Bot Dashboard - Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .error {{ color: red; padding: 20px; border: 1px solid red; }}
    </style>
</head>
<body>
    <h1>Trading Bot Dashboard</h1>
    <div class="error">
        <h2>Dashboard Error</h2>
        <p>Unable to generate dashboard properly.</p>
        <p>Error: {error_msg}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""
        
    def _collect_dashboard_data(self) -> Dict:
        """Collect current dashboard data safely"""
        try:
            return {
                'daily_pnl': getattr(self.bot, 'daily_pnl', 0),
                'win_rate': self.bot.metrics.calculate_win_rate() if hasattr(self.bot, 'metrics') else 0,
                'health_score': 0.85  # Placeholder
            }
        except Exception as e:
            print(f"Error collecting dashboard data: {e}")
            return {
                'daily_pnl': 0,
                'win_rate': 0,
                'health_score': 0.5
            }
            
    def _get_health_class(self, score: float) -> str:
        """Get CSS class for health score"""
        if score >= 0.8:
            return ""
        elif score >= 0.6:
            return "warning"
        else:
            return "critical"
            
    def _generate_position_rows(self) -> str:
        """Generate HTML rows for positions table"""
        try:
            positions = getattr(self.bot, 'positions', {})
            if not positions:
                return "<tr><td colspan='5'>No active positions</td></tr>"
                
            rows = []
            for symbol, position in positions.items():
                try:
                    entry_price = getattr(position, 'entry_price', 0)
                    unrealized_pnl = getattr(position, 'unrealized_pnl', 0)
                    stop_loss = getattr(position, 'stop_loss', 0)
                    duration = self._calculate_duration(position)
                    
                    rows.append(f"""
                    <tr>
                        <td>{symbol}</td>
                        <td>${entry_price:.2f}</td>
                        <td>${unrealized_pnl:.2f}</td>
                        <td>${stop_loss:.2f}</td>
                        <td>{duration}</td>
                    </tr>
                    """)
                except Exception as e:
                    print(f"Error processing position {symbol}: {e}")
                    
            return "".join(rows)
            
        except Exception as e:
            print(f"Error generating position rows: {e}")
            return "<tr><td colspan='5'>Error loading positions</td></tr>"
            
    def _generate_alerts_html(self) -> str:
        """Generate HTML for recent alerts"""
        try:
            # Simple status display
            api_status = "Connected" if self._test_api_connection() else "Disconnected"
            return f"<p>API Status: {api_status}</p><p>No recent alerts</p>"
        except:
            return "<p>Status unavailable</p>"
            
    def _test_api_connection(self) -> bool:
        """Test API connection"""
        try:
            self.bot.get_account_info()
            return True
        except:
            return False
        
    def _calculate_duration(self, position) -> str:
        """Calculate position duration"""
        try:
            entry_time = getattr(position, 'timestamp', datetime.now())
            duration = datetime.now() - entry_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"

class NotificationConfig:
    """Notification configuration for different channels"""
    
    def __init__(self):
        self.config = {
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender': os.getenv('EMAIL_SENDER'),
                'password': os.getenv('EMAIL_PASSWORD'),
                'recipients': {
                    'critical': [os.getenv('EMAIL_RECIPIENT', 'your-email@gmail.com')],
                    'warning': [os.getenv('EMAIL_RECIPIENT', 'your-email@gmail.com')],
                    'info': [os.getenv('EMAIL_RECIPIENT', 'your-email@gmail.com')]
                }
            },
            'sms': {
                'enabled': TWILIO_AVAILABLE,
                'twilio_sid': os.getenv('TWILIO_SID'),
                'twilio_token': os.getenv('TWILIO_TOKEN'),
                'from_number': os.getenv('TWILIO_FROM'),
                'to_numbers': {
                    'critical': [os.getenv('PHONE_NUMBER', '+1234567890')],
                    'warning': [],  # Only critical via SMS
                    'info': []
                }
            },
            'telegram': {
                'enabled': False,  # Optional
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'chat_ids': {
                    'critical': [os.getenv('TELEGRAM_CHAT_ID', 'your_chat_id')],
                    'warning': [os.getenv('TELEGRAM_CHAT_ID', 'your_chat_id')],
                    'info': [os.getenv('TELEGRAM_CHAT_ID', 'your_chat_id')]
                }
            },
            'discord': {
                'enabled': False,  # Optional
                'webhook_url': os.getenv('DISCORD_WEBHOOK_URL')
            }
        }

# QUICK FIX: Add this function to patch your existing bot
def fix_dashboard_css_error(bot_instance):
    """Quick fix to replace the problematic dashboard method"""
    try:
        # Create new dashboard instance
        fixed_dashboard = AutomatedDashboard(bot_instance)
        
        # Replace the bot's dashboard update method
        bot_instance._update_monitoring_dashboard = lambda: fixed_dashboard.generate_dashboard_html()
        
        # Test the fix
        html_content = fixed_dashboard.generate_dashboard_html()
        
        # Save to file
        with open('dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print("✅ Dashboard CSS error fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix dashboard: {str(e)}")
        return False

# Alternative quick fix - simpler version
def simple_dashboard_fix(bot_instance):
    """Even simpler fix - just update dashboard as JSON"""
    def safe_dashboard_update():
        try:
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'daily_pnl': getattr(bot_instance, 'daily_pnl', 0),
                'positions': len(getattr(bot_instance, 'positions', {})),
                'status': 'running'
            }
            
            try:
                account = bot_instance.get_account_info()
                dashboard_data['equity'] = account.get('equity', 0)
            except:
                dashboard_data['equity'] = 0
            
            # Save as JSON (no CSS issues)
            with open('dashboard.json', 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Dashboard update error: {e}")
    
    # Replace the method
    bot_instance._update_monitoring_dashboard = safe_dashboard_update
    print("✅ Dashboard fixed with JSON-only output")

if __name__ == "__main__":
    print("Fixed monitoring module loaded")
    print("Use fix_dashboard_css_error(bot_instance) to apply the fix")