# Add these methods to your existing algo_trading_bot_v5.py file

# ADD THIS METHOD to the AlgoTradingBot class to fix the missing _pre_trade_risk_check error:

def _pre_trade_risk_check(self, symbol: str, signal: str) -> bool:
    """
    CRITICAL FIX: Pre-trade risk check that was missing
    """
    try:
        # Check daily loss limit
        if self.daily_pnl < -self.max_daily_loss * (self.initial_equity or 50000):
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
            
        return True
        
    except Exception as e:
        self.logger.error(f"Pre-trade risk check failed: {e}")
        return False

# ADD THIS METHOD to fix the execution strategy determination:

def _determine_execution_strategy(self, symbol: str, quote_data: pd.DataFrame) -> str:
    """Determine optimal execution strategy"""
    try:
        if quote_data.empty:
            return 'limit'  # Default to safer limit orders
            
        spread_pct = (quote_data['ask'].iloc[0] - quote_data['bid'].iloc[0]) / quote_data['ask'].iloc[0]
        
        # Use market orders for tight spreads, limit orders for wide spreads
        if spread_pct < 0.005:  # 0.5% spread
            return 'market'
        else:
            return 'limit'
            
    except Exception as e:
        self.logger.debug(f"Execution strategy determination failed: {e}")
        return 'limit'  # Default to safer limit orders

# ADD THIS METHOD to fix smart limit price calculation:

def _calculate_smart_limit_price(self, symbol: str, quote_data: pd.DataFrame, signal: str) -> float:
    """Calculate intelligent limit price"""
    try:
        if quote_data.empty:
            raise ValueError("Empty quote data")
            
        bid = quote_data['bid'].iloc[0]
        ask = quote_data['ask'].iloc[0]
        
        if signal == 'buy':
            # Buy at slightly above bid but below ask
            return bid + (ask - bid) * 0.3  # 30% through spread
        else:
            # Sell at slightly below ask but above bid
            return ask - (ask - bid) * 0.3  # 30% through spread
            
    except Exception as e:
        self.logger.debug(f"Smart limit price calculation failed: {e}")
        # Fallback to mid-price
        try:
            return (quote_data['bid'].iloc[0] + quote_data['ask'].iloc[0]) / 2
        except:
            # Ultimate fallback - use a reasonable price based on recent data
            try:
                recent_data = self._get_historical_data(symbol, days=1)
                if not recent_data.empty:
                    return recent_data['close'].iloc[-1]
                else:
                    return 100.0  # Emergency fallback price
            except:
                return 100.0

# ADD THIS METHOD to fix adaptive stop loss calculation:

def _calculate_adaptive_stop_loss(self, symbol: str, entry_price: float, signal: str) -> float:
    """Calculate adaptive stop loss based on volatility and support/resistance"""
    try:
        data = self._get_historical_data(symbol, days=30)
        if data.empty:
            # Fallback to percentage-based stop
            return entry_price * (0.97 if signal == 'buy' else 1.03)
            
        # ATR-based stop
        atr = self._calculate_atr(data)
        if atr.empty:
            return entry_price * (0.97 if signal == 'buy' else 1.03)
            
        atr_value = atr.iloc[-1]
        atr_multiplier = 2.0
        
        # Support/resistance levels
        recent_lows = data['low'].tail(20).min()
        recent_highs = data['high'].tail(20).max()
        
        if signal == 'buy':
            atr_stop = entry_price - (atr_value * atr_multiplier)
            support_stop = recent_lows * 0.99
            return max(atr_stop, support_stop, entry_price * 0.95)  # Never more than 5% loss
        else:
            atr_stop = entry_price + (atr_value * atr_multiplier)
            resistance_stop = recent_highs * 1.01
            return min(atr_stop, resistance_stop, entry_price * 1.05)  # Never more than 5% loss
            
    except Exception as e:
        self.logger.debug(f"Adaptive stop loss calculation failed: {e}")
        return entry_price * (0.97 if signal == 'buy' else 1.03)

# ADD THIS METHOD to fix adaptive take profit calculation:

