"""
AlgoTradingBot v2.0 - Enhanced Algorithmic Trading System
Improved version with better error handling, logging, and algorithm optimizations
"""


# -*- coding: utf-8 -*-
import os
import logging
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
from collections import defaultdict
import json

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass, OrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Position:
    """Data class for position tracking"""
    symbol: str
    entry_price: float
    quantity: float
    order_id: str
    timestamp: datetime
    strategy: str
    stop_loss: float
    take_profit: float

@dataclass
class Trade:
    """Data class for completed trades"""
    symbol: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    strategy: str

class TradingMetrics:
    """Class to handle trading performance metrics"""
    
    def __init__(self):
        self.trades: List[Trade] = []
        self.daily_pnl = defaultdict(float)
        self.initial_equity = None
        
    def add_trade(self, trade: Trade):
        """Add completed trade to metrics"""
        self.trades.append(trade)
        date_key = trade.exit_time.date()
        self.daily_pnl[date_key] += trade.pnl
        
    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if not self.trades:
            return 0.0
        winning_trades = sum(1 for trade in self.trades if trade.pnl > 0)
        return (winning_trades / len(self.trades)) * 100
        
    def calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio based on daily returns"""
        if len(self.daily_pnl) < 2:
            return 0.0
        
        daily_returns = list(self.daily_pnl.values())
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        
        if std_return == 0:
            return 0.0
        
        # Assuming 252 trading days per year
        return (mean_return / std_return) * np.sqrt(252)
        
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.trades:
            return 0.0
            
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in self.trades:
            cumulative_pnl += trade.pnl
            peak = max(peak, cumulative_pnl)
            drawdown = (peak - cumulative_pnl) / peak if peak != 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
            
        return max_drawdown * 100

# Enhanced logging configuration
def setup_logging(log_level=logging.INFO):
    """Setup comprehensive logging configuration"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    logger = logging.getLogger('AlgoTradingBot')
    logger.setLevel(log_level)
    
    # File handlers
    file_handler = logging.FileHandler('logs/algo_trading.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    trade_handler = logging.FileHandler('logs/trades.log')
    trade_handler.setLevel(logging.INFO)
    trade_handler.setFormatter(simple_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    # Create trade logger
    trade_logger = logging.getLogger('AlgoTradingBot.trades')
    trade_logger.addHandler(trade_handler)
    trade_logger.propagate = False
    
    return logger

class AlgoTradingBot:
    """Enhanced algorithmic trading engine with improved risk management"""
    
    def __init__(self, config: Dict):
        """Initialize trading bot with enhanced configuration"""
        self.config = config
        self.logger = setup_logging()
        self._validate_config()
        
        # Initialize Alpaca clients with better error handling
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
            self.logger.info("Successfully connected to Alpaca API")
        except Exception as e:
            self.logger.error(f"Failed to initialize Alpaca clients: {str(e)}")
            raise
        
        # Enhanced position and metrics tracking
        self.positions: Dict[str, Position] = {}
        self.metrics = TradingMetrics()
        self.last_signal = {}
        self.market_session_active = False
        
        # Risk management parameters
        self.max_daily_loss = self.config.get('MAX_DAILY_LOSS', 0.02)  # 2% max daily loss
        self.daily_pnl = 0.0
        self.initial_equity = None

    def _validate_config(self):
        """Enhanced configuration validation"""
        required_keys = ['API_KEY', 'SECRET_KEY', 'RISK_PCT', 'MAX_POSITIONS', 'STRATEGY']
        missing_keys = [k for k in required_keys if k not in self.config]
        
        if missing_keys:
            raise ValueError(f"Missing required configuration parameters: {missing_keys}")
            
        # Validate risk parameters
        if self.config['RISK_PCT'] > 0.1:
            self.logger.warning("Risk per trade exceeds recommended 10% limit")
            
        if self.config.get('MAX_DAILY_LOSS', 0.02) > 0.05:
            self.logger.warning("Maximum daily loss exceeds recommended 5% limit")
            
        # Validate strategy
        valid_strategies = ['trend', 'mean_reversion', 'combined']
        if self.config['STRATEGY'] not in valid_strategies:
            raise ValueError(f"Invalid strategy. Must be one of: {valid_strategies}")

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.trade_client.get_clock()
            return clock.is_open
        except Exception as e:
            self.logger.error(f"Failed to check market status: {str(e)}")
            return False

    def get_account_info(self) -> Dict:
        """Enhanced account information retrieval with caching"""
        try:
            account = self.trade_client.get_account()
            
            if account.trading_blocked:
                raise Exception("Account trading is blocked")
                
            account_info = {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'daytrade_count': int(account.daytrade_count),
                'pattern_day_trader': account.pattern_day_trader
            }
            
            # Set initial equity if not set
            if self.initial_equity is None:
                self.initial_equity = account_info['equity']
                self.metrics.initial_equity = self.initial_equity
                
            return account_info
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve account information: {str(e)}")
            raise

    def calculate_position_size(self, symbol: str, current_price: float, volatility: float = None) -> int:
        """
        Enhanced position sizing with Kelly Criterion, dynamic risk adjustment, and event-driven factors
        """
        try:
            account_info = self.get_account_info()
            
            # STEP 1: Calculate Kelly Criterion base risk
            symbol_trades = [t for t in self.metrics.trades if t.symbol == symbol]
            
            if len(symbol_trades) >= 10:  # Use Kelly if sufficient history
                wins = sum(1 for t in symbol_trades if t.pnl > 0)
                win_rate = wins / len(symbol_trades)
                
                if wins > 0 and len(symbol_trades) - wins > 0:
                    avg_win = np.mean([t.pnl for t in symbol_trades if t.pnl > 0])
                    avg_loss = abs(np.mean([t.pnl for t in symbol_trades if t.pnl < 0]))
                    
                    if avg_loss > 0:
                        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                        kelly_fraction = max(0.01, min(0.25, kelly_fraction))  # Cap at 25%
                    else:
                        kelly_fraction = self.config['RISK_PCT']
                else:
                    kelly_fraction = self.config['RISK_PCT']
            else:
                kelly_fraction = self.config['RISK_PCT']
            
            # STEP 2: Apply portfolio and market adjustments
            portfolio_heat = self._calculate_portfolio_heat()
            heat_adjustment = max(0.5, 1 - portfolio_heat)  # Reduce size if portfolio is "hot"
            
            # Volatility adjustment
            if volatility and volatility > 0:
                vol_adjustment = min(1.0, 0.02 / volatility)  # Target 2% volatility
            else:
                vol_adjustment = 1.0
            
            # Market regime adjustment
            market_regime = self._detect_market_regime()
            regime_adjustment = 0.5 if market_regime == 'high_stress' else 1.0
            
            # STEP 3: Apply event-driven risk adjustments (NEW)
            event_adjustment = 1.0
            if hasattr(self, '_event_risk_adjustments') and symbol in self._event_risk_adjustments:
                event_adjustment = self._event_risk_adjustments[symbol]
                
            # STEP 4: Calculate final position size
            # Combine all adjustments
            total_adjustment = kelly_fraction * heat_adjustment * vol_adjustment * regime_adjustment * event_adjustment
            
            max_investment = min(
                account_info['equity'] * total_adjustment,
                account_info['buying_power'] * 0.9
            )
            
            shares = int(max_investment / current_price)
            
            # STEP 5: Logging for transparency
            self.logger.debug(f"Position sizing for {symbol}: "
                            f"Kelly={kelly_fraction:.3f}, "
                            f"Heat={heat_adjustment:.3f}, "
                            f"Vol={vol_adjustment:.3f}, "
                            f"Regime={regime_adjustment:.3f}, "
                            f"Event={event_adjustment:.3f}, "
                            f"Final={total_adjustment:.3f}, "
                            f"Shares={shares}")
            
            if event_adjustment < 1.0:
                self.logger.info(f"Position size for {symbol} reduced by events: {event_adjustment:.2f}")
                
            return max(1, shares)  # Always return at least 1 share
            
        except Exception as e:
            self.logger.error(f"Enhanced position sizing failed for {symbol}: {str(e)}")
            
            # FALLBACK: Simple position sizing without recursion
            try:
                account_info = self.get_account_info()
                simple_investment = account_info['equity'] * self.config['RISK_PCT']
                fallback_shares = int(simple_investment / current_price)
                
                self.logger.info(f"Using fallback position sizing for {symbol}: {fallback_shares} shares")
                return max(1, fallback_shares)
                
            except Exception as fallback_error:
                self.logger.error(f"Even fallback position sizing failed for {symbol}: {str(fallback_error)}")
                return 1  # Minimum viable position
            
    def _calculate_portfolio_heat(self) -> float:
        """Calculate portfolio heat (correlation risk)"""
        if len(self.positions) < 2:
            return 0.0
            
        symbols = list(self.positions.keys())
        correlations = []
        
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                try:
                    data1 = self._get_historical_data(sym1, days=30)
                    data2 = self._get_historical_data(sym2, days=30)
                    
                    if not data1.empty and not data2.empty:
                        corr = data1['close'].pct_change().corr(data2['close'].pct_change())
                        if not np.isnan(corr):
                            correlations.append(abs(corr))
                except:
                    continue
        
        return np.mean(correlations) if correlations else 0.0
    
    def _calculate_macd(self, prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence) indicator
        Returns: (macd_line, signal_line)
        """
        try:
            # Calculate exponential moving averages
            ema_fast = prices.ewm(span=fast_period).mean()
            ema_slow = prices.ewm(span=slow_period).mean()
            
            # MACD line = difference between fast and slow EMA
            macd_line = ema_fast - ema_slow
            
            # Signal line = EMA of MACD line
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            return macd_line, signal_line
            
        except Exception as e:
            self.logger.error(f"MACD calculation failed: {str(e)}")
            # Return empty series if calculation fails
            return pd.Series(dtype=float), pd.Series(dtype=float)

    def _detect_market_regime(self) -> str:
        """Detect current market regime for risk adjustment"""
        try:
            spy_data = self._get_historical_data('SPY', days=20)
            if spy_data.empty:
                return 'normal'
                
            recent_vol = spy_data['close'].pct_change().tail(10).std()
            long_vol = spy_data['close'].pct_change().std()
            
            if recent_vol > long_vol * 2:
                return 'high_stress'
            elif recent_vol < long_vol * 0.5:
                return 'low_vol'
            else:
                return 'normal'
                
        except:
            return 'normal'

    def get_real_time_data(self, symbol: str) -> pd.DataFrame:
        """Enhanced real-time data retrieval with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quote_data = self.data_client.get_stock_latest_quote(request_params)
                
                if symbol not in quote_data:
                    raise ValueError(f"No data returned for symbol {symbol}")
                
                quote = quote_data[symbol]
                return pd.DataFrame({
                    'timestamp': [quote.timestamp],
                    'bid': [float(quote.bid_price)],
                    'ask': [float(quote.ask_price)],
                    'bid_size': [int(quote.bid_size)],
                    'ask_size': [int(quote.ask_size)]
                })
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.logger.error(f"All attempts failed for {symbol}")
                    return pd.DataFrame()

    def trend_following_strategy(self, symbol: str) -> Optional[str]:
        """
        Enhanced Dual Moving Average Crossover with multiple filters
        """
        try:
            data = self._get_historical_data(symbol, days=100)
            if data.empty or len(data) < 50:
                self.logger.debug(f"Insufficient data for {symbol}")
                return None
                
            # Calculate indicators
            data['ema_fast'] = data['close'].ewm(span=12).mean()
            data['ema_slow'] = data['close'].ewm(span=26).mean()
            data['sma_trend'] = data['close'].rolling(50).mean()
            data['atr'] = self._calculate_atr(data)
            data['volume_ma'] = data['volume'].rolling(20).mean()
            
            # MACD
            data['macd'] = data['ema_fast'] - data['ema_slow']
            data['signal_line'] = data['macd'].ewm(span=9).mean()
            
            last_row = data.iloc[-1]
            prev_row = data.iloc[-2]
            
            # Multiple confirmation filters
            conditions = {
                'trend_up': last_row['close'] > last_row['sma_trend'],
                'ema_cross_up': (last_row['ema_fast'] > last_row['ema_slow'] and 
                               prev_row['ema_fast'] <= prev_row['ema_slow']),
                'macd_positive': last_row['macd'] > last_row['signal_line'],
                'volume_confirm': last_row['volume'] > last_row['volume_ma'] * 1.2,
                'volatility_ok': last_row['atr'] < data['atr'].quantile(0.8)
            }
            
            # Buy signal: at least 4 out of 5 conditions
            if sum(conditions.values()) >= 4:
                self.logger.info(f"Strong BUY signal for {symbol}: {conditions}")
                return 'buy'
                
            # Sell signal (reverse conditions)
            sell_conditions = {
                'trend_down': last_row['close'] < last_row['sma_trend'],
                'ema_cross_down': (last_row['ema_fast'] < last_row['ema_slow'] and 
                                 prev_row['ema_fast'] >= prev_row['ema_slow']),
                'macd_negative': last_row['macd'] < last_row['signal_line'],
                'volume_confirm': last_row['volume'] > last_row['volume_ma'] * 1.2
            }
            
            if sum(sell_conditions.values()) >= 3:
                self.logger.info(f"SELL signal for {symbol}: {sell_conditions}")
                return 'sell'
                
            return None
            
        except Exception as e:
            self.logger.error(f"Trend following strategy failed for {symbol}: {str(e)}")
            return None

    def mean_reversion_strategy(self, symbol: str) -> Optional[str]:
        """
        Enhanced Mean Reversion with multiple oscillators
        """
        try:
            data = self._get_historical_data(symbol, days=60)
            if data.empty or len(data) < 30:
                return None
                
            # Calculate indicators
            data['rsi'] = self._calculate_rsi(data['close'])
            data['bb_upper'], data['bb_lower'] = self._calculate_bollinger_bands(data['close'])
            data['bb_mid'] = (data['bb_upper'] + data['bb_lower']) / 2
            data['stoch_k'], data['stoch_d'] = self._calculate_stochastic(data)
            
            last_row = data.iloc[-1]
            
            # Oversold conditions
            oversold_conditions = {
                'rsi_oversold': last_row['rsi'] < 30,
                'bb_oversold': last_row['close'] < last_row['bb_lower'],
                'stoch_oversold': last_row['stoch_k'] < 20,
                'price_below_mean': last_row['close'] < data['close'].rolling(20).mean().iloc[-1]
            }
            
            # Overbought conditions
            overbought_conditions = {
                'rsi_overbought': last_row['rsi'] > 70,
                'bb_overbought': last_row['close'] > last_row['bb_upper'],
                'stoch_overbought': last_row['stoch_k'] > 80,
                'price_above_mean': last_row['close'] > data['close'].rolling(20).mean().iloc[-1]
            }
            
            if sum(oversold_conditions.values()) >= 3:
                self.logger.info(f"Mean reversion BUY signal for {symbol}")
                return 'buy'
                
            if sum(overbought_conditions.values()) >= 3:
                self.logger.info(f"Mean reversion SELL signal for {symbol}")
                return 'sell'
                
            return None
            
        except Exception as e:
            self.logger.error(f"Mean reversion strategy failed for {symbol}: {str(e)}")
            return None

    def execute_trade(self, symbol: str, signal: str):
        """
        Enhanced trade execution with market microstructure analysis
        """
        if not self.is_market_open():
            self.logger.warning("Market is closed, skipping trade execution")
            return
            
        if symbol in self.positions:
            self.logger.info(f"Existing position for {symbol}, skipping trade")
            return
            
        # Enhanced pre-trade checks
        if not self._pre_trade_risk_check(symbol, signal):
            return
            
        try:
            # Market microstructure analysis
            liquidity_score = self._analyze_market_liquidity(symbol)
            if liquidity_score < 0.5:
                self.logger.warning(f"Poor liquidity for {symbol}: {liquidity_score:.2f}")
                return
                
            # Get order book data
            quote_data = self.get_real_time_data(symbol)
            if quote_data.empty:
                return
                
            # Smart order routing
            execution_strategy = self._determine_execution_strategy(symbol, quote_data)
            
            if execution_strategy == 'market':
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=self.calculate_position_size(symbol, quote_data['ask'].iloc[0]),
                    side=OrderSide.BUY if signal == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.IOC  # Immediate or Cancel
                )
            else:
                # TWAP-style limit order
                limit_price = self._calculate_smart_limit_price(symbol, quote_data, signal)
                order = LimitOrderRequest(
                    symbol=symbol,
                    qty=self.calculate_position_size(symbol, limit_price),
                    side=OrderSide.BUY if signal == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )
            
            submitted_order = self.trade_client.submit_order(order)
            
            # Enhanced position tracking with microstructure data
            position = Position(
                symbol=symbol,
                entry_price=limit_price if execution_strategy != 'market' else quote_data['ask'].iloc[0],
                quantity=order.qty,
                order_id=submitted_order.id,
                timestamp=datetime.now(),
                strategy=f"{self.config['STRATEGY']}_enhanced",
                stop_loss=self._calculate_adaptive_stop_loss(symbol, limit_price, signal),
                take_profit=self._calculate_adaptive_take_profit(symbol, limit_price, signal)
            )
            
            self.positions[symbol] = position
            
            # Log with execution details
            trade_logger = logging.getLogger('AlgoTradingBot.trades')
            trade_logger.info(f"ENHANCED_TRADE,{symbol},{signal},{order.qty},{limit_price:.2f},"
                            f"{liquidity_score:.2f},{execution_strategy}")
            
        except Exception as e:
            self.logger.error(f"Enhanced trade execution failed for {symbol}: {str(e)}")

    def _analyze_market_liquidity(self, symbol: str) -> float:
        """Analyze market liquidity using multiple metrics"""
        try:
            quote_data = self.get_real_time_data(symbol)
            historical_data = self._get_historical_data(symbol, days=5)
            
            if quote_data.empty or historical_data.empty:
                return 0.0
                
            # Bid-ask spread
            spread = (quote_data['ask'].iloc[0] - quote_data['bid'].iloc[0]) / quote_data['ask'].iloc[0]
            
            # Volume consistency
            recent_volume = historical_data['volume'].tail(5).mean()
            avg_volume = historical_data['volume'].mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
            
            # Market depth (simplified)
            depth_score = min(1.0, (quote_data['bid_size'].iloc[0] + quote_data['ask_size'].iloc[0]) / 1000)
            
            # Composite liquidity score
            liquidity_score = (
                (1 - min(1.0, spread * 100)) * 0.4 +  # Lower spread = higher liquidity
                min(1.0, volume_ratio) * 0.4 +         # Higher volume = higher liquidity
                depth_score * 0.2                      # Higher depth = higher liquidity
            )
            
            return liquidity_score
            
        except Exception as e:
            self.logger.error(f"Liquidity analysis failed for {symbol}: {str(e)}")
            return 0.5

    def _calculate_adaptive_stop_loss(self, symbol: str, entry_price: float, signal: str) -> float:
        """Calculate adaptive stop loss based on volatility and support/resistance"""
        try:
            data = self._get_historical_data(symbol, days=30)
            if data.empty:
                return entry_price * (0.97 if signal == 'buy' else 1.03)
                
            # ATR-based stop
            atr = self._calculate_atr(data).iloc[-1]
            atr_multiplier = 2.0
            
            # Support/resistance levels
            recent_lows = data['low'].tail(20).min()
            recent_highs = data['high'].tail(20).max()
            
            if signal == 'buy':
                atr_stop = entry_price - (atr * atr_multiplier)
                support_stop = recent_lows * 0.99
                return max(atr_stop, support_stop)
            else:
                atr_stop = entry_price + (atr * atr_multiplier)
                resistance_stop = recent_highs * 1.01
                return min(atr_stop, resistance_stop)
                
        except Exception as e:
            self.logger.error(f"Adaptive stop loss calculation failed: {str(e)}")
            return entry_price * (0.97 if signal == 'buy' else 1.03)

    def monitor_positions(self):
        """Enhanced position monitoring with trailing stops"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                
                # Check order status first
                order = self.trade_client.get_order_by_id(position.order_id)
                if order.status not in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                    # Cancel unfilled orders after 5 minutes
                    if datetime.now() - position.timestamp > timedelta(minutes=5):
                        self.trade_client.cancel_order_by_id(position.order_id)
                        del self.positions[symbol]
                        self.logger.info(f"Cancelled unfilled order for {symbol}")
                    continue
                
                # Get current price
                quote_data = self.get_real_time_data(symbol)
                if quote_data.empty:
                    continue
                    
                current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                
                # Calculate P&L
                pnl = (current_price - position.entry_price) * position.quantity
                pnl_pct = (current_price / position.entry_price - 1) * 100
                
                # Trailing stop logic
                if pnl_pct > 5:  # If profit > 5%, implement trailing stop
                    new_stop = current_price * 0.98  # 2% trailing stop
                    if new_stop > position.stop_loss:
                        position.stop_loss = new_stop
                        self.logger.info(f"Updated trailing stop for {symbol}: ${new_stop:.2f}")
                
                # Exit conditions
                should_exit = (
                    current_price <= position.stop_loss or
                    current_price >= position.take_profit or
                    datetime.now() - position.timestamp > timedelta(hours=24)  # Max hold time
                )
                
                if should_exit:
                    self._exit_position(symbol, current_price, "Stop/Target hit")
                    
            except Exception as e:
                self.logger.error(f"Position monitoring failed for {symbol}: {str(e)}")

    def _exit_position(self, symbol: str, current_price: float, reason: str):
        """Enhanced position exit with better tracking"""
        try:
            position = self.positions[symbol]
            
            # Create market order to exit
            order = MarketOrderRequest(
                symbol=symbol,
                qty=position.quantity,
                side=OrderSide.SELL if position.order_id else OrderSide.BUY,  # Opposite of entry
                time_in_force=TimeInForce.DAY
            )
            
            exit_order = self.trade_client.submit_order(order)
            
            # Calculate P&L
            pnl = (current_price - position.entry_price) * position.quantity
            
            # Create trade record
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
            
        except Exception as e:
            self.logger.error(f"Position exit failed for {symbol}: {str(e)}")

    def _get_historical_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Enhanced historical data retrieval with caching"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 50)  # Extra buffer
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                start=start_date,
                end=end_date,
                timeframe=TimeFrame.Day
            )
            
            bars_response = self.data_client.get_stock_bars(request)
            
            # NEW: Better error handling for the response
            if bars_response is None:
                self.logger.debug(f"No bars response for {symbol}")
                return pd.DataFrame()
                
            # Check if symbol exists in response
            if not hasattr(bars_response, 'df') or bars_response.df is None:
                self.logger.debug(f"No dataframe in response for {symbol}")
                return pd.DataFrame()
                
            df = bars_response.df.reset_index()
            
            # Ensure we have enough data
            if len(df) < days * 0.8:  # At least 80% of requested days
                self.logger.debug(f"Insufficient historical data for {symbol}: {len(df)} bars")
                return pd.DataFrame()
                
            return df.tail(days)  # Return only requested number of days
            
        except Exception as e:
            self.logger.debug(f"Historical data fetch failed for {symbol}: {str(e)}")
            return pd.DataFrame()

    def _calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        low_min = data['low'].rolling(k_period).min()
        high_max = data['high'].rolling(k_period).max()
        
        k_percent = 100 * ((data['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(d_period).mean()
        
        return k_percent, d_percent

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, num_std: int = 2) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, lower_band
    
    def _select_symbols(self) -> List[str]:
        """Enhanced symbol selection with volume and liquidity filters"""
        # Base universe of liquid stocks
        base_symbols = [
        'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 
        'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS',
        'ADBE', 'NFLX', 'CRM', 'PYPL', 'INTC', 'AMD', 'QCOM',
        'BAC', 'XOM', 'WMT', 'LLY', 'ABBV', 'COST', 'PFE', 'KO', 
        'AVGO', 'TMO', 'ACN', 'MRK', 'CSCO', 'PEP', 'ABT', 'CVX', 
        'VZ', 'NKE', 'WFC', 'T', 'ORCL', 'CMCSA', 'IBM', 'MDT',
        'TXN', 'AMGN', 'HON', 'BMY', 'SBUX', 'CAT',
        'LMT', 'MMM', 'BA', 'GS', 'RTX', 'C', 'USB', 'SCHW',
        'INTU', 'NOW', 'ZM', 'SNAP', 'DOCU',
        'UBER', 'LYFT', 'PLTR', 'CRWD', 'DDOG', 'SNOW'
        ]
        
        # Filter based on volume and avoid penny stocks
        filtered_symbols = []
        for symbol in base_symbols:
            try:
                data = self._get_historical_data(symbol, days=5)
                if not data.empty and data['volume'].mean() > 1000000:  # Min 1M avg volume
                    filtered_symbols.append(symbol)
            except Exception as e:
                self.logger.debug(f"Skipping {symbol} due to data issue: {str(e)}")
                # Continue to next symbol instead of logging error
                
        self.logger.info(f"Selected {len(filtered_symbols)} symbols for analysis")
        return filtered_symbols
    
    def generate_performance_report(self):
        """Enhanced performance reporting with detailed metrics"""
        try:
            account_info = self.get_account_info()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'account': {
                    'equity': account_info['equity'],
                    'cash': account_info['cash'],
                    'buying_power': account_info['buying_power']
                },
                'performance': {
                    'total_pnl': account_info['equity'] - self.initial_equity if self.initial_equity else 0,
                    'daily_pnl': self.daily_pnl,
                    'total_trades': len(self.metrics.trades),
                    'win_rate': self.metrics.calculate_win_rate(),
                    'sharpe_ratio': self.metrics.calculate_sharpe_ratio(),
                    'max_drawdown': self.metrics.calculate_max_drawdown()
                },
                'positions': {
                    'active_count': len(self.positions),
                    'symbols': list(self.positions.keys())
                }
            }
            
            # Save report to file
            with open(f'logs/performance_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Performance Report Generated: {report}")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {str(e)}")
            return None
        
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

    def run(self):
        """Enhanced main trading loop with better error handling"""
        self.logger.info("Starting Enhanced AlgoTradingBot v2.0")
        
        # Initialize
        try:
            account_info = self.get_account_info()
            self.logger.info(f"Account initialized - Equity: ${account_info['equity']:,.2f}")
        except Exception as e:
            self.logger.error(f"Failed to initialize account: {str(e)}")
            return
        
        loop_count = 0
        last_report_time = datetime.now()
        
        while True:
            try:
                loop_count += 1
                self.logger.debug(f"Starting trading loop #{loop_count}")
                
                # Check if market is open
                if not self.is_market_open():
                    self.logger.info("Market is closed, waiting...")
                    time.sleep(300)  # Wait 5 minutes
                    continue
                
                # Reset daily P&L at market open
                current_time = datetime.now()
                if current_time.hour == 9 and current_time.minute <= 35:  # Market open time
                    self.daily_pnl = 0.0
                    self.logger.info("Daily P&L reset for new trading day")
                
                # Check daily loss limit
                if self.daily_pnl < -self.max_daily_loss * self.initial_equity:
                    self.logger.warning("Daily loss limit reached, pausing trading for today")
                    time.sleep(3600)  # Wait 1 hour
                    continue
                
                # Get symbols to analyze
                symbols = self._select_symbols()
                
                # Analyze each symbol
                for symbol in symbols:
                    try:
                        # Skip if we already have a position
                        if symbol in self.positions:
                            continue
                            
                        # Generate trading signal
                        signal = None
                        if self.config['STRATEGY'] == 'trend':
                            signal = self.trend_following_strategy(symbol)
                        elif self.config['STRATEGY'] == 'mean_reversion':
                            signal = self.mean_reversion_strategy(symbol)
                        elif self.config['STRATEGY'] == 'combined':
                            # Combined strategy - both must agree
                            trend_signal = self.trend_following_strategy(symbol)
                            mean_rev_signal = self.mean_reversion_strategy(symbol)
                            if trend_signal == mean_rev_signal and trend_signal is not None:
                                signal = trend_signal
                        
                        # Execute trade if signal is present
                        if signal:
                            # Avoid overtrading - limit signals per symbol
                            last_signal_time = self.last_signal.get(symbol, datetime.min)
                            if datetime.now() - last_signal_time > timedelta(hours=1):
                                self.execute_trade(symbol, signal)
                                self.last_signal[symbol] = datetime.now()
                            else:
                                self.logger.debug(f"Skipping {symbol} - recent signal within 1 hour")
                                
                    except Exception as e:
                        self.logger.error(f"Error analyzing {symbol}: {str(e)}")
                        continue
                
                # Monitor existing positions
                self.monitor_positions()
                
                # Generate performance report every hour
                if datetime.now() - last_report_time > timedelta(hours=1):
                    self.generate_performance_report()
                    last_report_time = datetime.now()
                
                # Log loop completion
                if loop_count % 10 == 0:  # Every 10th loop
                    self.logger.info(f"Completed {loop_count} trading loops - "
                                   f"Active positions: {len(self.positions)}, "
                                   f"Daily P&L: ${self.daily_pnl:.2f}")
                
                # Sleep between loops - adjust based on strategy frequency
                sleep_time = self.config.get('LOOP_SLEEP', 60)  # Default 1 minute
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal, closing positions...")
                self._emergency_shutdown()
                break
                
            except Exception as e:
                self.logger.error(f"Critical error in main loop: {str(e)}")
                # Don't exit on error, just wait and retry
                time.sleep(300)  # Wait 5 minutes before retrying
                
        self.logger.info("Trading bot shutdown complete")
    
    def _emergency_shutdown(self):
        """Emergency shutdown procedure to close all positions"""
        self.logger.warning("Initiating emergency shutdown...")
        
        for symbol in list(self.positions.keys()):
            try:
                quote_data = self.get_real_time_data(symbol)
                if not quote_data.empty:
                    current_price = (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
                    self._exit_position(symbol, current_price, "Emergency shutdown")
            except Exception as e:
                self.logger.error(f"Failed to close position for {symbol}: {str(e)}")
        
        # Generate final report
        final_report = self.generate_performance_report()
        if final_report:
            self.logger.info("Final performance report generated")

    def ml_enhanced_signal(self, symbol: str) -> Optional[str]:
        """
        ML-enhanced signal generation using ensemble methods
        """
        try:
            # Get extended historical data for ML features
            data = self._get_historical_data(symbol, days=200)
            if data.empty or len(data) < 100:
                return None
                
            # Feature engineering
            features_df = self._create_ml_features(data)
            
            # Simple ensemble prediction (replace with trained models in production)
            signal_strength = self._calculate_signal_strength(features_df)
            
            # Dynamic threshold based on market volatility
            vix_threshold = self._get_market_volatility_threshold()
            
            if signal_strength > 0.7 + vix_threshold:
                return 'buy'
            elif signal_strength < -0.7 - vix_threshold:
                return 'sell'
                
            return None
            
        except Exception as e:
            self.logger.error(f"ML signal generation failed for {symbol}: {str(e)}")
            return None

    def _create_ml_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive feature set for ML models"""
        df = data.copy()
        
        # Technical indicators
        df['rsi'] = self._calculate_rsi(df['close'])
        df['macd'], df['signal'] = self._calculate_macd(df['close'])
        df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        df['atr'] = self._calculate_atr(df)
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['volatility'] = df['returns'].rolling(20).std()
        
        # Volume features
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        df['price_volume'] = df['close'] * df['volume']
        
        # Momentum features
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            
        # Market microstructure (if tick data available)
        df['hl_ratio'] = (df['high'] - df['low']) / df['close']
        df['co_ratio'] = (df['close'] - df['open']) / df['open']
        
        return df.fillna(0)

    def _calculate_signal_strength(self, features_df: pd.DataFrame) -> float:
        """Calculate signal strength using multiple indicators"""
        latest = features_df.iloc[-1]
        
        # Weighted scoring system
        scores = {
            'trend': 0.3 if latest['macd'] > latest['signal'] else -0.3,
            'momentum': np.tanh(latest['momentum_10']) * 0.25,
            'mean_reversion': 0.2 if latest['rsi'] < 30 else (-0.2 if latest['rsi'] > 70 else 0),
            'volume': 0.15 if latest['volume_ratio'] > 1.5 else 0,
            'volatility': -0.1 if latest['volatility'] > features_df['volatility'].quantile(0.8) else 0.1
        }
        
        return sum(scores.values())

    def _get_market_volatility_threshold(self) -> float:
        """Dynamic threshold adjustment based on market conditions"""
        try:
            # Get VIX or calculate market volatility proxy
            spy_data = self._get_historical_data('SPY', days=20)
            if not spy_data.empty:
                market_vol = spy_data['close'].pct_change().std()
                return min(0.2, market_vol * 10)  # Cap at 0.2
        except:
            pass
        return 0.0
    
    def optimize_portfolio_allocation(self) -> Dict[str, float]:
        """
        Modern Portfolio Theory with risk parity and ML insights
        """
        try:
            symbols = self._select_symbols()
            if len(symbols) < 3:
                return {}
                
            # Get correlation matrix and expected returns
            returns_data = {}
            for symbol in symbols:
                data = self._get_historical_data(symbol, days=60)
                if not data.empty:
                    returns_data[symbol] = data['close'].pct_change().dropna()
            
            if len(returns_data) < 3:
                return {}
                
            returns_df = pd.DataFrame(returns_data).fillna(0)
            
            # Calculate metrics
            expected_returns = returns_df.mean() * 252  # Annualized
            cov_matrix = returns_df.cov() * 252
            
            # Risk parity weights (inverse volatility)
            volatilities = np.sqrt(np.diag(cov_matrix))
            inv_vol_weights = (1 / volatilities) / (1 / volatilities).sum()
            
            # ML-enhanced expected returns adjustment
            ml_adjustments = {}
            for symbol in symbols:
                signal_strength = self._calculate_signal_strength(
                    self._create_ml_features(self._get_historical_data(symbol, days=100))
                )
                ml_adjustments[symbol] = signal_strength * 0.1  # 10% max adjustment
            
            # Combine risk parity with ML insights
            optimized_weights = {}
            total_adjustment = sum(abs(adj) for adj in ml_adjustments.values())
            
            for symbol in symbols:
                base_weight = inv_vol_weights[symbol]
                ml_adj = ml_adjustments.get(symbol, 0)
                
                # Apply ML adjustment with damping
                if total_adjustment > 0:
                    adjusted_weight = base_weight * (1 + ml_adj * 0.5)  # 50% of ML signal
                else:
                    adjusted_weight = base_weight
                    
                optimized_weights[symbol] = max(0.05, min(0.4, adjusted_weight))  # 5-40% bounds
            
            # Normalize weights
            total_weight = sum(optimized_weights.values())
            return {k: v/total_weight for k, v in optimized_weights.items()}
            
        except Exception as e:
            self.logger.error(f"Portfolio optimization failed: {str(e)}")
            return {}
        
    def _create_market_dashboard(self):
        """Create real-time market monitoring dashboard"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'market_status': 'open' if self.is_market_open() else 'closed',
            'portfolio_metrics': {
                'total_positions': len(self.positions),
                'daily_pnl': self.daily_pnl,
                'portfolio_heat': self._calculate_portfolio_heat(),
                'market_regime': self._detect_market_regime()
            },
            'risk_metrics': {
                'var_95': self._calculate_var(),
                'sharpe_ratio': self.metrics.calculate_sharpe_ratio(),
                'max_drawdown': self.metrics.calculate_max_drawdown()
            },
            'active_positions': {
                symbol: {
                    'entry_price': pos.entry_price,
                    'current_pnl': self._calculate_position_pnl(symbol),
                    'stop_loss': pos.stop_loss,
                    'take_profit': pos.take_profit
                } for symbol, pos in self.positions.items()
            }
        }
        
        # Save dashboard data
        with open('logs/dashboard.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        return dashboard_data

    def _calculate_var(self, confidence=0.95) -> float:
        """Calculate Value at Risk"""
        if len(self.metrics.trades) < 10:
            return 0.0
            
        returns = [trade.pnl for trade in self.metrics.trades]
        return np.percentile(returns, (1 - confidence) * 100)

if __name__ == "__main__":
    # Enhanced configuration with additional parameters
    config = {
    # Existing config...
    'API_KEY': os.getenv('APCA_API_KEY_ID', 'your_api_key'),
    'SECRET_KEY': os.getenv('APCA_API_SECRET_KEY', 'your_secret_key'),
    'BASE_URL': os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets'),
    'PAPER_TRADING': True,  # Set to False for live trading
    
    # Risk Management
    'RISK_PCT': 0.02,  # 2% risk per trade (reduced from 5%)
    'MAX_POSITIONS': 3,  # Reduced from 5 for better risk management
    'MAX_DAILY_LOSS': 0.02,  # 2% maximum daily loss
    
    # Strategy Configuration
    'STRATEGY': 'combined',  # 'trend', 'mean_reversion', or 'combined'
    
    # Timing Configuration
    'LOOP_SLEEP': 60,  # Seconds between analysis loops
    
    # Logging Configuration
    'LOG_LEVEL': 'INFO',

    # New ML/Advanced features
    'USE_ML_SIGNALS': True,
    'ML_CONFIDENCE_THRESHOLD': 0.7,
    'PORTFOLIO_OPTIMIZATION': True,
    'ADAPTIVE_RISK_MANAGEMENT': True,
    'MARKET_MICROSTRUCTURE_ANALYSIS': True,
    
    # Enhanced risk parameters
    'USE_KELLY_CRITERION': True,
    'MAX_PORTFOLIO_HEAT': 0.6,  # Max average correlation
    'MIN_LIQUIDITY_SCORE': 0.5,
    
    # Execution parameters
    'SMART_ORDER_ROUTING': True,
    'MAX_SPREAD_PCT': 0.01,  # 1% max spread
    'USE_ADAPTIVE_STOPS': True,
    }
    
    try:
        bot = AlgoTradingBot(config)
        bot.run()
    except Exception as e:
        logging.error(f"Failed to start trading bot: {str(e)}")
        raise

    