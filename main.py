#!/usr/bin/env python3
"""
Enhanced Autonomous Trading Bot v3.0
Fully autonomous with minimal supervision required
Budget: <$10/day infrastructure
Capital: $50k account, $10k active trading
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json
import os
import pandas as pd
import numpy as np

# Import original modules
from algo_trading_bot_v5 import AlgoTradingBot, TradingMetrics
from fundamental_data import FundamentalDataProvider
from economic_calendar import EconomicCalendar
from news_sentiment import NewsSentimentAnalyzer
from market_events import MarketEventManager
from monitoring import SmartAlertSystem, DailyDigestGenerator, AutomatedDashboard, NotificationConfig

class AutonomousTradingBot(AlgoTradingBot):
    """
    Fully autonomous trading bot with enhanced features
    """
    
    def __init__(self, config: Dict):
        # Initialize base bot
        super().__init__(config)
        
        # Initialize enhanced components (simplified for now)
        self.error_recovery_enabled = config.get('AUTO_RECOVERY_ENABLED', True)
        self.health_check_enabled = True
        
        # State management
        self.state = self._load_state()
        self.last_health_check = datetime.now()
        self.consecutive_errors = 0
        self.shutdown_requested = False
        
        # Enhanced configuration
        self.config.update({
            'extended_hours_enabled': True,
            'auto_recovery_enabled': True,
            'smart_alerts_enabled': True,
            'max_consecutive_errors': 10,
            'health_check_interval': 300,  # 5 minutes
            'state_save_interval': 60,  # 1 minute
        })
        
        # Dashboard data
        self.dashboard_data = {}
        
        self.logger.info("Autonomous Trading Bot v3.0 initialized")

        try:
            # Initialize fundamental data provider
            if os.getenv('ALPHA_VANTAGE_KEY'):
                self.fundamental_data = FundamentalDataProvider(os.getenv('ALPHA_VANTAGE_KEY'))
                self.logger.info("Fundamental data provider initialized")
            else:
                self.fundamental_data = None
                self.logger.warning("Alpha Vantage key not found - fundamental analysis disabled")
                
            # Initialize economic calendar
            if os.getenv('FRED_API_KEY'):
                self.economic_calendar = EconomicCalendar(os.getenv('FRED_API_KEY'))
                self.logger.info("Economic calendar initialized")
            else:
                self.economic_calendar = None
                self.logger.warning("FRED API key not found - economic analysis disabled")
                
            # Initialize news sentiment analyzer
            if os.getenv('NEWS_API_KEY'):
                self.news_analyzer = NewsSentimentAnalyzer(os.getenv('NEWS_API_KEY'))
                self.logger.info("News sentiment analyzer initialized")
            else:
                self.news_analyzer = None
                self.logger.warning("News API key not found - news analysis disabled")
                
            # Initialize market events manager
            self.event_manager = MarketEventManager(self)
            self.logger.info("Market events manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced components: {str(e)}")
            # Set to None if initialization fails
            self.fundamental_data = None
            self.economic_calendar = None
            self.news_analyzer = None
            self.event_manager = None

         # Initialize monitoring and alerting system
        try:
            # Get notification configuration
            notification_config = NotificationConfig().config
            
            # Initialize smart alert system
            self.alert_system = SmartAlertSystem(notification_config)
            self.logger.info("Smart alert system initialized")
            
            # Initialize daily digest generator
            self.digest_generator = DailyDigestGenerator(self)
            self.logger.info("Daily digest generator initialized")
            
            # Initialize dashboard
            self.dashboard = AutomatedDashboard(self)
            self.logger.info("Automated dashboard initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring systems: {str(e)}")
            self.alert_system = None
            self.digest_generator = None
            self.dashboard = None
        
    def _load_state(self) -> Dict:
        """Load saved state from disk"""
        state_file = 'bot_state.json'
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'last_run': None,
            'total_trades': 0,
            'total_pnl': 0.0,
            'uptime_hours': 0,
            'last_positions': {}
        }
        
    def _save_state(self):
        """Save current state to disk"""
        self.state.update({
            'last_run': datetime.now().isoformat(),
            'total_trades': len(self.metrics.trades),
            'total_pnl': sum(t.pnl for t in self.metrics.trades),
            'current_positions': {
                symbol: {
                    'entry_price': pos.entry_price,
                    'quantity': pos.quantity,
                    'timestamp': pos.timestamp.isoformat()
                } for symbol, pos in self.positions.items()
            }
        })
        
        with open('bot_state.json', 'w') as f:
            json.dump(self.state, f, indent=2)

    async def _preload_historical_data(self):
        """Preload historical data for faster analysis"""
        try:
            self.logger.info("Preloading historical data...")
            symbols = self._select_symbols()[:10]  # Limit to top 10 for efficiency
            
            for symbol in symbols:
                try:
                    # Cache 100 days of data
                    data = self._get_historical_data(symbol, days=100)
                    if not data.empty:
                        self.logger.debug(f"Cached {len(data)} bars for {symbol}")
                except Exception as e:
                    self.logger.warning(f"Failed to cache data for {symbol}: {str(e)}")
                    
            self.logger.info("Historical data preloading complete")
            
        except Exception as e:
            self.logger.error(f"Failed to preload historical data: {str(e)}")

    async def _start_dashboard_server(self):
        """Start simple dashboard server (placeholder)"""
        try:
            self.logger.info("Dashboard server started (placeholder)")
            # In a real implementation, this would start a web server
            # For now, we'll just create a dashboard file
            self._update_dashboard()
            
        except Exception as e:
            self.logger.error(f"Failed to start dashboard server: {str(e)}")

    async def _filter_symbols_ml(self, symbols: List[str]) -> List[str]:
        """Filter symbols using ML criteria"""
        filtered = []
        for symbol in symbols:
            try:
                # Simple momentum filter
                data = self._get_historical_data(symbol, days=20)
                if not data.empty and len(data) >= 10:
                    momentum = (data['close'].iloc[-1] / data['close'].iloc[-10] - 1) * 100
                    volatility = data['close'].pct_change().std() * 100
                    
                    # Filter criteria: moderate momentum and volatility
                    if abs(momentum) > 2 and volatility < 5:
                        filtered.append(symbol)
                        
            except Exception as e:
                self.logger.debug(f"ML filter error for {symbol}: {str(e)}")
                
        return filtered[:5]  # Return top 5

    async def _execute_enhanced_trade(self, symbol: str, signal: str):
        """Execute trade with enhanced features"""
        try:
            # Use existing execute_trade method with error handling
            self.execute_trade(symbol, signal)
            
        except Exception as e:
            self.logger.error(f"Enhanced trade execution failed for {symbol}: {str(e)}")

    async def _check_volatility_exit(self, symbol: str, position) -> bool:
        """Check if position should exit due to high volatility"""
        try:
            data = self._get_historical_data(symbol, days=10)
            if data.empty:
                return False
                
            recent_vol = data['close'].pct_change().tail(5).std()
            avg_vol = data['close'].pct_change().std()
            
            # Exit if volatility is 3x normal
            return recent_vol > avg_vol * 3
            
        except:
            return False

    async def _check_ml_exit_signal(self, symbol: str, position) -> bool:
        """Check ML-based exit signal"""
        try:
            if not self.config.get('USE_ML_SIGNALS', False):
                return False
                
            signal_strength = self._calculate_signal_strength(
                self._create_ml_features(self._get_historical_data(symbol, days=50))
            )
            
            # Exit if signal strength reverses significantly
            return abs(signal_strength) > 0.8 and np.sign(signal_strength) != np.sign(position.quantity)
            
        except:
            return False

    async def _exit_position_enhanced(self, symbol: str, current_price: float, reason: str):
        """Enhanced position exit"""
        try:
            self._exit_position(symbol, current_price, reason)
            
            # Send alert for significant P&L
            position = self.positions.get(symbol)
            if position:
                pnl = (current_price - position.entry_price) * position.quantity
                if abs(pnl) > 1000:  # Alert for P&L > $1000
                    await self._send_alert(f"Large P&L exit: {symbol} ${pnl:.2f}")
                    
        except Exception as e:
            self.logger.error(f"Enhanced exit failed for {symbol}: {str(e)}")

    def _update_position_metrics(self, symbol: str, metrics: Dict):
        """Update position metrics for dashboard"""
        if symbol not in self.dashboard_data:
            self.dashboard_data[symbol] = {}
        self.dashboard_data[symbol].update(metrics)

    async def _update_metrics_and_alerts(self, additional_metrics: Dict = None):
        """Update metrics and check for alerts"""
        try:
            # Calculate current metrics
            account_info = self.get_account_info()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'equity': account_info['equity'],
                'daily_pnl': self.daily_pnl,
                'positions': len(self.positions),
                'win_rate': self.metrics.calculate_win_rate()
            }
            
            if additional_metrics:
                metrics.update(additional_metrics)
                
            # Check for alert conditions
            if self.daily_pnl < -500:  # Daily loss > $500
                await self._send_alert(f"Daily loss alert: ${self.daily_pnl:.2f}")
                
            if len(self.positions) >= self.config['MAX_POSITIONS']:
                await self._send_alert("Maximum positions reached")
                
        except Exception as e:
            self.logger.error(f"Metrics update failed: {str(e)}")

    def _update_dashboard(self):
        """Update dashboard data"""
        try:
            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'status': 'running',
                'market_open': self.is_market_open(),
                'equity': self.get_account_info()['equity'] if hasattr(self, 'trade_client') else 0,
                'daily_pnl': self.daily_pnl,
                'positions': len(self.positions),
                'total_trades': len(self.metrics.trades),
                'win_rate': self.metrics.calculate_win_rate(),
                'position_details': self.dashboard_data
            }
            
            with open('dashboard.json', 'w') as f:
                json.dump(dashboard, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Dashboard update failed: {str(e)}")

    def _log_progress(self, loop_count: int):
        """Log progress information"""
        try:
            account_info = self.get_account_info()
            self.logger.info(
                f"Loop #{loop_count} - Equity: ${account_info['equity']:,.2f}, "
                f"Daily P&L: ${self.daily_pnl:.2f}, "
                f"Positions: {len(self.positions)}, "
                f"Trades: {len(self.metrics.trades)}"
            )
        except Exception as e:
            self.logger.error(f"Progress logging failed: {str(e)}")

    async def _handle_critical_failure(self):
        """Handle critical system failure"""
        self.logger.critical("Critical failure detected - initiating emergency procedures")
        
        try:
            # Close all positions
            for symbol in list(self.positions.keys()):
                quote_data = self.get_real_time_data(symbol)
                if not quote_data.empty:
                    current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                    self._exit_position(symbol, current_price, "Critical failure")
                    
            # Send critical alert
            await self._send_alert("CRITICAL: Trading bot failure - all positions closed")
            
        except Exception as e:
            self.logger.error(f"Critical failure handling error: {str(e)}")

    async def _send_alert(self, message: str, severity: str = 'warning'):
        """Enhanced alert sending using smart alert system"""
        try:
            # Log the alert
            self.logger.warning(f"ALERT: {message}")
            
            # Use smart alert system if available
            if self.alert_system:
                # Create metrics for alert evaluation
                alert_metrics = {
                    'custom_alert': True,
                    'alert_message': message,
                    'severity': severity,
                    'events': ['custom_alert']
                }
                await self.alert_system.evaluate_alerts(alert_metrics)
            else:
                # Fallback to simple print
                print(f"🚨 {severity.upper()}: {message}")
                
        except Exception as e:
            self.logger.error(f"Alert sending failed: {str(e)}")
            # Ultimate fallback
            print(f"🚨 {severity.upper()}: {message}")

    async def _send_daily_digest(self, digest: Dict):
        """Send daily digest"""
        try:
            self.logger.info("Sending daily digest")
            # Save digest to file
            with open(f'daily_digest_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
                json.dump(digest, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Daily digest failed: {str(e)}")

    def _cleanup_old_logs(self):
        """Cleanup old log files"""
        try:
            logs_dir = 'logs'
            if os.path.exists(logs_dir):
                cutoff = datetime.now() - timedelta(days=30)
                for file in os.listdir(logs_dir):
                    file_path = os.path.join(logs_dir, file)
                    if os.path.getctime(file_path) < cutoff.timestamp():
                        os.remove(file_path)
                        self.logger.debug(f"Removed old log: {file}")
                        
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {str(e)}")

    def _optimize_storage(self):
        """Optimize storage usage"""
        try:
            # Compress old data files
            self.logger.debug("Storage optimization complete")
            
        except Exception as e:
            self.logger.error(f"Storage optimization failed: {str(e)}")

    async def _update_ml_models(self):
        """Update ML models with new data"""
        try:
            if not self.config.get('USE_ML_SIGNALS', False):
                return
                
            self.logger.info("Updating ML models")
            # Placeholder for ML model updates
            
        except Exception as e:
            self.logger.error(f"ML model update failed: {str(e)}")

    def _backup_critical_data(self):
        """Backup critical data"""
        try:
            # Save state and important files
            self._save_state()
            self.logger.debug("Critical data backup complete")
            
        except Exception as e:
            self.logger.error(f"Data backup failed: {str(e)}")

    async def _perform_health_check(self):
        """Perform system health check"""
        try:
            health_score = 1.0
            
            # Check API connectivity
            try:
                self.get_account_info()
            except:
                health_score -= 0.3
                
            # Check data connectivity
            try:
                test_data = self.get_real_time_data('AAPL')
                if test_data.empty:
                    health_score -= 0.2
            except:
                health_score -= 0.3
                
            # Check disk space
            import shutil
            disk_usage = shutil.disk_usage('.')
            free_pct = disk_usage.free / disk_usage.total
            if free_pct < 0.1:  # Less than 10% free
                health_score -= 0.2
                
            self.last_health_check = datetime.now()
            
            if health_score < 0.7:
                self.logger.warning(f"System health degraded: {health_score:.2f}")
                
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")

    async def _perform_maintenance(self):
        """Perform maintenance tasks during market close"""
        self.logger.info("Performing maintenance tasks")
        
        try:
            # Generate daily digest
            if datetime.now().hour == 18:  # 6 PM
                digest = {
                    'date': datetime.now().date().isoformat(),
                    'total_trades': len(self.metrics.trades),
                    'daily_pnl': self.daily_pnl,
                    'win_rate': self.metrics.calculate_win_rate(),
                    'positions': len(self.positions)
                }
                await self._send_daily_digest(digest)
                
            # Cleanup and optimization
            self._cleanup_old_logs()
            self._optimize_storage()
            
            # Update ML models if needed
            if self.config.get('USE_ML_SIGNALS', False):
                await self._update_ml_models()
                
            # Backup critical data
            self._backup_critical_data()
            
        except Exception as e:
            self.logger.error(f"Maintenance error: {str(e)}")

    def get_current_session(self) -> str:
        """Determine current market session"""
        now = datetime.now()
        hour = now.hour
        
        # Simplified session detection (EST)
        if 4 <= hour < 9:
            return 'pre_market'
        elif 9 <= hour < 16:
            return 'regular'
        elif 16 <= hour < 20:
            return 'after_hours'
        else:
            return 'closed'

    async def _handle_pre_market_trading(self):
        """Enhanced pre-market trading with event awareness"""
        self.logger.debug("Pre-market session - enhanced event-aware trading")
        
        # Only trade most liquid symbols in pre-market
        liquid_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA']
        
        for symbol in liquid_symbols:
            if symbol in self.positions:
                continue
                
            try:
                # Get pre-market risk adjustment
                pre_market_adjustment = 0.5  # Default 50% reduction
                
                if self.event_manager:
                    pre_market_adjustment = self.event_manager.get_pre_market_risk_adjustment(symbol)
                    
                if pre_market_adjustment == 0.0:
                    self.logger.debug(f"Pre-market trading blocked for {symbol}")
                    continue
                    
                # Generate signal with event awareness
                signal = await self._generate_enhanced_signal(symbol)
                if signal:
                    # Apply additional pre-market risk reduction
                    original_risk = self.config['RISK_PCT']
                    self.config['RISK_PCT'] = original_risk * pre_market_adjustment
                    
                    await self._execute_enhanced_trade(symbol, signal)
                    
                    # Restore original risk
                    self.config['RISK_PCT'] = original_risk
                    
            except Exception as e:
                self.logger.error(f"Pre-market trading error for {symbol}: {str(e)}")

    async def _handle_regular_trading(self):
        """Handle regular market hours trading"""
        symbols = self._select_symbols()
        
        # Add ML-enhanced filtering
        if self.config.get('USE_ML_SIGNALS', False):
            symbols = await self._filter_symbols_ml(symbols)
            
        for symbol in symbols:
            if symbol in self.positions:
                continue
                
            try:
                signal = await self._generate_enhanced_signal(symbol)
                if signal:
                    await self._execute_enhanced_trade(symbol, signal)
                    
            except Exception as e:
                self.logger.error(f"Trading error for {symbol}: {str(e)}")

    async def _handle_after_hours_trading(self):
        """Handle after-hours trading (simplified)"""
        self.logger.debug("After-hours session - monitoring only")
        # Primarily monitor positions in after-hours
        await self._monitor_positions_enhanced()

    async def _generate_enhanced_signal(self, symbol: str) -> Optional[str]:
        """Generate trading signal with event-aware enhancements"""
        try:
            # Get base technical signals
            trend_signal = self.trend_following_strategy(symbol)
            mean_rev_signal = self.mean_reversion_strategy(symbol)
            
            # ML signal if enabled
            ml_signal = None
            if self.config.get('USE_ML_SIGNALS', False):
                ml_signal = self.ml_enhanced_signal(symbol)
                
            # Combine base signals
            if self.config['STRATEGY'] == 'combined':
                signals = [s for s in [trend_signal, mean_rev_signal, ml_signal] if s is not None]
                if signals.count('buy') >= 2:
                    base_signal = 'buy'
                elif signals.count('sell') >= 2:
                    base_signal = 'sell'
                else:
                    base_signal = None
            else:
                base_signal = trend_signal or mean_rev_signal
                
            # If no base signal, return None
            if not base_signal:
                return None
                
            # NEW: Event-driven risk assessment
            if self.event_manager:
                should_enter, size_multiplier, reason = self.event_manager.should_enter_position(symbol, base_signal)
                
                if not should_enter:
                    self.logger.info(f"Trade blocked for {symbol}: {reason}")
                    return None
                    
                # Store the size multiplier for later use in position sizing
                self._event_risk_adjustments = getattr(self, '_event_risk_adjustments', {})
                self._event_risk_adjustments[symbol] = size_multiplier
                
                if size_multiplier < 1.0:
                    self.logger.info(f"Position size adjusted for {symbol}: {size_multiplier:.2f} - {reason}")
            
            return base_signal
            
        except Exception as e:
            self.logger.error(f"Enhanced signal generation failed for {symbol}: {str(e)}")
            return None

    async def _monitor_positions_enhanced(self):
        """Enhanced position monitoring with event-driven exits"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                
                # Get current data
                quote_data = self.get_real_time_data(symbol)
                if quote_data.empty:
                    continue
                    
                current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                
                # Calculate current P&L
                pnl = (current_price - position.entry_price) * position.quantity
                pnl_pct = (current_price / position.entry_price - 1) * 100
                hold_time = datetime.now() - position.timestamp
                
                # NEW: Event-driven exit check
                should_exit_event = False
                exit_reason = None
                
                if self.event_manager:
                    should_exit_event, exit_reason = self.event_manager.should_exit_position(symbol, pnl)
                    
                # Existing exit conditions
                if (should_exit_event or 
                    current_price <= position.stop_loss or 
                    current_price >= position.take_profit or
                    hold_time > timedelta(hours=24)):
                    
                    final_reason = exit_reason if should_exit_event else "Stop/Target/Time limit hit"
                    await self._exit_position_enhanced(symbol, current_price, final_reason)
                    
                # Update position metrics for dashboard
                self._update_position_metrics(symbol, {
                    'current_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'hold_time': hold_time.total_seconds() / 3600
                })
                
            except Exception as e:
                self.logger.error(f"Enhanced position monitoring error for {symbol}: {str(e)}")

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        self.logger.info(f"Shutdown signal received: {signum}")
        self.shutdown_requested = True

    async def _shutdown_cleanup(self):
        """Cleanup on shutdown"""
        self.logger.info("Performing shutdown cleanup")
        
        try:
            # Close all positions if requested
            if self.config.get('CLOSE_ON_SHUTDOWN', False):
                for symbol in list(self.positions.keys()):
                    quote_data = self.get_real_time_data(symbol)
                    if not quote_data.empty:
                        current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                        self._exit_position(symbol, current_price, "Shutdown")
                        
            # Save final state
            self._save_state()
            
            # Send shutdown notification
            await self._send_alert(
                f"Trading bot shutdown at {datetime.now()}. Final P&L: ${self.daily_pnl:.2f}",
                severity='info'
            )
            
        except Exception as e:
            self.logger.error(f"Shutdown cleanup error: {str(e)}")

    async def run_autonomous(self):
        """Main autonomous trading loop"""
        self.logger.info("Starting autonomous trading bot")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        # Initialize components
        await self._initialize_autonomous_components()
        
        # Main loop
        loop_count = 0
        last_state_save = datetime.now()
        last_alert_check = datetime.now()
        last_digest_time = datetime.now()
        
        while not self.shutdown_requested:
            try:
                loop_count += 1
                loop_start = datetime.now()
                
                # Health check
                if datetime.now() - self.last_health_check > timedelta(seconds=self.config['health_check_interval']):
                    await self._perform_health_check()
                    
                # Determine trading session
                session = self.get_current_session()
                
                if session == 'closed':
                    # Market closed - perform maintenance
                    await self._perform_maintenance()
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                    
                # Trading logic based on session
                if session == 'pre_market':
                    await self._handle_pre_market_trading()
                elif session == 'regular':
                    await self._handle_regular_trading()
                elif session == 'after_hours':
                    await self._handle_after_hours_trading()
                    
                # Monitor positions (all sessions)
                await self._monitor_positions_enhanced()
                
                # Update metrics and alerts
                await self._update_metrics_and_alerts()

                # ALERT EVALUATION (Every 5 minutes)
                if datetime.now() - last_alert_check > timedelta(minutes=5):
                    await self._evaluate_alerts()
                    last_alert_check = datetime.now()
                
                # DAILY DIGEST GENERATION (Once per day at 6 PM)
                current_hour = datetime.now().hour
                if (current_hour == 18 and  # 6 PM
                    datetime.now() - last_digest_time > timedelta(hours=23)):  # Once per day
                    await self._generate_daily_digest()
                    last_digest_time = datetime.now()

                # Save state periodically
                if datetime.now() - last_state_save > timedelta(seconds=self.config['state_save_interval']):
                    self._save_state()
                    last_state_save = datetime.now()
                    
                # Dashboard update
                if loop_count % 10 == 0:
                    self._update_monitoring_dashboard()
                    
                # Log progress
                if loop_count % 100 == 0:
                    self._log_progress(loop_count)
                    
                # Calculate sleep time
                loop_duration = (datetime.now() - loop_start).total_seconds()
                sleep_time = max(0, 60 - loop_duration)  # Target 1 minute loops
                await asyncio.sleep(sleep_time)
                
                # Reset error counter on successful loop
                self.consecutive_errors = 0
                
            except Exception as e:
                self.consecutive_errors += 1
                self.logger.error(f"Error in main loop: {str(e)}", exc_info=True)
                
                if (self.consecutive_errors >= 5 and 
                self.alert_system and 
                datetime.now() - last_alert_check > timedelta(minutes=10)):

                # Trigger critical system alert
                    await self.alert_system.evaluate_alerts({
                        'daily_pnl': self.daily_pnl,
                        'consecutive_errors': self.consecutive_errors,
                        'events': ['system_errors'],
                        'severity': 'critical'
                    })
                    last_alert_check = datetime.now()
                
                # Check if we've hit the maximum error threshold
                if self.consecutive_errors >= self.config['max_consecutive_errors']:
                    await self._handle_critical_failure()
                    break  # Exit the main loop
                    
                # Exponential backoff: wait longer after each consecutive error
                backoff_time = min(300, 30 * (2 ** self.consecutive_errors))
                await asyncio.sleep(backoff_time)
                
        # Cleanup
        await self._shutdown_cleanup()

    async def _initialize_autonomous_components(self):
        """Initialize all autonomous components"""
        try:
            # Setup infrastructure
            if not os.path.exists('bot_initialized'):
                os.makedirs('logs', exist_ok=True)
                with open('bot_initialized', 'w') as f:
                    f.write(datetime.now().isoformat())
                    
            # Load historical data for ML features
            await self._preload_historical_data()
            
            # Start dashboard server
            await self._start_dashboard_server()
            
            self.logger.info("Autonomous components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {str(e)}")
            raise

    # ADD this new method to the AutonomousTradingBot class:

    async def _evaluate_alerts(self):
        """Evaluate alerts based on current metrics"""
        if not self.alert_system:
            return
            
        try:
            # Collect current metrics for alert evaluation
            account_info = self.get_account_info()
        
            current_metrics = {
                'timestamp': datetime.now().isoformat(),
                'daily_pnl': self.daily_pnl,                    # Current day profit/loss
                'equity': account_info['equity'],               # Total account value
                'positions_count': len(self.positions),         # Number of open positions
                'win_rate': self.metrics.calculate_win_rate(),  # Percentage of winning trades
                'health_score': 0.85,                          # System health (0.0 to 1.0)
                'active_symbols': list(self.positions.keys()), # Currently traded symbols
                'consecutive_errors': self.consecutive_errors   # Error tracking
            }
            
            # Evaluate alerts with bot instance for event checking
            await self.alert_system.evaluate_alerts(current_metrics, bot_instance=self)
            
        except Exception as e:
            self.logger.error(f"Alert evaluation failed: {str(e)}")


    # ADD this new method for daily digest:
    async def _generate_daily_digest(self):
        """Generate and send daily digest"""
        if not self.digest_generator:
            return
            
        try:
            # Generate comprehensive daily digest
            digest = await self.digest_generator.generate_daily_digest()
            
            # Save to file
            digest_filename = f'daily_digest_{datetime.now().strftime("%Y%m%d")}.json'
            with open(digest_filename, 'w') as f:
                json.dump(digest, f, indent=2)
                
            self.logger.info(f"Daily digest generated: {digest_filename}")
            
            # Could also email the digest here if configured
            if self.alert_system and digest:
                digest_summary = f"""
                    Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}
                    Daily P&L: ${digest.get('performance', {}).get('daily_pnl', 0):.2f}
                    Total Trades: {digest.get('performance', {}).get('trades_count', 0)}
                    Win Rate: {digest.get('performance', {}).get('win_rate', 0):.1f}%
            """
            await self._send_alert(digest_summary, severity='info')

            return digest
            
        except Exception as e:
            self.logger.error(f"Daily digest generation failed: {str(e)}")

    # ADD this new method for dashboard updates:

    def _update_monitoring_dashboard(self):
        """Update monitoring dashboard"""
        if not self.dashboard:
            return
            
        try:
            # Generate HTML dashboard
            dashboard_html = self.dashboard.generate_dashboard_html()
            
            # Save dashboard HTML file
            with open('dashboard.html', 'w') as f:
                f.write(dashboard_html)
                
            # Also update JSON dashboard for API access
            self._update_dashboard()  # Your existing method
            self.logger.debug("Monitoring dashboard updated")
            
        except Exception as e:
            self.logger.error(f"Dashboard update failed: {str(e)}")


