"""
Advanced Position Sizing with Multiple Risk Models.

This module implements sophisticated position sizing algorithms including
Kelly Criterion, volatility adjustment, correlation limits, and regime-based sizing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from decimal import Decimal

from core.domain import Symbol, TradingSignal, Portfolio, Position
from core.data.interfaces import IHistoricalDataProvider
from utils.technical_indicators import TechnicalIndicators
from .market_regime import MarketRegimeDetector, MarketRegime


class AdvancedPositionSizer:
    """
    Advanced position sizing with multiple risk models.
    
    Features:
    - Enhanced Kelly Criterion with confidence adjustment
    - Volatility-based position scaling
    - Portfolio correlation limits
    - Market regime adaptation
    - Risk parity considerations
    """
    
    def __init__(
        self,
        data_provider: IHistoricalDataProvider,
        regime_detector: MarketRegimeDetector,
        logger: Optional[logging.Logger] = None
    ):
        self.data_provider = data_provider
        self.regime_detector = regime_detector
        self.logger = logger or logging.getLogger(__name__)
        self.indicators = TechnicalIndicators()
        
        # Position sizing parameters (slightly more aggressive as requested)
        self.base_risk_per_trade = 0.025  # 2.5% base risk per trade (up from 2%)
        self.max_portfolio_risk = 0.12    # 12% max portfolio risk (up from 10%)
        self.max_correlation = 0.65       # 65% max correlation (slightly higher)
        self.target_volatility = 0.20     # 20% target annual volatility
        self.confidence_multiplier = 1.3  # Boost for high-confidence signals
        
        # Kelly Criterion parameters
        self.kelly_lookback_trades = 50   # Use last 50 trades for Kelly calculation
        self.max_kelly_fraction = 0.4     # Cap Kelly at 40% of portfolio
        self.min_kelly_fraction = 0.01    # Minimum 1% position
    
    async def calculate_optimal_position_size(
        self,
        signal: TradingSignal,
        portfolio: Portfolio,
        signal_confidence: float = 0.7
    ) -> int:
        """
        Calculate optimal position size using multiple factors.
        
        Args:
            signal: Trading signal
            portfolio: Current portfolio state
            signal_confidence: Signal confidence score (0-1)
            
        Returns:
            Optimal position size in shares
        """
        try:
            if not signal.price or signal.price <= 0:
                self.logger.warning(f"Invalid signal price for {signal.symbol.ticker}")
                return 0
            
            # Get current market regime for regime-based adjustments
            current_regime = await self.regime_detector.detect_market_regime(signal.symbol)
            regime_params = await self.regime_detector.get_regime_parameters(current_regime)
            
            # Calculate base position size using enhanced Kelly Criterion
            kelly_size = await self._calculate_enhanced_kelly_size(
                signal, portfolio, signal_confidence
            )
            
            # Apply volatility adjustment
            volatility_adjusted_size = await self._apply_volatility_adjustment(
                kelly_size, signal, signal_confidence
            )
            
            # Apply correlation limits
            correlation_adjusted_size = await self._apply_correlation_limits(
                volatility_adjusted_size, signal, portfolio
            )
            
            # Apply regime-based multiplier
            regime_multiplier = regime_params.get("position_size_multiplier", 1.0)
            regime_adjusted_size = int(correlation_adjusted_size * regime_multiplier)
            
            # Apply confidence boost for high-confidence signals
            if signal_confidence > 0.8:
                confidence_boost = 1 + (signal_confidence - 0.8) * self.confidence_multiplier
                regime_adjusted_size = int(regime_adjusted_size * confidence_boost)
            
            # Final safety checks
            final_size = await self._apply_safety_limits(
                regime_adjusted_size, signal, portfolio
            )
            
            self.logger.info(
                f"Position sizing for {signal.symbol.ticker}: "
                f"Kelly={kelly_size}, Vol_adj={volatility_adjusted_size}, "
                f"Corr_adj={correlation_adjusted_size}, Final={final_size} "
                f"(confidence={signal_confidence:.2f}, regime={current_regime.value})"
            )
            
            return max(0, final_size)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {signal.symbol.ticker}: {e}")
            return 0
    
    async def _calculate_enhanced_kelly_size(
        self,
        signal: TradingSignal,
        portfolio: Portfolio,
        signal_confidence: float
    ) -> int:
        """Calculate position size using enhanced Kelly Criterion."""
        try:
            # Get historical performance data for Kelly calculation
            win_rate, avg_win, avg_loss = await self._get_strategy_performance(
                signal.strategy_name
            )
            
            if win_rate <= 0 or avg_win <= 0 or avg_loss <= 0:
                # Use default conservative estimates for new strategies
                win_rate = 0.55  # Slightly optimistic default
                avg_win = 0.03   # 3% average win
                avg_loss = 0.02  # 2% average loss
            
            # Adjust win rate based on signal confidence
            adjusted_win_rate = win_rate * (0.7 + 0.3 * signal_confidence)
            
            # Calculate Kelly fraction: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
            if avg_loss > 0:
                b = avg_win / avg_loss
                p = adjusted_win_rate
                q = 1 - p
                kelly_fraction = (b * p - q) / b
            else:
                kelly_fraction = 0.1  # Conservative default
            
            # Cap Kelly fraction to prevent over-leverage
            kelly_fraction = max(
                self.min_kelly_fraction,
                min(kelly_fraction, self.max_kelly_fraction)
            )
            
            # Convert to position size
            portfolio_value = portfolio.equity
            max_risk_amount = portfolio_value * Decimal(str(kelly_fraction))
            
            # Calculate shares based on risk amount and expected stop loss
            expected_stop_distance = Decimal(str(self.base_risk_per_trade))
            max_position_value = max_risk_amount / expected_stop_distance
            
            shares = int(max_position_value / signal.price)
            
            return shares
            
        except Exception as e:
            self.logger.error(f"Error in Kelly calculation: {e}")
            # Fallback to simple percentage-based sizing
            portfolio_value = portfolio.equity
            risk_amount = portfolio_value * Decimal(str(self.base_risk_per_trade))
            return int(risk_amount / signal.price)
    
    async def _apply_volatility_adjustment(
        self,
        base_size: int,
        signal: TradingSignal,
        signal_confidence: float
    ) -> int:
        """Apply volatility-based position size adjustment."""
        try:
            # Get symbol volatility
            symbol_volatility = await self._calculate_symbol_volatility(signal.symbol)
            
            if symbol_volatility is None or symbol_volatility <= 0:
                return base_size  # No adjustment if can't calculate volatility
            
            # Calculate volatility adjustment factor
            # Target: reduce size for high volatility, increase for low volatility
            volatility_ratio = symbol_volatility / self.target_volatility
            
            # More aggressive adjustment based on confidence
            if signal_confidence > 0.7:
                # High confidence: less conservative on volatility
                volatility_adjustment = 1 / (0.5 + 0.5 * volatility_ratio)
            else:
                # Low confidence: more conservative
                volatility_adjustment = 1 / (0.3 + 0.7 * volatility_ratio)
            
            # Apply bounds to prevent extreme adjustments
            volatility_adjustment = max(0.3, min(volatility_adjustment, 2.0))
            
            adjusted_size = int(base_size * volatility_adjustment)
            
            self.logger.debug(
                f"Volatility adjustment for {signal.symbol.ticker}: "
                f"vol={symbol_volatility:.3f}, ratio={volatility_ratio:.2f}, "
                f"adjustment={volatility_adjustment:.2f}"
            )
            
            return adjusted_size
            
        except Exception as e:
            self.logger.error(f"Error in volatility adjustment: {e}")
            return base_size
    
    async def _apply_correlation_limits(
        self,
        base_size: int,
        signal: TradingSignal,
        portfolio: Portfolio
    ) -> int:
        """Apply correlation-based position size limits."""
        try:
            if not portfolio.positions:
                return base_size  # No correlation limits if no existing positions
            
            # Calculate correlation with existing positions
            existing_symbols = [Symbol(pos.symbol.ticker) for pos in portfolio.positions.values()]
            portfolio_correlation = await self._calculate_portfolio_correlation(
                signal.symbol, existing_symbols
            )
            
            if portfolio_correlation is None:
                return base_size
            
            # Apply correlation adjustment
            if portfolio_correlation > self.max_correlation:
                # High correlation: reduce position size
                correlation_penalty = portfolio_correlation / self.max_correlation
                correlation_adjustment = 1 / correlation_penalty
            else:
                # Low correlation: allow normal or slightly increased size
                correlation_adjustment = 1.0 + (self.max_correlation - portfolio_correlation) * 0.2
            
            # Apply bounds
            correlation_adjustment = max(0.2, min(correlation_adjustment, 1.5))
            
            adjusted_size = int(base_size * correlation_adjustment)
            
            self.logger.debug(
                f"Correlation adjustment for {signal.symbol.ticker}: "
                f"portfolio_corr={portfolio_correlation:.3f}, "
                f"adjustment={correlation_adjustment:.2f}"
            )
            
            return adjusted_size
            
        except Exception as e:
            self.logger.error(f"Error in correlation adjustment: {e}")
            return base_size
    
    async def _apply_safety_limits(
        self,
        base_size: int,
        signal: TradingSignal,
        portfolio: Portfolio
    ) -> int:
        """Apply final safety limits to position size."""
        try:
            # Check buying power
            available_cash = portfolio.cash
            required_cash = Decimal(str(base_size)) * signal.price
            
            if required_cash > available_cash:
                # Reduce size to fit available cash
                max_affordable_shares = int(available_cash / signal.price)
                base_size = min(base_size, max_affordable_shares)
            
            # Check maximum position size as percentage of portfolio
            portfolio_value = portfolio.equity
            position_value = Decimal(str(base_size)) * signal.price
            position_percentage = float(position_value / portfolio_value) if portfolio_value > 0 else 0
            
            max_position_percentage = 0.25  # 25% max position size (more aggressive)
            if position_percentage > max_position_percentage:
                max_allowed_shares = int(
                    float(portfolio_value) * max_position_percentage / float(signal.price)
                )
                base_size = min(base_size, max_allowed_shares)
            
            # Minimum position size (avoid tiny positions)
            min_position_value = 500  # $500 minimum
            min_shares = int(min_position_value / float(signal.price))
            
            if base_size < min_shares:
                if float(portfolio.cash) >= min_position_value:
                    base_size = min_shares  # Increase to minimum viable size
                else:
                    base_size = 0  # Skip if can't meet minimum
            
            return base_size
            
        except Exception as e:
            self.logger.error(f"Error applying safety limits: {e}")
            return base_size
    
    async def _calculate_symbol_volatility(
        self,
        symbol: Symbol,
        period_days: int = 30
    ) -> Optional[float]:
        """Calculate symbol's realized volatility."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days + 10)
            
            data = await self.data_provider.get_bars_dataframe(
                symbol,
                timeframe="1D",
                start_date=start_date,
                end_date=end_date
            )
            
            if data.empty or len(data) < period_days:
                return None
            
            # Calculate daily returns
            returns = data['close'].pct_change().dropna()
            
            # Annualized volatility
            volatility = returns.std() * np.sqrt(252)
            
            return float(volatility)
            
        except Exception as e:
            self.logger.debug(f"Error calculating volatility for {symbol.ticker}: {e}")
            return None
    
    async def _calculate_portfolio_correlation(
        self,
        new_symbol: Symbol,
        existing_symbols: List[Symbol],
        period_days: int = 60
    ) -> Optional[float]:
        """Calculate correlation between new symbol and existing portfolio."""
        try:
            if not existing_symbols:
                return 0.0
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days + 10)
            
            # Get data for all symbols
            all_symbols = [new_symbol] + existing_symbols
            returns_data = {}
            
            for symbol in all_symbols:
                data = await self.data_provider.get_bars_dataframe(
                    symbol,
                    timeframe="1D",
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not data.empty:
                    returns = data['close'].pct_change().dropna()
                    returns_data[symbol.ticker] = returns
            
            if len(returns_data) < 2:
                return None
            
            # Create correlation matrix
            returns_df = pd.DataFrame(returns_data)
            correlation_matrix = returns_df.corr()
            
            # Calculate average correlation between new symbol and existing symbols
            new_symbol_correlations = []
            for existing_symbol in existing_symbols:
                if (new_symbol.ticker in correlation_matrix.index and 
                    existing_symbol.ticker in correlation_matrix.columns):
                    corr = correlation_matrix.loc[new_symbol.ticker, existing_symbol.ticker]
                    if not pd.isna(corr):
                        new_symbol_correlations.append(abs(corr))  # Use absolute correlation
            
            if new_symbol_correlations:
                avg_correlation = np.mean(new_symbol_correlations)
                return float(avg_correlation)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error calculating portfolio correlation: {e}")
            return None
    
    async def _get_strategy_performance(
        self,
        strategy_name: str
    ) -> Tuple[float, float, float]:
        """Get historical performance metrics for strategy."""
        try:
            # This would typically query a performance database
            # For now, return strategy-specific defaults based on your current performance
            
            strategy_defaults = {
                "trend_following": (0.58, 0.035, 0.022),    # 58% win rate, 3.5% avg win, 2.2% avg loss
                "mean_reversion": (0.65, 0.025, 0.018),     # 65% win rate, 2.5% avg win, 1.8% avg loss  
                "combined": (0.62, 0.030, 0.020),           # 62% win rate, 3.0% avg win, 2.0% avg loss
                "momentum": (0.55, 0.040, 0.025),           # 55% win rate, 4.0% avg win, 2.5% avg loss
            }
            
            return strategy_defaults.get(strategy_name, (0.55, 0.03, 0.02))
            
        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {e}")
            return (0.55, 0.03, 0.02)  # Conservative defaults
    
    async def calculate_portfolio_heat(self, portfolio: Portfolio) -> float:
        """Calculate current portfolio correlation heat."""
        try:
            if len(portfolio.positions) < 2:
                return 0.0
            
            symbols = [Symbol(pos.symbol.ticker) for pos in portfolio.positions.values()]
            
            # Get returns for all positions
            returns_data = {}
            for symbol in symbols:
                try:
                    data = await self.data_provider.get_bars_dataframe(
                        symbol,
                        timeframe="1D",
                        limit=60
                    )
                    if not data.empty:
                        returns = data['close'].pct_change().dropna()
                        returns_data[symbol.ticker] = returns
                except:
                    continue
            
            if len(returns_data) < 2:
                return 0.0
            
            # Calculate correlation matrix
            returns_df = pd.DataFrame(returns_data)
            correlation_matrix = returns_df.corr()
            
            # Calculate average correlation (portfolio heat)
            correlations = []
            for i in range(len(correlation_matrix)):
                for j in range(i + 1, len(correlation_matrix)):
                    corr = correlation_matrix.iloc[i, j]
                    if not pd.isna(corr):
                        correlations.append(abs(corr))
            
            return np.mean(correlations) if correlations else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio heat: {e}")
            return 0.0