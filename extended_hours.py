from datetime import datetime, time, timezone
from typing import Dict, List, Optional, Tuple
import pytz

class ExtendedHoursTrading:
    """Handle pre-market and after-hours trading with special rules"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.eastern = pytz.timezone('US/Eastern')
        
        # Trading session times (ET)
        self.sessions = {
            'pre_market': {'start': time(4, 0), 'end': time(9, 30)},
            'regular': {'start': time(9, 30), 'end': time(16, 0)},
            'after_hours': {'start': time(16, 0), 'end': time(20, 0)}
        }
        
        # Extended hours configuration
        self.extended_config = {
            'pre_market': {
                'max_position_size_pct': 0.3,  # 30% of regular size
                'allowed_symbols': [],  # Will be populated with liquid symbols
                'min_volume': 50000,
                'max_spread_pct': 0.02,  # 2% max spread
                'use_limit_orders_only': True
            },
            'after_hours': {
                'max_position_size_pct': 0.2,  # 20% of regular size
                'allowed_symbols': [],
                'min_volume': 30000,
                'max_spread_pct': 0.03,  # 3% max spread
                'use_limit_orders_only': True
            }
        }
        
    def get_current_session(self) -> str:
        """Determine current trading session"""
        now = datetime.now(self.eastern).time()
        
        for session_name, times in self.sessions.items():
            if times['start'] <= now < times['end']:
                return session_name
                
        return 'closed'
        
    def is_extended_hours(self) -> bool:
        """Check if currently in extended hours"""
        session = self.get_current_session()
        return session in ['pre_market', 'after_hours']
        
    def update_liquid_symbols(self):
        """Update list of symbols suitable for extended hours trading"""
        # High-liquidity symbols that trade well in extended hours
        liquid_symbols = [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA',
            'SPY', 'QQQ', 'IWM', 'DIA', 'AMD', 'INTC', 'BAC', 'JPM'
        ]
        
        self.extended_config['pre_market']['allowed_symbols'] = liquid_symbols
        self.extended_config['after_hours']['allowed_symbols'] = liquid_symbols
        
    def can_trade_symbol(self, symbol: str) -> bool:
        """Check if symbol can be traded in current session"""
        session = self.get_current_session()
        
        if session == 'regular':
            return True
        elif session in ['pre_market', 'after_hours']:
            return symbol in self.extended_config[session]['allowed_symbols']
        else:
            return False
            
    def get_adjusted_position_size(self, symbol: str, regular_size: int) -> int:
        """Adjust position size for extended hours"""
        session = self.get_current_session()
        
        if session == 'regular':
            return regular_size
        elif session in ['pre_market', 'after_hours']:
            if not self.can_trade_symbol(symbol):
                return 0
            size_pct = self.extended_config[session]['max_position_size_pct']
            return int(regular_size * size_pct)
        else:
            return 0
            
    def validate_extended_hours_order(self, symbol: str, order_type: str) -> Tuple[bool, str]:
        """Validate order for extended hours trading"""
        session = self.get_current_session()
        
        if session == 'regular':
            return True, "Regular hours - all orders allowed"
            
        if session == 'closed':
            return False, "Market is closed"
            
        if session in ['pre_market', 'after_hours']:
            config = self.extended_config[session]
            
            # Check if symbol is allowed
            if symbol not in config['allowed_symbols']:
                return False, f"{symbol} not allowed in {session}"
                
            # Check order type
            if config['use_limit_orders_only'] and order_type != 'limit':
                return False, f"Only limit orders allowed in {session}"
                
            # Check spread
            quote = self.bot.get_real_time_data(symbol)
            if not quote.empty:
                spread_pct = (quote['ask'].iloc[0] - quote['bid'].iloc[0]) / quote['ask'].iloc[0]
                if spread_pct > config['max_spread_pct']:
                    return False, f"Spread too wide: {spread_pct:.2%}"
                    
            return True, "Extended hours validation passed"
            
        return False, "Unknown session"

class GapAnalyzer:
    """Analyze overnight gaps for trading opportunities"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.gap_threshold = 0.02  # 2% gap to be significant
        
    def analyze_gaps(self, symbols: List[str]) -> Dict[str, Dict]:
        """Analyze overnight gaps for given symbols"""
        gaps = {}
        
        for symbol in symbols:
            try:
                # Get previous close and current pre-market price
                prev_close = self._get_previous_close(symbol)
                current_price = self._get_pre_market_price(symbol)
                
                if prev_close and current_price:
                    gap_pct = (current_price - prev_close) / prev_close
                    
                    if abs(gap_pct) >= self.gap_threshold:
                        gaps[symbol] = {
                            'gap_pct': gap_pct,
                            'prev_close': prev_close,
                            'current_price': current_price,
                            'gap_type': 'up' if gap_pct > 0 else 'down',
                            'volume': self._get_pre_market_volume(symbol)
                        }
                        
            except Exception as e:
                self.bot.logger.error(f"Gap analysis failed for {symbol}: {str(e)}")
                
        return gaps
        
    def _get_previous_close(self, symbol: str) -> Optional[float]:
        """Get previous day's closing price"""
        try:
            bars = self.bot._get_historical_data(symbol, days=2)
            if not bars.empty:
                return bars.iloc[-2]['close']
        except:
            pass
        return None
        
    def _get_pre_market_price(self, symbol: str) -> Optional[float]:
        """Get current pre-market price"""
        try:
            quote = self.bot.get_real_time_data(symbol)
            if not quote.empty:
                return (quote['bid'].iloc[0] + quote['ask'].iloc[0]) / 2
        except:
            pass
        return None

class ExtendedHoursStrategy:
    """Specialized strategies for extended hours trading"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.gap_analyzer = GapAnalyzer(bot_instance)
        
    def gap_fade_strategy(self, symbol: str, gap_info: Dict) -> Optional[str]:
        """Fade extreme gaps in pre-market"""
        gap_pct = gap_info['gap_pct']
        
        # Fade large gaps (bet on mean reversion)
        if gap_pct > 0.05:  # 5% up gap
            # Look for weakness to short
            return 'sell'
        elif gap_pct < -0.05:  # 5% down gap
            # Look for strength to buy
            return 'buy'
            
        return None
        
    def news_driven_strategy(self, symbol: str) -> Optional[str]:
        """Trade based on pre-market news and sentiment"""
        # This would integrate with news APIs
        # Placeholder for news-based logic
        return None
        
    def earnings_play_strategy(self, symbol: str) -> Optional[str]:
        """Trade earnings announcements in extended hours"""
        # Check if symbol has earnings today
        # Implement earnings calendar integration
        return None