# Entry point
if __name__ == "__main__":
    # Enhanced configuration
    config = {
        # API Configuration
        'API_KEY': os.getenv('APCA_API_KEY_ID'),
        'SECRET_KEY': os.getenv('APCA_API_SECRET_KEY'),
        'PAPER_TRADING': True,
        
        # Capital Management
        'TOTAL_CAPITAL': 50000,
        'TRADING_CAPITAL': 10000,
        'RISK_PCT': 0.02,
        'MAX_POSITIONS': 3,
        'MAX_DAILY_LOSS': 0.02,
        
        # Strategy
        'STRATEGY': 'combined',
        'USE_ML_SIGNALS': True,
        'USE_ADAPTIVE_STOPS': True,
        
        # Extended Hours
        'EXTENDED_HOURS_ENABLED': True,
        'PRE_MARKET_RISK_REDUCTION': 0.5,
        
        # Infrastructure
        'USE_CLOUD_BACKUP': False,  # Start with local only
        'MAX_DAILY_INFRA_COST': 10.0,

        # NEW: Monitoring Configuration
        'monitoring': {
        'alerts_enabled': True,
        'alert_check_interval': 300,  # 5 minutes
        'daily_digest_enabled': True,
        'dashboard_enabled': True
    },
        
        # Alerts Configuration
        'alerts': {
            'email_enabled': True,
            'sms_enabled': False,
            'critical_only_sms': True,
            'daily_digest_time': '18:00'
        },
        
        # Autonomous Features
        'AUTO_RECOVERY_ENABLED': True,
        'SMART_ALERTS_ENABLED': True,
        'CLOSE_ON_SHUTDOWN': False,

    # Notification Settings
    'email_enabled': True,
    'sms_enabled': True,  # Only if you have Twilio setup
    'telegram_enabled': False,
    'discord_enabled': False
    }
    
    # Validate required environment variables
    if not config['API_KEY'] or not config['SECRET_KEY']:
        print("Error: Please set APCA_API_KEY_ID and APCA_API_SECRET_KEY environment variables")
        sys.exit(1)
    
    # Create and run bot
    try:
        bot = AutonomousTradingBot(config)
        asyncio.run(bot.run_autonomous())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Critical error: {str(e)}")
        sys.exit(1)