def _calculate_adaptive_take_profit(self, symbol: str, entry_price: float, signal: str) -> float:
    """Calculate adaptive take profit based on volatility"""
    try:
        data = self._get_historical_data(symbol, days=20)
        if not data.empty:
            atr = self._calculate_atr(data)
            if not atr.empty:
                atr_value = atr.iloc[-1]
                atr_multiplier = 3.0  # 3x ATR for take profit
                
                if signal == 'buy':
                    return entry_price + (atr_value * atr_multiplier)
                else:
                    return entry_price - (atr_value * atr_multiplier)
                    
        # Fallback to percentage-based
        multiplier = 1.04 if signal == 'buy' else 0.96  # 4% target
        return entry_price * multiplier
        
    except Exception as e:
        self.logger.debug(f"Adaptive take profit calculation failed: {e}")
        multiplier = 1.04 if signal == 'buy' else 0.96
        return entry_price * multiplier

# ADD THIS METHOD to enhance the _get_historical_data with better error handling:

def _get_historical_data_enhanced(self, symbol: str, days: int) -> pd.DataFrame:
    """Enhanced historical data retrieval with fallback mechanisms"""
    try:
        # Try the original method first
        data = self._get_historical_data(symbol, days)
        if not data.empty:
            return data
            
        # If that fails, try with fewer days
        if days > 30:
            self.logger.debug(f"Retrying {symbol} with fewer days")
            return self._get_historical_data(symbol, 30)
            
        # If still failing, try yfinance as backup
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            
            if not hist.empty:
                # Convert to expected format
                hist.reset_index(inplace=True)
                hist.columns = [col.lower() for col in hist.columns]
                self.logger.debug(f"Using yfinance backup for {symbol}")
                return hist
                
        except Exception as yf_error:
            self.logger.debug(f"yfinance backup failed for {symbol}: {yf_error}")
            
        return pd.DataFrame()
        
    except Exception as e:
        self.logger.debug(f"Enhanced historical data fetch failed for {symbol}: {e}")
        return pd.DataFrame()

# ADD THIS METHOD to improve symbol selection with better filtering:

def _select_symbols_enhanced(self) -> List[str]:
    """Enhanced symbol selection with better error handling and fallback"""
    try:
        # Base universe of liquid stocks (organized by sector for better diversification)
        tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN', 'TSLA']
        finance_symbols = ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C']
        healthcare_symbols = ['JNJ', 'UNH', 'PFE', 'ABBV', 'LLY', 'BMY']
        consumer_symbols = ['WMT', 'HD', 'NKE', 'DIS', 'COST', 'SBUX']
        industrial_symbols = ['MMM', 'BA', 'CAT', 'HON', 'LMT', 'RTX']
        
        all_symbols = tech_symbols + finance_symbols + healthcare_symbols + consumer_symbols + industrial_symbols
        
        # Filter based on volume and avoid problematic symbols
        filtered_symbols = []
        max_symbols_to_check = 50  # Limit to prevent API overuse
        
        for symbol in all_symbols[:max_symbols_to_check]:
            try:
                # Quick volume check using recent data
                data = self._get_historical_data(symbol, days=5)
                if not data.empty and len(data) >= 3:
                    avg_volume = data['volume'].mean()
                    recent_price = data['close'].iloc[-1]
                    
                    # Filter criteria
                    if (avg_volume > 500000 and  # Min 500K average volume
                        recent_price > 10 and     # Avoid penny stocks
                        recent_price < 1000):     # Avoid extreme prices
                        filtered_symbols.append(symbol)
                        
                    # Limit number of symbols to manage API calls
                    if len(filtered_symbols) >= 30:
                        break
                        
            except Exception as e:
                self.logger.debug(f"Symbol filtering error for {symbol}: {e}")
                continue
                
        if not filtered_symbols:
            # Fallback to most liquid symbols
            filtered_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'UNH', 'HD']
            
        self.logger.info(f"Enhanced symbol selection: {len(filtered_symbols)} symbols")
        return filtered_symbols
        
    except Exception as e:
        self.logger.error(f"Enhanced symbol selection failed: {e}")
        # Ultimate fallback
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

# ADD THIS METHOD to handle API failures gracefully:

