#!/usr/bin/env python3
"""
UNIFIED Industry-Grade Autonomous Trading Bot v5.0 - FIXED
Single file with all essential features - eliminates confusion
Run with: python unified_trading_bot.py
"""

import os
import sys
import asyncio
import signal as signal_module  # FIXED: Renamed to avoid conflict
import json
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Third-party imports with fallbacks
try:
    import pandas as pd
    import numpy as np
    from alpaca.trading.client import TradingClient
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
    from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from dotenv import load_dotenv
    
    load_dotenv()
    
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install with: pip install alpaca-py pandas numpy python-dotenv")
    sys.exit(1)

# Optional imports for enhanced features
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from error_recovery import CircuitBreaker, ErrorRecoverySystem
    from extended_hours import ExtendedHoursManager
    from monitoring import AdvancedMonitoring, AlertSystem
    from news_sentiment import SentimentAnalyzer
    from economic_calendar import EconomicEventManager
    from fundamental_data import FundamentalAnalyzer
    from market_events import MarketEventHandler
    ENHANCED_FEATURES = True
    print("✅ Enhanced features available")
except ImportError as e:
    ENHANCED_FEATURES = False
    print(f"⚠️ Enhanced features unavailable: {e}")

# Enhanced logging setup
def setup_logging():
    """Setup comprehensive logging"""
    os.makedirs('logs', exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('TradingBot')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler('logs/trading_bot.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def load_enhancements(self):
    """Load optional enhancement modules based on config"""
    if not ENHANCED_FEATURES:
        return
        
    # Load config files
    config_path = Path('config/config.json')
    if config_path.exists():
        with open(config_path) as f:
            enhanced_config = json.load(f)
    else:
        enhanced_config = {}
    
    features = enhanced_config.get('features', {})
    
    # Initialize based on configuration
    if features.get('circuit_breaker', True):
        self.circuit_breaker = CircuitBreaker()
        
    if features.get('extended_hours', False):
        self.extended_hours = ExtendedHoursManager()
        
    if features.get('sentiment_analysis', False):
        self.sentiment_analyzer = SentimentAnalyzer()
        
    if features.get('economic_events', True):
        self.event_manager = EconomicEventManager()
        
    self.logger.info("✅ Enhanced features loaded from config")

class Position:
    """Position tracking"""
    def __init__(self, symbol: str, entry_price: float, quantity: float, 
                 order_id: str, timestamp: datetime, strategy: str):
        self.symbol = symbol
        self.entry_price = entry_price
        self.quantity = quantity
        self.order_id = order_id
        self.timestamp = timestamp
        self.strategy = strategy
        self.stop_loss = entry_price * 0.97  # 3% stop loss
        self.take_profit = entry_price * 1.06  # 6% take profit
        self.unrealized_pnl = 0.0

class Trade:
    """Completed trade record"""
    def __init__(self, symbol: str, entry_price: float, exit_price: float, 
                 quantity: float, entry_time: datetime, exit_time: datetime, 
                 pnl: float, strategy: str):
        self.symbol = symbol
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.pnl = pnl
        self.strategy = strategy

class RobustDataProvider:
    """Ultra-robust data provider with multiple fallbacks"""
    
    def __init__(self, alpaca_data_client):
        self.data_client = alpaca_data_client
        self.logger = logging.getLogger('TradingBot.DataProvider')
        
        # Static fallback data (updated current prices)
        self.fallback_data = {
            'AAPL': 201.29, 'MSFT': 477.40, 'GOOGL': 167.0, 'AMZN': 201.0,
            'TSLA': 350.0, 'META': 565.0, 'NVDA': 135.0, 'JPM': 245.0,
            'SPY': 598.0, 'QQQ': 513.0, 'DIS': 115.0, 'V': 315.0
        }
    
    def get_quote_data(self, symbol: str) -> pd.DataFrame:
        """Get real-time quote with fallbacks"""
        # Try Alpaca first
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote_data = self.data_client.get_stock_latest_quote(request)
            
            if symbol in quote_data:
                quote = quote_data[symbol]
                return pd.DataFrame({
                    'timestamp': [quote.timestamp],
                    'bid': [float(quote.bid_price)],
                    'ask': [float(quote.ask_price)],
                    'bid_size': [int(quote.bid_size)],
                    'ask_size': [int(quote.ask_size)]
                })
        except Exception as e:
            self.logger.debug(f"Alpaca quote failed for {symbol}: {e}")
        
        # Try Yahoo Finance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                if hasattr(info, 'last_price') and info.last_price:
                    price = float(info.last_price)
                    spread = price * 0.001
                    return pd.DataFrame({
                        'timestamp': [datetime.now()],
                        'bid': [price - spread/2],
                        'ask': [price + spread/2],
                        'bid_size': [100],
                        'ask_size': [100]
                    })
            except Exception as e:
                self.logger.debug(f"Yahoo quote failed for {symbol}: {e}")
        
        # Fallback to static data
        if symbol in self.fallback_data:
            price = self.fallback_data[symbol]
            spread = price * 0.001
            self.logger.warning(f"Using fallback data for {symbol}: ${price}")
            return pd.DataFrame({
                'timestamp': [datetime.now()],
                'bid': [price - spread/2],
                'ask': [price + spread/2],
                'bid_size': [100],
                'ask_size': [100]
            })
        
        self.logger.error(f"All data sources failed for {symbol}")
        return pd.DataFrame()
    
    def get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical data with fallbacks"""
        # Try Alpaca first
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                start=start_date,
                end=end_date,
                timeframe=TimeFrame.Day
            )
            
            bars_response = self.data_client.get_stock_bars(request)
            if hasattr(bars_response, 'df') and bars_response.df is not None:
                df = bars_response.df.reset_index()
                if len(df) >= days * 0.7:  # At least 70% of requested days
                    return df.tail(days)
        except Exception as e:
            self.logger.debug(f"Alpaca historical failed for {symbol}: {e}")
        
        # Try Yahoo Finance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                if not hist.empty:
                    hist.reset_index(inplace=True)
                    hist.columns = [col.lower() for col in hist.columns]
                    return hist
            except Exception as e:
                self.logger.debug(f"Yahoo historical failed for {symbol}: {e}")
        
        # Generate synthetic data as last resort
        if symbol in self.fallback_data:
            self.logger.warning(f"Generating synthetic data for {symbol}")
            base_price = self.fallback_data[symbol]
            dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')
            
            # Simple random walk
            prices = [base_price]
            for _ in range(1, days):
                change = np.random.normal(0, 0.02)  # 2% daily volatility
                new_price = prices[-1] * (1 + change)
                prices.append(max(new_price, 1.0))
            
            data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                open_price = close * np.random.uniform(0.99, 1.01)
                high = max(open_price, close) * np.random.uniform(1.0, 1.02)
                low = min(open_price, close) * np.random.uniform(0.98, 1.0)
                volume = np.random.randint(500000, 5000000)
                
                data.append({
                    'date': date,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume
                })
            
            return pd.DataFrame(data)
        
        return pd.DataFrame()

class UnifiedTradingBot:
    """Industry-grade autonomous trading bot - all features unified"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = setup_logging()
        self.shutdown_requested = False
        self.consecutive_errors = 0
        
        # Validate configuration
        self._validate_config()
        
        # Initialize Alpaca clients
        try:
            self.trade_client = TradingClient(
                api_key=self.config['API_KEY'],
                secret_key=self.config['SECRET_KEY'],
                paper=self.config.get('PAPER_TRADING', True)
            )
            self.data_client = StockHistoricalDataClient(
                self.config['API_KEY'],
                self.config['SECRET_KEY']
            )
            self.logger.info("✅ Connected to Alpaca API")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Alpaca: {e}")
            raise
        
        # Initialize data provider
        self.data_provider = RobustDataProvider(self.data_client)
        
        # Trading state
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.daily_pnl = 0.0
        self.initial_equity = None
        
        # Performance tracking
        self.performance_data = {
            'start_time': datetime.now(),
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0
        }
        
        self.logger.info("🚀 Unified Trading Bot initialized")
    
    def _validate_config(self):
        """Validate configuration"""
        required = ['API_KEY', 'SECRET_KEY', 'STRATEGY', 'RISK_PCT', 'MAX_POSITIONS']
        missing = [k for k in required if k not in self.config]
        
        if missing:
            raise ValueError(f"Missing config keys: {missing}")
        
        if self.config['RISK_PCT'] > 0.1:
            self.logger.warning("⚠️ Risk per trade > 10%")
    
    def is_market_open(self) -> bool:
        """Check if market is open"""
        try:
            clock = self.trade_client.get_clock()
            return clock.is_open
        except Exception as e:
            self.logger.error(f"Failed to check market status: {e}")
            # Fallback to time-based check
            now = datetime.now()
            return 9 <= now.hour < 16 and now.weekday() < 5
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account = self.trade_client.get_account()
            
            info = {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power)
            }
            
            if self.initial_equity is None:
                self.initial_equity = info['equity']
                self.logger.info(f"💰 Initial equity: ${self.initial_equity:,.2f}")
            
            return info
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            return {'equity': 50000, 'cash': 50000, 'buying_power': 50000}
    
    def calculate_position_size(self, symbol: str, price: float) -> int:
        """Calculate position size based on risk management"""
        try:
            account_info = self.get_account_info()
            risk_amount = account_info['equity'] * self.config['RISK_PCT']
            
            # Adjust for number of existing positions
            position_adjustment = 1.0 / max(1, len(self.positions) + 1)
            adjusted_risk = risk_amount * position_adjustment
            
            shares = int(min(adjusted_risk / price, account_info['buying_power'] * 0.9 / price))
            return max(1, shares)
        except Exception as e:
            self.logger.error(f"Position sizing failed: {e}")
            return 1
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9).mean()  # FIXED: Renamed variable
        return macd, signal_line
    
    def trend_following_strategy(self, symbol: str) -> Optional[str]:
        """Enhanced trend following strategy"""
        try:
            data = self.data_provider.get_historical_data(symbol, days=50)
            if data.empty or len(data) < 30:
                return None
            
            # Calculate indicators
            data['ema_12'] = data['close'].ewm(span=12).mean()
            data['ema_26'] = data['close'].ewm(span=26).mean()
            data['rsi'] = self._calculate_rsi(data['close'])
            data['volume_sma'] = data['volume'].rolling(20).mean()
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Trend following conditions
            conditions = {
                'ema_cross_up': (last['ema_12'] > last['ema_26'] and 
                               prev['ema_12'] <= prev['ema_26']),
                'price_above_ema': last['close'] > last['ema_12'],
                'rsi_not_overbought': last['rsi'] < 70,
                'volume_confirmation': last['volume'] > last['volume_sma'] * 1.2
            }
            
            if sum(conditions.values()) >= 3:
                return 'buy'
            
            # Sell conditions
            sell_conditions = {
                'ema_cross_down': (last['ema_12'] < last['ema_26'] and 
                                 prev['ema_12'] >= prev['ema_26']),
                'price_below_ema': last['close'] < last['ema_12'],
                'rsi_oversold': last['rsi'] > 80
            }
            
            if sum(sell_conditions.values()) >= 2:
                return 'sell'
            
            return None
            
        except Exception as e:
            self.logger.error(f"Trend strategy failed for {symbol}: {e}")
            return None
    
    def mean_reversion_strategy(self, symbol: str) -> Optional[str]:
        """Mean reversion strategy"""
        try:
            data = self.data_provider.get_historical_data(symbol, days=30)
            if data.empty or len(data) < 20:
                return None
            
            # Calculate indicators
            data['sma_20'] = data['close'].rolling(20).mean()
            data['std_20'] = data['close'].rolling(20).std()
            data['bb_upper'] = data['sma_20'] + (data['std_20'] * 2)
            data['bb_lower'] = data['sma_20'] - (data['std_20'] * 2)
            data['rsi'] = self._calculate_rsi(data['close'])
            
            last = data.iloc[-1]
            
            # Oversold (buy trading_signal)
            if (last['close'] < last['bb_lower'] and 
                last['rsi'] < 30 and 
                last['close'] < data['close'].rolling(10).mean().iloc[-1]):
                return 'buy'
            
            # Overbought (sell trading_signal)
            if (last['close'] > last['bb_upper'] and 
                last['rsi'] > 70 and 
                last['close'] > data['close'].rolling(10).mean().iloc[-1]):
                return 'sell'
            
            return None
            
        except Exception as e:
            self.logger.error(f"Mean reversion strategy failed for {symbol}: {e}")
            return None
    
    def generate_signal(self, symbol: str) -> Optional[str]:
        """Generate trading signal based on strategy"""
        try:
            if self.config['STRATEGY'] == 'trend':
                return self.trend_following_strategy(symbol)
            elif self.config['STRATEGY'] == 'mean_reversion':
                return self.mean_reversion_strategy(symbol)
            elif self.config['STRATEGY'] == 'combined':
                trend_trading_signal = self.trend_following_strategy(symbol)
                mean_rev_trading_signal = self.mean_reversion_strategy(symbol)
                
                # Both must agree
                if trend_trading_signal == mean_rev_trading_signal and trend_trading_signal is not None:
                    return trend_trading_signal
                    
            return None
        except Exception as e:
            self.logger.error(f"Signal generation failed for {symbol}: {e}")
            return None
    
    def execute_trade(self, symbol: str, trading_signal: str):
        """Execute trade with enhanced error handling"""
        if symbol in self.positions:
            return
        
        if len(self.positions) >= self.config['MAX_POSITIONS']:
            self.logger.warning("Maximum positions reached")
            return
        
        try:
            # Get current price
            quote_data = self.data_provider.get_quote_data(symbol)
            if quote_data.empty:
                self.logger.warning(f"No quote data for {symbol}")
                return
            
            current_price = quote_data['ask'].iloc[0] if trading_signal == 'buy' else quote_data['bid'].iloc[0]
            position_size = self.calculate_position_size(symbol, current_price)
            
            # Create and submit order
            order = MarketOrderRequest(
                symbol=symbol,
                qty=position_size,
                side=OrderSide.BUY if trading_signal == 'buy' else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            submitted_order = self.trade_client.submit_order(order)
            
            # Track position
            position = Position(
                symbol=symbol,
                entry_price=current_price,
                quantity=position_size,
                order_id=submitted_order.id,
                timestamp=datetime.now(),
                strategy=self.config['STRATEGY']
            )
            
            self.positions[symbol] = position
            
            self.logger.info(f"🎯 {trading_signal.upper()} {position_size} {symbol} @ ${current_price:.2f}")
            
        except Exception as e:
            self.logger.error(f"Trade execution failed for {symbol}: {e}")
    
    def monitor_positions(self):
        """Monitor and manage existing positions"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                
                # Check order status
                try:
                    order = self.trade_client.get_order_by_id(position.order_id)
                    if order.status not in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                        # Cancel unfilled orders after 10 minutes
                        if datetime.now() - position.timestamp > timedelta(minutes=10):
                            self.trade_client.cancel_order_by_id(position.order_id)
                            del self.positions[symbol]
                            self.logger.info(f"🚫 Cancelled unfilled order for {symbol}")
                        continue
                except Exception as e:
                    self.logger.debug(f"Order status check failed for {symbol}: {e}")
                
                # Get current price
                quote_data = self.data_provider.get_quote_data(symbol)
                if quote_data.empty:
                    continue
                
                current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                pnl = (current_price - position.entry_price) * position.quantity
                pnl_pct = (current_price / position.entry_price - 1) * 100
                
                # Update position unrealized P&L
                position.unrealized_pnl = pnl
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                if current_price <= position.stop_loss:
                    should_exit = True
                    exit_reason = "Stop loss"
                elif current_price >= position.take_profit:
                    should_exit = True
                    exit_reason = "Take profit"
                elif datetime.now() - position.timestamp > timedelta(hours=24):
                    should_exit = True
                    exit_reason = "Time limit"
                
                if should_exit:
                    self._exit_position(symbol, current_price, exit_reason)
                else:
                    self.logger.debug(f"📈 {symbol}: ${current_price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:+.1f}%)")
                
            except Exception as e:
                self.logger.error(f"Position monitoring failed for {symbol}: {e}")
    
    def _exit_position(self, symbol: str, exit_price: float, reason: str):
        """Exit position and record trade"""
        try:
            position = self.positions[symbol]
            
            # Create exit order
            order = MarketOrderRequest(
                symbol=symbol,
                qty=position.quantity,
                side=OrderSide.SELL if position.quantity > 0 else OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            self.trade_client.submit_order(order)
            
            # Calculate P&L
            pnl = (exit_price - position.entry_price) * position.quantity
            
            # Record trade
            trade = Trade(
                symbol=symbol,
                entry_price=position.entry_price,
                exit_price=exit_price,
                quantity=position.quantity,
                entry_time=position.timestamp,
                exit_time=datetime.now(),
                pnl=pnl,
                strategy=position.strategy
            )
            
            self.trades.append(trade)
            self.daily_pnl += pnl
            self.performance_data['total_trades'] += 1
            if pnl > 0:
                self.performance_data['winning_trades'] += 1
            self.performance_data['total_pnl'] += pnl
            
            # Remove position
            del self.positions[symbol]
            
            self.logger.info(f"🏁 Exited {symbol} @ ${exit_price:.2f} - P&L: ${pnl:.2f} ({reason})")
            
        except Exception as e:
            self.logger.error(f"Position exit failed for {symbol}: {e}")
    
    def _select_symbols(self) -> List[str]:
        """Select liquid symbols for trading"""
        symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'JNJ', 'UNH', 'PFE',
            'HD', 'WMT', 'DIS', 'V', 'MA', 'SPY', 'QQQ', 'IWM'
        ]
        
        # Filter symbols with available data
        filtered_symbols = []
        for symbol in symbols:
            try:
                data = self.data_provider.get_historical_data(symbol, days=5)
                if not data.empty:
                    filtered_symbols.append(symbol)
                    if len(filtered_symbols) >= self.config.get('MAX_SYMBOLS', 15):
                        break
            except Exception as e:
                self.logger.debug(f"Skipping {symbol}: {e}")
        
        return filtered_symbols
    
    def _update_dashboard(self):
        """Update dashboard with current status"""
        try:
            account_info = self.get_account_info()
            win_rate = (self.performance_data['winning_trades'] / 
                       max(1, self.performance_data['total_trades'])) * 100
            
            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'status': 'running',
                'market_open': self.is_market_open(),
                'equity': account_info['equity'],
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.performance_data['total_pnl'],
                'positions': len(self.positions),
                'total_trades': self.performance_data['total_trades'],
                'win_rate': win_rate,
                'active_positions': {
                    symbol: {
                        'entry_price': pos.entry_price,
                        'entry_time': pos.timestamp.isoformat(),
                        'strategy': pos.strategy,
                        'unrealized_pnl': pos.unrealized_pnl
                    } for symbol, pos in self.positions.items()
                },
                'recent_trades': [
                    {
                        'symbol': trade.symbol,
                        'pnl': trade.pnl,
                        'exit_time': trade.exit_time.isoformat(),
                        'strategy': trade.strategy
                    } for trade in self.trades[-5:]  # Last 5 trades
                ]
            }
            
            # Save dashboard
            with open('dashboard.json', 'w') as f:
                json.dump(dashboard, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Dashboard update failed: {e}")
    
    def _save_state(self):
        """Save bot state to disk"""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'daily_pnl': self.daily_pnl,
                'performance_data': self.performance_data,
                'positions_count': len(self.positions),
                'trades_count': len(self.trades),
                'config': self.config
            }
            
            with open('bot_state.json', 'w') as f:
                json.dump(state, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"State save failed: {e}")
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        self.logger.info(f"🛑 Shutdown signal received: {signum}")
        self.shutdown_requested = True
    
    async def _shutdown_cleanup(self):
        """Cleanup on shutdown"""
        self.logger.info("🧹 Performing shutdown cleanup...")
        
        try:
            # Optionally close all positions
            if self.config.get('CLOSE_ON_SHUTDOWN', False):
                for symbol in list(self.positions.keys()):
                    quote_data = self.data_provider.get_quote_data(symbol)
                    if not quote_data.empty:
                        current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                        self._exit_position(symbol, current_price, "Shutdown")
            
            # Save final state
            self._save_state()
            
            # Generate final report
            account_info = self.get_account_info()
            total_return = ((account_info['equity'] - self.initial_equity) / 
                          self.initial_equity * 100) if self.initial_equity else 0
            
            self.logger.info(f"📊 Final Performance Summary:")
            self.logger.info(f"   Total Return: {total_return:+.2f}%")
            self.logger.info(f"   Daily P&L: ${self.daily_pnl:+.2f}")
            self.logger.info(f"   Total Trades: {self.performance_data['total_trades']}")
            if self.performance_data['total_trades'] > 0:
                win_rate = (self.performance_data['winning_trades'] / 
                           self.performance_data['total_trades'] * 100)
                self.logger.info(f"   Win Rate: {win_rate:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Shutdown cleanup error: {e}")
    
    async def run_autonomous(self):
        """Main autonomous trading loop"""
        self.logger.info("🚀 Starting Unified Autonomous Trading Bot")
        
        # Setup signal handlers - FIXED
        signal_module.signal(signal_module.SIGINT, self._handle_shutdown)
        signal_module.signal(signal_module.SIGTERM, self._handle_shutdown)
        
        # Initialize
        try:
            account_info = self.get_account_info()
            self.logger.info(f"💰 Account equity: ${account_info['equity']:,.2f}")
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            return
        
        loop_count = 0
        last_dashboard_update = datetime.now()
        last_daily_reset = datetime.now().date()
        
        while not self.shutdown_requested:
            try:
                loop_count += 1
                loop_start = datetime.now()
                
                # Reset daily P&L at market open
                if datetime.now().date() != last_daily_reset:
                    self.daily_pnl = 0.0
                    last_daily_reset = datetime.now().date()
                    self.logger.info("📅 New trading day - P&L reset")
                
                # Check if market is open
                if not self.is_market_open():
                    if loop_count % 12 == 1:  # Log every hour when closed
                        self.logger.info("🕒 Market is closed, waiting...")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                # Check daily loss limit
                max_daily_loss = self.config.get('MAX_DAILY_LOSS', 0.02)
                if self.daily_pnl < -max_daily_loss * self.initial_equity:
                    self.logger.warning("🚨 Daily loss limit reached, pausing trading")
                    await asyncio.sleep(3600)  # Wait 1 hour
                    continue
                
                # Get symbols to analyze
                symbols = self._select_symbols()
                self.logger.debug(f"📋 Analyzing {len(symbols)} symbols")
                
                # Analyze symbols for trading opportunities
                for symbol in symbols:
                    try:
                        # Skip if we already have a position
                        if symbol in self.positions:
                            continue
                        
                        # Generate trading signal
                        trading_signal = self.generate_signal(symbol)
                        if trading_signal:
                            self.logger.info(f"🎯 {trading_signal.upper()} signal for {symbol}")
                            self.execute_trade(symbol, trading_signal)
                            
                    except Exception as e:
                        self.logger.error(f"Analysis failed for {symbol}: {e}")
                
                # Monitor existing positions
                self.monitor_positions()
                
                # Update dashboard every 5 minutes
                if datetime.now() - last_dashboard_update > timedelta(minutes=5):
                    self._update_dashboard()
                    last_dashboard_update = datetime.now()
                
                # Progress logging
                if loop_count % 10 == 0:
                    self.logger.info(f"🔄 Loop #{loop_count} - "
                                   f"Positions: {len(self.positions)}, "
                                   f"Daily P&L: ${self.daily_pnl:+.2f}, "
                                   f"Trades: {self.performance_data['total_trades']}")
                
                # Save state periodically
                if loop_count % 20 == 0:
                    self._save_state()
                
                # Calculate sleep time (target 1-minute loops)
                loop_duration = (datetime.now() - loop_start).total_seconds()
                sleep_time = max(10, 60 - loop_duration)
                await asyncio.sleep(sleep_time)
                
                # Reset error counter on successful loop
                self.consecutive_errors = 0
                
            except Exception as e:
                self.consecutive_errors += 1
                self.logger.error(f"💥 Error in main loop #{loop_count}: {e}")
                
                # Emergency shutdown if too many consecutive errors
                if self.consecutive_errors >= 10:
                    self.logger.critical("🚨 Too many consecutive errors - emergency shutdown")
                    break
                
                # Exponential backoff
                backoff_time = min(300, 30 * (2 ** min(self.consecutive_errors, 4)))
                self.logger.warning(f"⏳ Waiting {backoff_time}s before retry...")
                await asyncio.sleep(backoff_time)
        
        # Cleanup
        await self._shutdown_cleanup()
        self.logger.info("✅ Unified Trading Bot shutdown complete")

def validate_environment():
    """Validate environment and configuration"""
    print("🔧 Validating environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check required environment variables
    required_vars = ['APCA_API_KEY_ID', 'APCA_API_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Set them in your environment or .env file")
        return False
    
    # Create directories
    for directory in ['logs', 'data', 'backups']:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Environment validation passed")
    return True

def create_config() -> Dict:
    """Create trading configuration"""
    return {
        # API Configuration
        'API_KEY': os.getenv('APCA_API_KEY_ID'),
        'SECRET_KEY': os.getenv('APCA_API_SECRET_KEY'),
        'PAPER_TRADING': os.getenv('PAPER_TRADING', 'True').lower() == 'true',
        
        # Risk Management
        'RISK_PCT': float(os.getenv('RISK_PCT', '0.015')),  # 1.5% per trade
        'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', '3')),
        'MAX_DAILY_LOSS': float(os.getenv('MAX_DAILY_LOSS', '0.02')),  # 2% max daily loss
        'MAX_SYMBOLS': int(os.getenv('MAX_SYMBOLS', '15')),
        
        # Strategy
        'STRATEGY': os.getenv('STRATEGY', 'combined'),  # 'trend', 'mean_reversion', 'combined'
        
        # Operational
        'CLOSE_ON_SHUTDOWN': os.getenv('CLOSE_ON_SHUTDOWN', 'False').lower() == 'true',
    }

async def main():
    """Main entry point"""
    print("🚀 Unified Industry-Grade Trading Bot v5.0")
    print("=" * 50)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Create configuration
    config = create_config()
    
    # Display configuration
    print("🎯 Configuration:")
    print(f"   Paper Trading: {'Yes' if config['PAPER_TRADING'] else 'No'}")
    print(f"   Risk per Trade: {config['RISK_PCT']*100:.1f}%")
    print(f"   Max Positions: {config['MAX_POSITIONS']}")
    print(f"   Strategy: {config['STRATEGY']}")
    print(f"   Max Daily Loss: {config['MAX_DAILY_LOSS']*100:.1f}%")
    
    # Confirmation
    if not config['PAPER_TRADING']:
        response = input("\n⚠️  LIVE TRADING MODE - Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled by user")
            sys.exit(0)
    
    print("\n🏁 Starting autonomous trading...")
    print("   Press Ctrl+C to stop gracefully")
    print("   Monitor progress in dashboard.json")
    print("   Logs available in logs/trading_bot.log")
    print("=" * 50)
    
    try:
        # Create and run bot
        bot = UnifiedTradingBot(config)
        await bot.run_autonomous()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"💥 Critical error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())