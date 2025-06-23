#!/usr/bin/env python3
"""
Enhanced Autonomous Trading Bot v4.0 - Industry Grade
Self-sufficient with robust error handling, fallbacks, and optimizations
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
import os
import pandas as pd
import numpy as np
import time
from collections import defaultdict

# Import original modules with error handling
try:
    from algo_trading_bot_v5 import AlgoTradingBot, TradingMetrics
    from fundamental_data import FundamentalDataProvider
    from economic_calendar import EconomicCalendar
    from news_sentiment import NewsSentimentAnalyzer
    from market_events import MarketEventManager
    from monitoring import SmartAlertSystem, DailyDigestGenerator, AutomatedDashboard, NotificationConfig
    from error_recovery import ErrorRecoverySystem, HealthMonitor, AutoRecoveryManager
except ImportError as e:
    print(f"Warning: Failed to import some modules: {e}")

class IndustryGradeAutonomousBot(AlgoTradingBot):
    """
    Industry-grade autonomous trading bot with enterprise features
    """
    
    def __init__(self, config: Dict):
        # Initialize base bot with enhanced error handling
        try:
            super().__init__(config)
        except Exception as e:
            self.logger.error(f"Failed to initialize base bot: {e}")
            raise
        
        # Enhanced configuration with industry standards
        self.config.update({
            'extended_hours_enabled': True,
            'auto_recovery_enabled': True,
            'smart_alerts_enabled': True,
            'max_consecutive_errors': 10,
            'health_check_interval': 300,  # 5 minutes
            'state_save_interval': 60,  # 1 minute
            'symbol_analysis_cache_duration': 300,  # 5 minutes
            'max_daily_api_calls': 1000,
            'fallback_mode_enabled': True,
            'performance_monitoring_enabled': True
        })
        
        # Performance tracking
        self.performance_metrics = {
            'api_calls_today': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'last_reset_date': datetime.now().date(),
            'symbol_analysis_cache': {},
            'last_symbol_refresh': datetime.now()
        }
        
        # State management
        self.state = self._load_state()
        self.last_health_check = datetime.now()
        self.consecutive_errors = 0
        self.shutdown_requested = False
        self.fallback_mode = False
        
        # Dashboard data
        self.dashboard_data = {}
        
        # Initialize enhanced components with fallbacks
        self._initialize_data_providers()
        self._initialize_monitoring_systems()
        self._initialize_recovery_systems()
        
        self.logger.info("Industry-Grade Autonomous Trading Bot v4.0 initialized")

    def _initialize_data_providers(self):
        """Initialize data providers with robust fallback handling"""
        # Initialize fundamental data provider
        try:
            if os.getenv('ALPHA_VANTAGE_KEY'):
                self.fundamental_data = FundamentalDataProvider(os.getenv('ALPHA_VANTAGE_KEY'))
                self.logger.info("Fundamental data provider initialized")
            else:
                self.fundamental_data = None
                self.logger.warning("Alpha Vantage key not found - using fallback methods")
        except Exception as e:
            self.logger.error(f"Fundamental data provider failed: {e}")
            self.fundamental_data = None
            
        # Initialize economic calendar
        try:
            if os.getenv('FRED_API_KEY'):
                self.economic_calendar = EconomicCalendar(os.getenv('FRED_API_KEY'))
                self.logger.info("Economic calendar initialized")
            else:
                self.economic_calendar = None
                self.logger.warning("FRED API key not found - using basic calendar")
        except Exception as e:
            self.logger.error(f"Economic calendar failed: {e}")
            self.economic_calendar = None
            
        # Initialize news sentiment analyzer
        try:
            if os.getenv('NEWS_API_KEY'):
                self.news_analyzer = NewsSentimentAnalyzer(os.getenv('NEWS_API_KEY'))
                self.logger.info("News sentiment analyzer initialized")
            else:
                self.news_analyzer = None
                self.logger.warning("News API key not found - sentiment analysis disabled")
        except Exception as e:
            self.logger.error(f"News analyzer failed: {e}")
            self.news_analyzer = None
            
        # Initialize market events manager
        try:
            self.event_manager = MarketEventManager(self)
            self.logger.info("Market events manager initialized")
        except Exception as e:
            self.logger.error(f"Event manager failed: {e}")
            self.event_manager = None

    def _initialize_monitoring_systems(self):
        """Initialize monitoring and alerting systems"""
        try:
            notification_config = NotificationConfig().config
            self.alert_system = SmartAlertSystem(notification_config)
            self.digest_generator = DailyDigestGenerator(self)
            self.dashboard = AutomatedDashboard(self)
            self.logger.info("Monitoring systems initialized")
        except Exception as e:
            self.logger.error(f"Monitoring systems failed: {e}")
            self.alert_system = None
            self.digest_generator = None
            self.dashboard = None

    def _initialize_recovery_systems(self):
        """Initialize error recovery and health monitoring"""
        try:
            self.error_recovery = ErrorRecoverySystem(self)
            self.health_monitor = HealthMonitor(self)
            self.auto_recovery = AutoRecoveryManager(self)
            self.logger.info("Recovery systems initialized")
        except Exception as e:
            self.logger.error(f"Recovery systems failed: {e}")
            self.error_recovery = None
            self.health_monitor = None
            self.auto_recovery = None

    def _load_state(self) -> Dict:
        """Load saved state from disk with enhanced error handling"""
        state_file = 'bot_state.json'
        default_state = {
            'last_run': None,
            'total_trades': 0,
            'total_pnl': 0.0,
            'uptime_hours': 0,
            'last_positions': {},
            'performance_stats': {
                'best_day': 0.0,
                'worst_day': 0.0,
                'consecutive_winning_days': 0,
                'consecutive_losing_days': 0
            }
        }
        
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    loaded_state = json.load(f)
                    # Merge with defaults to handle missing keys
                    for key, value in default_state.items():
                        if key not in loaded_state:
                            loaded_state[key] = value
                    return loaded_state
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
                
        return default_state

    def _save_state(self):
        """Save current state to disk with backup"""
        try:
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
            
            # Save with atomic write
            temp_file = 'bot_state.json.tmp'
            with open(temp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            # Atomic move
            if os.path.exists('bot_state.json'):
                os.replace('bot_state.json', 'bot_state.json.backup')
            os.replace(temp_file, 'bot_state.json')
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _pre_trade_risk_check(self, symbol: str, signal: str) -> bool:
        """
        Comprehensive pre-trade risk check - FIXES THE MISSING METHOD ERROR
        """
        try:
            # Check daily loss limit
            if self.daily_pnl < -self.max_daily_loss * self.initial_equity:
                self.logger.warning(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
                return False
                
            # Check maximum positions
            if len(self.positions) >= self.config['MAX_POSITIONS']:
                self.logger.warning("Maximum positions reached")
                return False
                
            # Check if we already have position in this symbol
            if symbol in self.positions:
                self.logger.debug(f"Already have position in {symbol}")
                return False
                
            # Check account status
            try:
                account_info = self.get_account_info()
                if account_info['buying_power'] < 1000:  # Min $1000 buying power
                    self.logger.warning("Insufficient buying power")
                    return False
            except Exception as e:
                self.logger.error(f"Failed to check account info: {e}")
                return False
                
            # Check market conditions
            if self.fallback_mode:
                self.logger.info("Operating in fallback mode - reduced trading")
                return len(self.positions) < 1  # Only allow 1 position in fallback
                
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-trade risk check failed: {e}")
            return False

    def _reset_daily_counters(self):
        """Reset daily performance counters"""
        today = datetime.now().date()
        if self.performance_metrics['last_reset_date'] != today:
            self.performance_metrics['api_calls_today'] = 0
            self.performance_metrics['last_reset_date'] = today
            self.daily_pnl = 0.0
            self.logger.info("Daily counters reset for new trading day")

    def _should_refresh_symbol_cache(self) -> bool:
        """Check if symbol analysis cache should be refreshed"""
        cache_duration = self.config['symbol_analysis_cache_duration']
        time_since_refresh = (datetime.now() - self.performance_metrics['last_symbol_refresh']).total_seconds()
        return time_since_refresh > cache_duration

    def _get_cached_symbols(self) -> List[str]:
        """Get symbols from cache or refresh if needed"""
        if self._should_refresh_symbol_cache():
            symbols = self._select_symbols()
            self.performance_metrics['symbol_analysis_cache'] = {
                'symbols': symbols,
                'timestamp': datetime.now()
            }
            self.performance_metrics['last_symbol_refresh'] = datetime.now()
            self.logger.info(f"Symbol cache refreshed with {len(symbols)} symbols")
            return symbols
        else:
            cached_symbols = self.performance_metrics['symbol_analysis_cache'].get('symbols', [])
            if cached_symbols:
                self.logger.debug(f"Using cached symbols: {len(cached_symbols)}")
                return cached_symbols
            else:
                return self._select_symbols()

    def _determine_execution_strategy(self, symbol: str, quote_data: pd.DataFrame) -> str:
        """Determine optimal execution strategy"""
        try:
            spread_pct = (quote_data['ask'].iloc[0] - quote_data['bid'].iloc[0]) / quote_data['ask'].iloc[0]
            
            # Use market orders for tight spreads, limit orders for wide spreads
            if spread_pct < 0.005:  # 0.5% spread
                return 'market'
            else:
                return 'limit'
                
        except Exception as e:
            self.logger.debug(f"Execution strategy determination failed: {e}")
            return 'limit'  # Default to safer limit orders

    def _calculate_smart_limit_price(self, symbol: str, quote_data: pd.DataFrame, signal: str) -> float:
        """Calculate intelligent limit price"""
        try:
            if signal == 'buy':
                # Buy at slightly above bid but below ask
                bid = quote_data['bid'].iloc[0]
                ask = quote_data['ask'].iloc[0]
                return bid + (ask - bid) * 0.3  # 30% through spread
            else:
                # Sell at slightly below ask but above bid
                bid = quote_data['bid'].iloc[0]
                ask = quote_data['ask'].iloc[0]
                return ask - (ask - bid) * 0.3  # 30% through spread
                
        except Exception as e:
            self.logger.debug(f"Smart limit price calculation failed: {e}")
            # Fallback to mid-price
            return (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2

    def _calculate_adaptive_take_profit(self, symbol: str, entry_price: float, signal: str) -> float:
        """Calculate adaptive take profit based on volatility"""
        try:
            data = self._get_historical_data(symbol, days=20)
            if not data.empty:
                atr = self._calculate_atr(data).iloc[-1]
                atr_multiplier = 3.0  # 3x ATR for take profit
                
                if signal == 'buy':
                    return entry_price + (atr * atr_multiplier)
                else:
                    return entry_price - (atr * atr_multiplier)
            else:
                # Fallback to percentage-based
                multiplier = 1.02 if signal == 'buy' else 0.98
                return entry_price * multiplier
                
        except Exception as e:
            self.logger.debug(f"Adaptive take profit calculation failed: {e}")
            multiplier = 1.02 if signal == 'buy' else 0.98
            return entry_price * multiplier

    async def _generate_enhanced_signal(self, symbol: str) -> Optional[str]:
        """Enhanced signal generation with fallback support"""
        try:
            # Increment API call counter
            self.performance_metrics['api_calls_today'] += 1
            
            # Check API rate limits
            if self.performance_metrics['api_calls_today'] > self.config['max_daily_api_calls']:
                self.logger.warning("Daily API limit reached, entering fallback mode")
                self.fallback_mode = True
                
            # Get base technical signals
            trend_signal = self.trend_following_strategy(symbol)
            mean_rev_signal = self.mean_reversion_strategy(symbol)
            
            # ML signal if enabled and not in fallback mode
            ml_signal = None
            if self.config.get('USE_ML_SIGNALS', False) and not self.fallback_mode:
                try:
                    ml_signal = self.ml_enhanced_signal(symbol)
                except Exception as e:
                    self.logger.debug(f"ML signal failed for {symbol}: {e}")
                    
            # Log signals for debugging
            signals_info = {
                'trend': trend_signal,
                'mean_reversion': mean_rev_signal, 
                'ml': ml_signal,
                'fallback_mode': self.fallback_mode
            }
            self.logger.debug(f"Signals for {symbol}: {signals_info}")
            
            # Enhanced signal combination logic
            if self.config['STRATEGY'] == 'combined':
                signals = [s for s in [trend_signal, mean_rev_signal, ml_signal] if s is not None]
                
                if not signals:
                    return None
                    
                # In fallback mode, require stronger consensus
                required_consensus = 2 if not self.fallback_mode else len(signals)
                
                buy_count = signals.count('buy')
                sell_count = signals.count('sell')
                
                if buy_count >= required_consensus:
                    base_signal = 'buy'
                elif sell_count >= required_consensus:
                    base_signal = 'sell'
                else:
                    self.logger.debug(f"Insufficient consensus for {symbol}: {signals_info}")
                    return None
            else:
                base_signal = trend_signal or mean_rev_signal
                
            if not base_signal:
                return None
                
            # Event-driven risk assessment with fallback
            if self.event_manager and not self.fallback_mode:
                try:
                    should_enter, size_multiplier, reason = self.event_manager.should_enter_position(symbol, base_signal)
                    
                    if not should_enter:
                        self.logger.info(f"Trade blocked for {symbol}: {reason}")
                        return None
                        
                    # Store the size multiplier for position sizing
                    self._event_risk_adjustments = getattr(self, '_event_risk_adjustments', {})
                    self._event_risk_adjustments[symbol] = size_multiplier
                    
                    if size_multiplier < 1.0:
                        self.logger.info(f"Position size adjusted for {symbol}: {size_multiplier:.2f} - {reason}")
                except Exception as e:
                    self.logger.debug(f"Event manager check failed: {e}")
            
            return base_signal
            
        except Exception as e:
            self.logger.error(f"Enhanced signal generation failed for {symbol}: {e}")
            return None

    async def _execute_enhanced_trade(self, symbol: str, signal: str):
        """Execute trade with enhanced error handling and fallbacks"""
        if not self.is_market_open():
            self.logger.warning("Market is closed, skipping trade execution")
            return
            
        # Enhanced pre-trade checks
        if not self._pre_trade_risk_check(symbol, signal):
            return
            
        try:
            # Get order book data with retry
            max_retries = 3
            quote_data = None
            
            for attempt in range(max_retries):
                quote_data = self.get_real_time_data(symbol)
                if not quote_data.empty:
                    break
                else:
                    self.logger.warning(f"Quote data attempt {attempt + 1} failed for {symbol}")
                    await asyncio.sleep(1)
                    
            if quote_data.empty:
                self.logger.error(f"Failed to get quote data for {symbol}")
                return
                
            # Smart order routing
            execution_strategy = self._determine_execution_strategy(symbol, quote_data)
            
            # Calculate position size with event adjustments
            base_price = quote_data['ask'].iloc[0] if signal == 'buy' else quote_data['bid'].iloc[0]
            position_size = self.calculate_position_size(symbol, base_price)
            
            if position_size <= 0:
                self.logger.warning(f"Position size calculation returned {position_size} for {symbol}")
                return
                
            # Create order based on execution strategy
            if execution_strategy == 'market':
                from alpaca.trading.requests import MarketOrderRequest
                from alpaca.trading.enums import OrderSide, TimeInForce
                
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=position_size,
                    side=OrderSide.BUY if signal == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.IOC  # Immediate or Cancel
                )
                entry_price = base_price
            else:
                from alpaca.trading.requests import LimitOrderRequest
                from alpaca.trading.enums import OrderSide, TimeInForce
                
                limit_price = self._calculate_smart_limit_price(symbol, quote_data, signal)
                order = LimitOrderRequest(
                    symbol=symbol,
                    qty=position_size,
                    side=OrderSide.BUY if signal == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )
                entry_price = limit_price
                
            # Submit order with error handling
            try:
                submitted_order = self.trade_client.submit_order(order)
                self.performance_metrics['successful_trades'] += 1
            except Exception as order_error:
                self.logger.error(f"Order submission failed for {symbol}: {order_error}")
                self.performance_metrics['failed_trades'] += 1
                return
                
            # Enhanced position tracking
            from algo_trading_bot_v5 import Position
            
            position = Position(
                symbol=symbol,
                entry_price=entry_price,
                quantity=position_size,
                order_id=submitted_order.id,
                timestamp=datetime.now(),
                strategy=f"{self.config['STRATEGY']}_enhanced",
                stop_loss=self._calculate_adaptive_stop_loss(symbol, entry_price, signal),
                take_profit=self._calculate_adaptive_take_profit(symbol, entry_price, signal)
            )
            
            self.positions[symbol] = position
            
            # Log successful trade
            trade_logger = logging.getLogger('AlgoTradingBot.trades')
            trade_logger.info(f"ENHANCED_TRADE,{symbol},{signal},{position_size},{entry_price:.2f},{execution_strategy}")
            
            self.logger.info(f"Trade executed: {signal} {position_size} shares of {symbol} at ${entry_price:.2f}")
            
        except Exception as e:
            self.logger.error(f"Enhanced trade execution failed for {symbol}: {e}")
            self.performance_metrics['failed_trades'] += 1

    async def _handle_regular_trading(self):
        """Handle regular market hours trading with optimization"""
        symbols = self._get_cached_symbols()  # Use cached symbols
        
        # Add ML-enhanced filtering if not in fallback mode
        if self.config.get('USE_ML_SIGNALS', False) and not self.fallback_mode:
            try:
                symbols = await self._filter_symbols_ml(symbols)
            except Exception as e:
                self.logger.debug(f"ML filtering failed: {e}")
                
        for symbol in symbols:
            if symbol in self.positions:
                continue
                
            try:
                signal = await self._generate_enhanced_signal(symbol)
                if signal:
                    await self._execute_enhanced_trade(symbol, signal)
                    
                    # Rate limiting to prevent overwhelming APIs
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Trading error for {symbol}: {e}")

    async def _monitor_positions_enhanced(self):
        """Enhanced position monitoring with better error handling"""
        if not self.positions:
            return
            
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                
                # Check order status first
                try:
                    order = self.trade_client.get_order_by_id(position.order_id)
                    from alpaca.trading.enums import OrderStatus
                    
                    if order.status not in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                        # Cancel unfilled orders after timeout
                        age = datetime.now() - position.timestamp
                        if age > timedelta(minutes=10):  # Increased timeout
                            try:
                                self.trade_client.cancel_order_by_id(position.order_id)
                                del self.positions[symbol]
                                self.logger.info(f"Cancelled unfilled order for {symbol}")
                            except Exception as cancel_error:
                                self.logger.error(f"Failed to cancel order for {symbol}: {cancel_error}")
                        continue
                except Exception as order_check_error:
                    self.logger.debug(f"Order status check failed for {symbol}: {order_check_error}")
                    
                # Get current price with retry
                quote_data = None
                for attempt in range(3):
                    quote_data = self.get_real_time_data(symbol)
                    if not quote_data.empty:
                        break
                    await asyncio.sleep(0.5)
                    
                if quote_data.empty:
                    self.logger.warning(f"Failed to get current price for {symbol}")
                    continue
                    
                current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                
                # Calculate P&L and metrics
                pnl = (current_price - position.entry_price) * position.quantity
                pnl_pct = (current_price / position.entry_price - 1) * 100
                hold_time = datetime.now() - position.timestamp
                
                # Trailing stop logic
                if pnl_pct > 5:  # If profit > 5%, implement trailing stop
                    new_stop = current_price * 0.98  # 2% trailing stop
                    if new_stop > position.stop_loss:
                        position.stop_loss = new_stop
                        self.logger.info(f"Updated trailing stop for {symbol}: ${new_stop:.2f}")
                
                # Enhanced exit conditions
                should_exit = False
                exit_reason = ""
                
                # Standard exit conditions
                if current_price <= position.stop_loss:
                    should_exit = True
                    exit_reason = "Stop loss hit"
                elif current_price >= position.take_profit:
                    should_exit = True
                    exit_reason = "Take profit hit"
                elif hold_time > timedelta(hours=24):
                    should_exit = True
                    exit_reason = "Max hold time reached"
                    
                # Event-driven exit check
                if self.event_manager and not should_exit:
                    try:
                        event_exit, event_reason = self.event_manager.should_exit_position(symbol, pnl)
                        if event_exit:
                            should_exit = True
                            exit_reason = f"Event-driven exit: {event_reason}"
                    except Exception as e:
                        self.logger.debug(f"Event exit check failed: {e}")
                
                if should_exit:
                    await self._exit_position_enhanced(symbol, current_price, exit_reason)
                else:
                    # Update position metrics for dashboard
                    self._update_position_metrics(symbol, {
                        'current_price': current_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'hold_time': hold_time.total_seconds() / 3600
                    })
                    
            except Exception as e:
                self.logger.error(f"Enhanced position monitoring error for {symbol}: {e}")

    async def _exit_position_enhanced(self, symbol: str, current_price: float, reason: str):
        """Enhanced position exit with better tracking"""
        try:
            position = self.positions[symbol]
            
            # Create market order to exit
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            order = MarketOrderRequest(
                symbol=symbol,
                qty=position.quantity,
                side=OrderSide.SELL if position.quantity > 0 else OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            try:
                exit_order = self.trade_client.submit_order(order)
            except Exception as order_error:
                self.logger.error(f"Exit order failed for {symbol}: {order_error}")
                return
                
            # Calculate P&L
            pnl = (current_price - position.entry_price) * position.quantity
            
            # Create trade record
            from algo_trading_bot_v5 import Trade
            
            trade = Trade(
                symbol=symbol,
                entry_price=position.entry_price,
                exit_price=current_price,
                quantity=position.quantity,
                entry_time=position.timestamp,
                exit_time=datetime.now(),
                pnl=pnl,
                strategy=position.strategy
            )
            
            # Update metrics
            self.metrics.add_trade(trade)
            self.daily_pnl += pnl
            
            # Remove position
            del self.positions[symbol]
            
            # Log exit
            trade_logger = logging.getLogger('AlgoTradingBot.trades')
            trade_logger.info(f"TRADE_CLOSED,{symbol},{current_price:.2f},{pnl:.2f},{reason}")
            
            self.logger.info(f"Exited position for {symbol} at ${current_price:.2f} - P&L: ${pnl:.2f} ({reason})")
            
            # Send alert for significant P&L
            if abs(pnl) > 500:  # Alert for P&L > $500
                await self._send_alert(f"Significant trade exit: {symbol} ${pnl:.2f} - {reason}")
                
        except Exception as e:
            self.logger.error(f"Enhanced exit failed for {symbol}: {e}")

    def _update_position_metrics(self, symbol: str, metrics: Dict):
        """Update position metrics for dashboard"""
        if symbol not in self.dashboard_data:
            self.dashboard_data[symbol] = {}
        self.dashboard_data[symbol].update(metrics)

    async def _send_alert(self, message: str, severity: str = 'warning'):
        """Enhanced alert sending"""
        try:
            self.logger.warning(f"ALERT: {message}")
            
            if self.alert_system:
                alert_metrics = {
                    'custom_alert': True,
                    'alert_message': message,
                    'severity': severity,
                    'events': ['custom_alert']
                }
                await self.alert_system.evaluate_alerts(alert_metrics)
            else:
                print(f"🚨 {severity.upper()}: {message}")
                
        except Exception as e:
            self.logger.error(f"Alert sending failed: {e}")
            print(f"🚨 {severity.upper()}: {message}")

    async def _perform_health_check(self):
        """Enhanced system health check"""
        try:
            if self.health_monitor:
                health_results = await self.health_monitor.run_health_checks()
                
                # Check for critical failures
                critical_failures = [name for name, result in health_results.items() if not result]
                
                if critical_failures:
                    self.logger.warning(f"Health check failures: {critical_failures}")
                    
                    # Enable fallback mode if multiple failures
                    if len(critical_failures) >= 2:
                        self.fallback_mode = True
                        self.logger.warning("Entering fallback mode due to health failures")
                        await self._send_alert("System health degraded - entering fallback mode", severity='critical')
                else:
                    # Reset fallback mode if health is good
                    if self.fallback_mode:
                        self.fallback_mode = False
                        self.logger.info("Exiting fallback mode - system health restored")
                        
                self.last_health_check = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")

    async def _perform_maintenance(self):
        """Enhanced maintenance with better error handling"""
        self.logger.info("Performing maintenance tasks")
        
        try:
            # Auto-recovery scan
            if self.auto_recovery:
                await self.auto_recovery.perform_recovery_scan()
                
            # Generate daily digest
            if datetime.now().hour == 18 and self.digest_generator:  # 6 PM
                try:
                    digest = await self.digest_generator.generate_daily_digest()
                    await self._send_daily_digest(digest)
                except Exception as e:
                    self.logger.error(f"Daily digest generation failed: {e}")
                    
            # Cleanup tasks
            self._cleanup_old_logs()
            self._optimize_storage()
            
            # Reset performance counters
            self._reset_daily_counters()
            
            # Update ML models if needed
            if self.config.get('USE_ML_SIGNALS', False) and not self.fallback_mode:
                await self._update_ml_models()
                
            # Backup critical data
            self._backup_critical_data()
            
        except Exception as e:
            self.logger.error(f"Maintenance error: {e}")

    def _update_monitoring_dashboard(self):
        """Update monitoring dashboard with fallback handling"""
        try:
            if self.dashboard:
                html_content = self.dashboard.generate_dashboard_html()
                with open('dashboard.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            # Always update JSON dashboard as fallback
            self._update_dashboard()
            
            self.logger.debug("Dashboard updated successfully")
            
        except Exception as e:
            self.logger.error(f"Dashboard update failed: {e}")
            # Fallback to basic JSON dashboard
            try:
                self._update_dashboard()
            except Exception as fallback_error:
                self.logger.error(f"Fallback dashboard also failed: {fallback_error}")

    def _update_dashboard(self):
        """Update basic JSON dashboard"""
        try:
            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'status': 'fallback' if self.fallback_mode else 'running',
                'market_open': self.is_market_open(),
                'daily_pnl': self.daily_pnl,
                'positions': len(self.positions),
                'total_trades': len(self.metrics.trades),
                'win_rate': self.metrics.calculate_win_rate(),
                'performance_metrics': self.performance_metrics,
                'consecutive_errors': self.consecutive_errors,
                'position_details': self.dashboard_data
            }
            
            # Safely get equity
            try:
                account_info = self.get_account_info()
                dashboard['equity'] = account_info['equity']
            except Exception as e:
                dashboard['equity'] = 0
                dashboard['account_error'] = str(e)
            
            with open('dashboard.json', 'w') as f:
                json.dump(dashboard, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Basic dashboard update failed: {e}")

    async def _evaluate_alerts(self):
        """Evaluate alerts with enhanced error handling"""
        if not self.alert_system:
            return
            
        try:
            # Safely collect metrics
            try:
                account_info = self.get_account_info()
                equity = account_info['equity']
            except Exception:
                equity = 0
                
            current_metrics = {
                'timestamp': datetime.now().isoformat(),
                'daily_pnl': self.daily_pnl,
                'equity': equity,
                'positions_count': len(self.positions),
                'win_rate': self.metrics.calculate_win_rate(),
                'health_score': 0.85 if not self.fallback_mode else 0.5,
                'active_symbols': list(self.positions.keys()),
                'consecutive_errors': self.consecutive_errors,
                'fallback_mode': self.fallback_mode,
                'api_calls_today': self.performance_metrics['api_calls_today']
            }
            
            await self.alert_system.evaluate_alerts(current_metrics, bot_instance=self)
            
        except Exception as e:
            self.logger.error(f"Alert evaluation failed: {e}")

    async def _generate_daily_digest(self):
        """Generate daily digest with error handling"""
        if not self.digest_generator:
            return
            
        try:
            digest = await self.digest_generator.generate_daily_digest()
            
            # Save to file
            digest_filename = f'daily_digest_{datetime.now().strftime("%Y%m%d")}.json'
            with open(digest_filename, 'w') as f:
                json.dump(digest, f, indent=2, default=str)
                
            self.logger.info(f"Daily digest generated: {digest_filename}")
            
            # Send digest summary
            if digest:
                digest_summary = f"""
Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}
Daily P&L: ${digest.get('performance', {}).get('daily_pnl', 0):.2f}
Total Trades: {digest.get('performance', {}).get('trades_count', 0)}
Win Rate: {digest.get('performance', {}).get('win_rate', 0):.1f}%
Status: {'Fallback Mode' if self.fallback_mode else 'Normal Operation'}
"""
                await self._send_alert(digest_summary, severity='info')

            return digest
            
        except Exception as e:
            self.logger.error(f"Daily digest generation failed: {e}")

    async def _send_daily_digest(self, digest: Dict):
        """Send daily digest"""
        try:
            self.logger.info("Daily digest prepared")
            # Additional processing could be added here
        except Exception as e:
            self.logger.error(f"Daily digest sending failed: {e}")

    def _cleanup_old_logs(self):
        """Cleanup old log files"""
        try:
            logs_dir = 'logs'
            if os.path.exists(logs_dir):
                cutoff = datetime.now() - timedelta(days=30)
                cleaned_count = 0
                for file in os.listdir(logs_dir):
                    file_path = os.path.join(logs_dir, file)
                    if os.path.isfile(file_path) and os.path.getctime(file_path) < cutoff.timestamp():
                        os.remove(file_path)
                        cleaned_count += 1
                        
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} old log files")
                        
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")

    def _optimize_storage(self):
        """Optimize storage usage"""
        try:
            # Compress old JSON files
            import gzip
            import glob
            
            json_files = glob.glob('daily_digest_*.json')
            compressed_count = 0
            
            for json_file in json_files:
                # Compress files older than 7 days
                file_date = os.path.getctime(json_file)
                if (time.time() - file_date) > (7 * 24 * 3600):
                    gz_file = json_file + '.gz'
                    if not os.path.exists(gz_file):
                        with open(json_file, 'rb') as f_in:
                            with gzip.open(gz_file, 'wb') as f_out:
                                f_out.write(f_in.read())
                        os.remove(json_file)
                        compressed_count += 1
                        
            if compressed_count > 0:
                self.logger.info(f"Compressed {compressed_count} old digest files")
                
        except Exception as e:
            self.logger.error(f"Storage optimization failed: {e}")

    async def _update_ml_models(self):
        """Update ML models with new data"""
        try:
            if not self.config.get('USE_ML_SIGNALS', False):
                return
                
            self.logger.info("ML model update scheduled")
            # Placeholder for ML model updates
            # In production, this would retrain models with recent data
            
        except Exception as e:
            self.logger.error(f"ML model update failed: {e}")

    def _backup_critical_data(self):
        """Backup critical data"""
        try:
            self._save_state()
            
            # Create compressed backup of critical files
            import shutil
            backup_files = ['bot_state.json', 'dashboard.json']
            backup_dir = f'backups/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.makedirs(backup_dir, exist_ok=True)
            
            for file in backup_files:
                if os.path.exists(file):
                    shutil.copy2(file, backup_dir)
                    
            self.logger.debug("Critical data backup complete")
            
        except Exception as e:
            self.logger.error(f"Data backup failed: {e}")

    def get_current_session(self) -> str:
        """Determine current market session"""
        now = datetime.now()
        hour = now.hour
        
        # Enhanced session detection with timezone awareness
        try:
            import pytz
            eastern = pytz.timezone('US/Eastern')
            et_time = datetime.now(eastern)
            hour = et_time.hour
        except ImportError:
            pass  # Use local time as fallback
        
        if 4 <= hour < 9:
            return 'pre_market'
        elif 9 <= hour < 16:
            return 'regular'
        elif 16 <= hour < 20:
            return 'after_hours'
        else:
            return 'closed'

    async def _handle_pre_market_trading(self):
        """Enhanced pre-market trading"""
        self.logger.debug("Pre-market session - enhanced trading")
        
        # Only trade most liquid symbols in pre-market
        liquid_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA']
        
        for symbol in liquid_symbols:
            if symbol in self.positions:
                continue
                
            try:
                # Enhanced pre-market risk assessment
                pre_market_adjustment = 0.3  # Default 30% reduction
                
                if self.event_manager and not self.fallback_mode:
                    pre_market_adjustment = self.event_manager.get_pre_market_risk_adjustment(symbol)
                    
                if pre_market_adjustment == 0.0:
                    self.logger.debug(f"Pre-market trading blocked for {symbol}")
                    continue
                    
                # Generate signal
                signal = await self._generate_enhanced_signal(symbol)
                if signal:
                    # Apply pre-market risk reduction
                    original_risk = self.config['RISK_PCT']
                    self.config['RISK_PCT'] = original_risk * pre_market_adjustment
                    
                    await self._execute_enhanced_trade(symbol, signal)
                    
                    # Restore original risk
                    self.config['RISK_PCT'] = original_risk
                    
                # Rate limiting
                await asyncio.sleep(0.5)
                    
            except Exception as e:
                self.logger.error(f"Pre-market trading error for {symbol}: {e}")

    async def _handle_after_hours_trading(self):
        """Handle after-hours trading (monitoring focus)"""
        self.logger.debug("After-hours session - monitoring mode")
        await self._monitor_positions_enhanced()

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        self.logger.info(f"Shutdown signal received: {signum}")
        self.shutdown_requested = True

    async def _shutdown_cleanup(self):
        """Enhanced cleanup on shutdown"""
        self.logger.info("Performing shutdown cleanup")
        
        try:
            # Close positions if requested
            if self.config.get('CLOSE_ON_SHUTDOWN', False):
                for symbol in list(self.positions.keys()):
                    try:
                        quote_data = self.get_real_time_data(symbol)
                        if not quote_data.empty:
                            current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                            await self._exit_position_enhanced(symbol, current_price, "Shutdown")
                    except Exception as e:
                        self.logger.error(f"Failed to close position {symbol}: {e}")
                        
            # Save final state
            self._save_state()
            
            # Generate final performance report
            try:
                final_report = self.generate_performance_report()
                if final_report:
                    self.logger.info(f"Final performance: ${final_report['performance']['daily_pnl']:.2f}")
            except Exception as e:
                self.logger.error(f"Final report generation failed: {e}")
            
            # Send shutdown notification
            await self._send_alert(
                f"Trading bot shutdown at {datetime.now()}. Final P&L: ${self.daily_pnl:.2f}",
                severity='info'
            )
            
        except Exception as e:
            self.logger.error(f"Shutdown cleanup error: {e}")

    async def run_autonomous(self):
        """Enhanced main autonomous trading loop"""
        self.logger.info("Starting Enhanced Autonomous Trading Bot v4.0")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        # Initialize components
        await self._initialize_autonomous_components()
        
        # Main loop with enhanced error handling
        loop_count = 0
        last_state_save = datetime.now()
        last_alert_check = datetime.now()
        last_digest_time = datetime.now()
        last_maintenance_time = datetime.now()
        
        while not self.shutdown_requested:
            try:
                loop_count += 1
                loop_start = datetime.now()
                
                # Reset daily counters if needed
                self._reset_daily_counters()
                
                # Health check
                if datetime.now() - self.last_health_check > timedelta(seconds=self.config['health_check_interval']):
                    await self._perform_health_check()
                    
                # Determine trading session
                session = self.get_current_session()
                
                if session == 'closed':
                    # Market closed - perform maintenance
                    if datetime.now() - last_maintenance_time > timedelta(hours=2):
                        await self._perform_maintenance()
                        last_maintenance_time = datetime.now()
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
                
                # Alert evaluation (every 5 minutes)
                if datetime.now() - last_alert_check > timedelta(minutes=5):
                    await self._evaluate_alerts()
                    last_alert_check = datetime.now()
                
                # Daily digest generation (once per day at 6 PM)
                current_hour = datetime.now().hour
                if (current_hour == 18 and 
                    datetime.now() - last_digest_time > timedelta(hours=23)):
                    await self._generate_daily_digest()
                    last_digest_time = datetime.now()

                # Save state periodically
                if datetime.now() - last_state_save > timedelta(seconds=self.config['state_save_interval']):
                    self._save_state()
                    last_state_save = datetime.now()
                    
                # Dashboard update (every 10 loops)
                if loop_count % 10 == 0:
                    self._update_monitoring_dashboard()
                    
                # Progress logging (every 100 loops)
                if loop_count % 100 == 0:
                    self._log_progress(loop_count)
                    
                # Calculate sleep time for consistent loop timing
                loop_duration = (datetime.now() - loop_start).total_seconds()
                sleep_time = max(0, 60 - loop_duration)  # Target 1 minute loops
                await asyncio.sleep(sleep_time)
                
                # Reset error counter on successful loop
                self.consecutive_errors = 0
                
            except Exception as e:
                self.consecutive_errors += 1
                self.logger.error(f"Error in main loop #{loop_count}: {e}", exc_info=True)
                
                # Enhanced error handling
                if self.consecutive_errors >= 3:
                    self.fallback_mode = True
                    self.logger.warning("Entering fallback mode due to consecutive errors")
                
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
                
                # Check for critical failure threshold
                if self.consecutive_errors >= self.config['max_consecutive_errors']:
                    self.logger.critical("Maximum consecutive errors reached - initiating emergency shutdown")
                    await self._handle_critical_failure()
                    break
                    
                # Exponential backoff with cap
                backoff_time = min(300, 30 * (2 ** min(self.consecutive_errors, 4)))
                await asyncio.sleep(backoff_time)
                
        # Cleanup
        await self._shutdown_cleanup()
        self.logger.info("Enhanced Autonomous Trading Bot shutdown complete")

    async def _handle_critical_failure(self):
        """Enhanced critical failure handling"""
        self.logger.critical("Critical failure detected - emergency procedures")
        
        try:
            # Emergency position closure
            emergency_closed = 0
            for symbol in list(self.positions.keys()):
                try:
                    quote_data = self.get_real_time_data(symbol)
                    if not quote_data.empty:
                        current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                        await self._exit_position_enhanced(symbol, current_price, "Emergency closure")
                        emergency_closed += 1
                except Exception as e:
                    self.logger.error(f"Emergency closure failed for {symbol}: {e}")
                    
            # Send critical alert
            await self._send_alert(
                f"EMERGENCY: Critical failure - {emergency_closed} positions closed, system shutting down",
                severity='critical'
            )
            
            # Save emergency state
            self._backup_critical_data()
            
        except Exception as e:
            self.logger.error(f"Critical failure handling error: {e}")

    async def _initialize_autonomous_components(self):
        """Initialize autonomous components with better error handling"""
        try:
            # Setup infrastructure
            if not os.path.exists('bot_initialized'):
                os.makedirs('logs', exist_ok=True)
                os.makedirs('data', exist_ok=True)
                os.makedirs('backups', exist_ok=True)
                with open('bot_initialized', 'w') as f:
                    f.write(datetime.now().isoformat())
                    
            # Preload data if not in fallback mode
            if not self.fallback_mode:
                await self._preload_historical_data()
            
            # Start dashboard server
            await self._start_dashboard_server()
            
            self.logger.info("Enhanced autonomous components initialized")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            self.fallback_mode = True
            self.logger.warning("Starting in fallback mode due to initialization errors")

    async def _preload_historical_data(self):
        """Preload historical data for faster analysis"""
        try:
            self.logger.info("Preloading historical data...")
            symbols = self._select_symbols()[:5]  # Limit to top 5 for efficiency
            
            preloaded_count = 0
            for symbol in symbols:
                try:
                    data = self._get_historical_data(symbol, days=50)
                    if not data.empty:
                        preloaded_count += 1
                        self.logger.debug(f"Cached {len(data)} bars for {symbol}")
                except Exception as e:
                    self.logger.debug(f"Failed to cache data for {symbol}: {e}")
                    
            self.logger.info(f"Historical data preloading complete: {preloaded_count} symbols cached")
            
        except Exception as e:
            self.logger.error(f"Failed to preload historical data: {e}")

    async def _start_dashboard_server(self):
        """Start dashboard server (enhanced placeholder)"""
        try:
            self.logger.info("Dashboard system initialized")
            self._update_monitoring_dashboard()
            
        except Exception as e:
            self.logger.error(f"Dashboard initialization failed: {e}")

    def _log_progress(self, loop_count: int):
        """Enhanced progress logging"""
        try:
            status_info = {
                'loop': loop_count,
                'daily_pnl': self.daily_pnl,
                'positions': len(self.positions),
                'trades': len(self.metrics.trades),
                'mode': 'fallback' if self.fallback_mode else 'normal',
                'errors': self.consecutive_errors
            }
            
            try:
                account_info = self.get_account_info()
                status_info['equity'] = account_info['equity']
            except Exception:
                status_info['equity'] = 'unavailable'
            
            self.logger.info(
                f"Progress #{loop_count} - Mode: {status_info['mode']}, "
                f"Equity: ${status_info['equity']}, Daily P&L: ${self.daily_pnl:.2f}, "
                f"Positions: {len(self.positions)}, Trades: {len(self.metrics.trades)}, "
                f"Errors: {self.consecutive_errors}"
            )
            
        except Exception as e:
            self.logger.error(f"Progress logging failed: {e}")

    async def _filter_symbols_ml(self, symbols: List[str]) -> List[str]:
        """Filter symbols using ML criteria (placeholder for now)"""
        try:
            filtered = []
            for symbol in symbols[:10]:  # Limit processing
                try:
                    data = self._get_historical_data(symbol, days=20)
                    if not data.empty and len(data) >= 10:
                        # Simple momentum and volatility filter
                        momentum = (data['close'].iloc[-1] / data['close'].iloc[-10] - 1) * 100
                        volatility = data['close'].pct_change().std() * 100
                        
                        # Filter criteria
                        if abs(momentum) > 1 and volatility < 8:
                            filtered.append(symbol)
                            
                except Exception as e:
                    self.logger.debug(f"ML filter error for {symbol}: {e}")
                    
            return filtered[:3]  # Return top 3 in fallback mode, 5 in normal mode
            
        except Exception as e:
            self.logger.debug(f"ML filtering failed: {e}")
            return symbols[:3]  # Fallback to first 3 symbols


# Entry point with enhanced error handling
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
        'RISK_PCT': 0.015,  # Reduced to 1.5% for safety
        'MAX_POSITIONS': 3,
        'MAX_DAILY_LOSS': 0.02,
        
        # Strategy Configuration
        'STRATEGY': 'combined',
        'USE_ML_SIGNALS': True,
        'USE_ADAPTIVE_STOPS': True,
        
        # Enhanced Features
        'EXTENDED_HOURS_ENABLED': True,
        'PRE_MARKET_RISK_REDUCTION': 0.3,
        'AUTO_RECOVERY_ENABLED': True,
        'SMART_ALERTS_ENABLED': True,
        'CLOSE_ON_SHUTDOWN': False,
        
        # Performance & Monitoring
        'monitoring': {
            'alerts_enabled': True,
            'alert_check_interval': 300,
            'daily_digest_enabled': True,
            'dashboard_enabled': True
        },
        
        # Notification Settings
        'email_enabled': True,
        'sms_enabled': False,  # Enable if you have Twilio
        'telegram_enabled': False,
        'discord_enabled': False
    }
    
    # Validate environment
    required_vars = ['APCA_API_KEY_ID', 'APCA_API_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Optional API keys check
    optional_vars = ['ALPHA_VANTAGE_KEY', 'FRED_API_KEY', 'NEWS_API_KEY']
    available_apis = [var for var in optional_vars if os.getenv(var)]
    missing_apis = [var for var in optional_vars if not os.getenv(var)]
    
    print(f"✅ Available APIs: {available_apis}")
    if missing_apis:
        print(f"⚠️  Missing optional APIs: {missing_apis} (will use fallback methods)")
    
    # Create and run enhanced bot
    try:
        print("🚀 Starting Industry-Grade Autonomous Trading Bot...")
        bot = IndustryGradeAutonomousBot(config)
        asyncio.run(bot.run_autonomous())
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"💥 Critical startup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)