def _handle_api_failure(self, operation: str, symbol: str = None, error: Exception = None) -> bool:
    """Handle API failures gracefully and determine if operation should continue"""
    try:
        error_msg = str(error) if error else "Unknown error"
        context = f" for {symbol}" if symbol else ""
        
        # Log the failure
        self.logger.warning(f"API failure in {operation}{context}: {error_msg}")
        
        # Check for specific error types
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            self.logger.warning("Rate limit detected - implementing backoff")
            time.sleep(60)  # Wait 1 minute for rate limits
            return True  # Retry allowed
            
        elif "authentication" in error_msg.lower() or "401" in error_msg:
            self.logger.error("Authentication error - check API keys")
            return False  # Don't retry auth errors
            
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            self.logger.warning("Network error - will retry")
            time.sleep(5)  # Short wait for network issues
            return True  # Retry allowed
            
        elif "empty" in error_msg.lower() or "no data" in error_msg.lower():
            self.logger.debug(f"No data available{context}")
            return False  # Don't retry for missing data
            
        else:
            # Unknown error - allow limited retries
            return True
            
    except Exception as e:
        self.logger.error(f"Error in API failure handler: {e}")
        return False

# ADD THIS METHOD for better performance monitoring:

def _update_performance_metrics(self):
    """Update comprehensive performance metrics"""
    try:
        current_time = datetime.now()
        
        # Calculate daily metrics
        today_trades = [t for t in self.metrics.trades 
                       if hasattr(t, 'exit_time') and t.exit_time.date() == current_time.date()]
        
        daily_pnl = sum(t.pnl for t in today_trades)
        daily_wins = sum(1 for t in today_trades if t.pnl > 0)
        daily_losses = sum(1 for t in today_trades if t.pnl <= 0)
        
        # Update performance state
        performance_update = {
            'last_update': current_time.isoformat(),
            'daily_trades': len(today_trades),
            'daily_pnl': daily_pnl,
            'daily_win_rate': (daily_wins / max(1, len(today_trades))) * 100,
            'total_trades': len(self.metrics.trades),
            'overall_win_rate': self.metrics.calculate_win_rate(),
            'current_positions': len(self.positions),
            'account_equity': 0  # Will be updated separately
        }
        
        # Safely get account equity
        try:
            account_info = self.get_account_info()
            performance_update['account_equity'] = account_info.get('equity', 0)
        except Exception as e:
            self.logger.debug(f"Could not get account equity: {e}")
            
        # Save performance metrics
        if not hasattr(self, 'performance_history'):
            self.performance_history = []
            
        self.performance_history.append(performance_update)
        
        # Keep only last 100 records
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
            
        return performance_update
        
    except Exception as e:
        self.logger.error(f"Performance metrics update failed: {e}")
        return {}

# ADD THIS METHOD to create a robust fallback trading mode:

def _enable_fallback_mode(self):
    """Enable fallback trading mode when APIs are failing"""
    try:
        self.logger.warning("Enabling fallback trading mode")
        
        # Store original settings
        if not hasattr(self, '_original_settings'):
            self._original_settings = {
                'RISK_PCT': self.config.get('RISK_PCT', 0.02),
                'MAX_POSITIONS': self.config.get('MAX_POSITIONS', 3),
                'USE_ML_SIGNALS': self.config.get('USE_ML_SIGNALS', False)
            }
        
        # Apply conservative fallback settings
        self.config.update({
            'RISK_PCT': 0.01,  # Reduce risk to 1%
            'MAX_POSITIONS': 1,  # Only 1 position at a time
            'USE_ML_SIGNALS': False,  # Disable ML features
            'STRATEGY': 'trend'  # Use simple trend following only
        })
        
        # Mark fallback mode active
        self.fallback_mode = True
        
        self.logger.info("Fallback mode enabled - conservative trading settings active")
        
    except Exception as e:
        self.logger.error(f"Failed to enable fallback mode: {e}")

def _disable_fallback_mode(self):
    """Disable fallback mode and restore normal settings"""
    try:
        if hasattr(self, '_original_settings') and self.fallback_mode:
            self.config.update(self._original_settings)
            self.fallback_mode = False
            self.logger.info("Fallback mode disabled - normal trading settings restored")
            
    except Exception as e:
        self.logger.error(f"Failed to disable fallback mode: {e}")

# ADD THIS to replace your existing execute_trade method with enhanced version:

def execute_trade_enhanced(self, symbol: str, signal: str):
    """
    Enhanced trade execution that replaces the original execute_trade method
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
        
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Get market data with retries
            quote_data = self.get_real_time_data(symbol)
            if quote_data.empty:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Quote data failed for {symbol}, attempt {attempt + 1}")
                    time.sleep(2)
                    continue
                else:
                    self.logger.error(f"Failed to get quote data for {symbol} after {max_retries} attempts")
                    return
                    
            # Liquidity analysis
            spread_pct = (quote_data['ask'].iloc[0] - quote_data['bid'].iloc[0]) / quote_data['ask'].iloc[0]
            if spread_pct > 0.02:  # 2% spread threshold
                self.logger.warning(f"Wide spread for {symbol}: {spread_pct:.2%}")
                return
                
            # Execution strategy
            execution_strategy = self._determine_execution_strategy(symbol, quote_data)
            
            # Position sizing
            base_price = quote_data['ask'].iloc[0] if signal == 'buy' else quote_data['bid'].iloc[0]
            position_size = self.calculate_position_size(symbol, base_price)
            
            if position_size <= 0:
                self.logger.warning(f"Invalid position size for {symbol}: {position_size}")
                return
                
            # Create and submit order
            if execution_strategy == 'market':
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=position_size,
                    side=OrderSide.BUY if signal == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.IOC
                )
                execution_price = base_price
            else:
                limit_price = self._calculate_smart_limit_price(symbol, quote_data, signal)
                order = LimitOrderRequest(
                    symbol=symbol,
                    qty=position_size,
                    side=OrderSide.BUY if signal == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )
                execution_price = limit_price
                
            # Submit order
            submitted_order = self.trade_client.submit_order(order)
            
            # Create position tracking
            position = Position(
                symbol=symbol,
                entry_price=execution_price,
                quantity=position_size,
                order_id=submitted_order.id,
                timestamp=datetime.now(),
                strategy=f"{self.config['STRATEGY']}_enhanced",
                stop_loss=self._calculate_adaptive_stop_loss(symbol, execution_price, signal),
                take_profit=self._calculate_adaptive_take_profit(symbol, execution_price, signal)
            )
            
            self.positions[symbol] = position
            
            # Logging
            trade_logger = logging.getLogger('AlgoTradingBot.trades')
            trade_logger.info(f"ENHANCED_TRADE,{symbol},{signal},{position_size},{execution_price:.2f},{execution_strategy}")
            
            self.logger.info(f"Enhanced trade executed: {signal} {position_size} {symbol} @ ${execution_price:.2f}")
            
            # Success - break retry loop
            break
            
        except Exception as e:
            if not self._handle_api_failure("execute_trade", symbol, e):
                break  # Don't retry for certain errors
                
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                self.logger.warning(f"Trade execution attempt {attempt + 1} failed, retrying in {wait_time}s")
                time.sleep(wait_time)
            else:
                self.logger.error(f"Enhanced trade execution failed for {symbol} after {max_retries} attempts: {e}")

# Method to integrate these fixes into your existing bot:
def apply_enhanced_fixes(bot_instance):
    """
    Apply all enhanced fixes to an existing AlgoTradingBot instance
    Call this after creating your bot to add missing methods
    """
    import types
    
    # Add missing methods
    bot_instance._pre_trade_risk_check = types.MethodType(_pre_trade_risk_check, bot_instance)
    bot_instance._determine_execution_strategy = types.MethodType(_determine_execution_strategy, bot_instance)
    bot_instance._calculate_smart_limit_price = types.MethodType(_calculate_smart_limit_price, bot_instance)
    bot_instance._calculate_adaptive_stop_loss = types.MethodType(_calculate_adaptive_stop_loss, bot_instance)
    bot_instance._calculate_adaptive_take_profit = types.MethodType(_calculate_adaptive_take_profit, bot_instance)
    bot_instance._handle_api_failure = types.MethodType(_handle_api_failure, bot_instance)
    bot_instance._enable_fallback_mode = types.MethodType(_enable_fallback_mode, bot_instance)
    bot_instance._disable_fallback_mode = types.MethodType(_disable_fallback_mode, bot_instance)
    bot_instance.execute_trade_enhanced = types.MethodType(execute_trade_enhanced, bot_instance)
    
    # Initialize fallback mode flag
    bot_instance.fallback_mode = False
    
    print("✅ Enhanced fixes applied to bot instance")