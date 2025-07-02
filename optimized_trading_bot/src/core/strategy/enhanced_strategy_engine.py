"""
Enhanced Strategy Engine with Advanced Features.

This module integrates all the advanced trading features including market regime
detection, signal confidence analysis, and advanced position sizing into a
unified strategy engine.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from core.domain import Symbol, TradingSignal, SignalType, Portfolio, Position
from core.data.interfaces import IHistoricalDataProvider, IQuoteProvider
from utils.technical_indicators import TechnicalIndicators
from .market_regime import MarketRegimeDetector, MarketRegime
from .signal_analyzer import SignalConfidenceAnalyzer
from .advanced_position_sizing import AdvancedPositionSizer
from .interfaces import IStrategy


class EnhancedStrategyEngine(IStrategy):
    """
    Enhanced strategy engine combining multiple advanced features.
    
    Features:
    - Market regime adaptive parameters
    - Signal confidence filtering
    - Advanced position sizing
    - Multi-strategy signal combination
    - Risk-adjusted signal generation
    """
    
    def __init__(
        self,
        data_provider: IHistoricalDataProvider,
        quote_provider: IQuoteProvider,
        logger: Optional[logging.Logger] = None
    ):
        self.data_provider = data_provider
        self.quote_provider = quote_provider
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize advanced components
        self.regime_detector = MarketRegimeDetector(data_provider, logger)
        self.signal_analyzer = SignalConfidenceAnalyzer(
            data_provider, quote_provider, self.regime_detector, logger
        )
        self.position_sizer = AdvancedPositionSizer(
            data_provider, self.regime_detector, logger
        )
        self.indicators = TechnicalIndicators()
        
        # Strategy configuration (optimized for paper trading)
        self.config = {
            "min_signal_confidence": 0.50,  # 50% minimum confidence for more trades
            "max_positions": 6,              # Increased for more opportunities
            "enable_regime_adaptation": True,
            "enable_confidence_filtering": True,
            "enable_advanced_sizing": True,
            "strategy_weights": {
                "trend_following": 0.4,
                "mean_reversion": 0.35,
                "momentum": 0.25
            }
        }
    
    @property
    def strategy_type(self):
        """Return strategy type."""
        from ..domain import StrategyType
        return StrategyType.COMBINED
    
    @property
    def name(self) -> str:
        """Return strategy name."""
        return "enhanced_combined_strategy"
    
    async def generate_signal(
        self,
        symbol: Symbol,
        current_data: Optional[pd.DataFrame] = None
    ) -> Optional[TradingSignal]:
        """
        Generate enhanced trading signal with confidence analysis.
        
        Args:
            symbol: Symbol to analyze
            current_data: Optional pre-loaded data
            
        Returns:
            Enhanced trading signal or None
        """
        try:
            # Get market data
            if current_data is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=100)
                current_data = await self.data_provider.get_bars_dataframe(
                    symbol,
                    timeframe="1D",
                    start_date=start_date,
                    end_date=end_date
                )
            
            if current_data.empty or len(current_data) < 50:
                self.logger.debug(f"Insufficient data for {symbol.ticker}")
                return None
            
            # Get current market regime
            current_regime = await self.regime_detector.detect_market_regime(symbol)
            regime_params = await self.regime_detector.get_regime_parameters(current_regime)
            
            # Generate multi-strategy signals
            signals = await self._generate_multi_strategy_signals(
                symbol, current_data, regime_params
            )
            
            if not signals:
                return None
            
            # Check if single strategy signals are enabled
            enable_single_strategy = self.config.get("enable_single_strategy_trades", False)
            
            # Combine signals using weighted voting
            combined_signal = await self._combine_signals(signals, regime_params, enable_single_strategy)
            
            if not combined_signal:
                return None
            
            # Analyze signal confidence
            if self.config["enable_confidence_filtering"]:
                confidence = await self.signal_analyzer.analyze_signal_confidence(
                    combined_signal, current_data
                )
                combined_signal.confidence = confidence
                
                # Filter by minimum confidence
                if confidence < self.config["min_signal_confidence"]:
                    self.logger.debug(
                        f"Signal filtered out for {symbol.ticker}: "
                        f"confidence {confidence:.3f} < {self.config['min_signal_confidence']}"
                    )
                    return None
            
            # Add regime and strategy metadata
            combined_signal.metadata.update({
                "market_regime": current_regime.value,
                "regime_params": regime_params,
                "strategy_signals": [s.metadata.get("strategy_type") for s in signals],
                "generation_timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(
                f"Enhanced signal generated for {symbol.ticker}: "
                f"{combined_signal.signal_type.value} (confidence: {combined_signal.confidence:.3f}, "
                f"regime: {current_regime.value})"
            )
            
            return combined_signal
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced signal for {symbol.ticker}: {e}")
            return None
    
    async def _generate_multi_strategy_signals(
        self,
        symbol: Symbol,
        data: pd.DataFrame,
        regime_params: Dict[str, float]
    ) -> List[TradingSignal]:
        """Generate signals from multiple strategies."""
        signals = []
        
        # 1. Trend Following Strategy
        trend_signal = await self._generate_trend_signal(symbol, data, regime_params)
        if trend_signal:
            trend_signal.metadata["strategy_type"] = "trend_following"
            signals.append(trend_signal)
        
        # 2. Mean Reversion Strategy
        mean_reversion_signal = await self._generate_mean_reversion_signal(
            symbol, data, regime_params
        )
        if mean_reversion_signal:
            mean_reversion_signal.metadata["strategy_type"] = "mean_reversion"
            signals.append(mean_reversion_signal)
        
        # 3. Momentum Strategy
        momentum_signal = await self._generate_momentum_signal(
            symbol, data, regime_params
        )
        if momentum_signal:
            momentum_signal.metadata["strategy_type"] = "momentum"
            signals.append(momentum_signal)
        
        return signals
    
    async def _generate_trend_signal(
        self,
        symbol: Symbol,
        data: pd.DataFrame,
        regime_params: Dict[str, float]
    ) -> Optional[TradingSignal]:
        """Generate trend-following signal with regime adaptation."""
        try:
            # Calculate indicators with regime-adjusted parameters
            ema_fast = data['close'].ewm(span=12).mean()
            ema_slow = data['close'].ewm(span=26).mean()
            macd_result = await self.indicators.calculate_macd(data, 12, 26, 9)
            
            if ema_fast.empty or ema_slow.empty or not macd_result:
                return None
            
            macd_line = macd_result.get('macd', pd.Series())
            signal_line = macd_result.get('signal', pd.Series())
            
            if macd_line.empty or signal_line.empty:
                return None
            
            current_price = data['close'].iloc[-1]
            current_ema_fast = ema_fast.iloc[-1]
            current_ema_slow = ema_slow.iloc[-1]
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            
            # Enhanced trend detection with volume confirmation
            volume_confirmation = await self._check_volume_confirmation(data)
            
            # Bullish trend conditions
            if (current_ema_fast > current_ema_slow and 
                current_macd > current_signal and
                volume_confirmation > 1.05):  # 5% above average volume
                
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    strategy_name=self.name,
                    metadata={
                        "ema_fast": float(current_ema_fast),
                        "ema_slow": float(current_ema_slow),
                        "macd": float(current_macd),
                        "signal": float(current_signal),
                        "volume_confirmation": volume_confirmation
                    }
                )
            
            # Bearish trend conditions
            elif (current_ema_fast < current_ema_slow and 
                  current_macd < current_signal and
                  volume_confirmation > 1.05):
                
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    strategy_name=self.name,
                    metadata={
                        "ema_fast": float(current_ema_fast),
                        "ema_slow": float(current_ema_slow),
                        "macd": float(current_macd),
                        "signal": float(current_signal),
                        "volume_confirmation": volume_confirmation
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in trend signal generation: {e}")
            return None
    
    async def _generate_mean_reversion_signal(
        self,
        symbol: Symbol,
        data: pd.DataFrame,
        regime_params: Dict[str, float]
    ) -> Optional[TradingSignal]:
        """Generate mean reversion signal with regime adaptation."""
        try:
            # Calculate indicators with regime-adjusted parameters
            rsi = await self.indicators.calculate_rsi(data, period=14)
            bollinger_result = await self.indicators.calculate_bollinger_bands(
                data, period=20, std_dev=2.0
            )
            
            if rsi.empty or not bollinger_result:
                return None
            
            bb_upper = bollinger_result.get('upper', pd.Series())
            bb_lower = bollinger_result.get('lower', pd.Series())
            bb_middle = bollinger_result.get('middle', pd.Series())
            
            if bb_upper.empty or bb_lower.empty or bb_middle.empty:
                return None
            
            current_price = data['close'].iloc[-1]
            current_rsi = rsi.iloc[-1]
            current_bb_upper = bb_upper.iloc[-1]
            current_bb_lower = bb_lower.iloc[-1]
            current_bb_middle = bb_middle.iloc[-1]
            
            # Get regime-adjusted RSI thresholds
            rsi_oversold = regime_params.get("rsi_oversold", 30)
            rsi_overbought = regime_params.get("rsi_overbought", 70)
            
            # Enhanced mean reversion with multiple confirmations
            bb_position = (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower)
            
            # Oversold conditions (buy signal)
            if (current_rsi < rsi_oversold and 
                bb_position < 0.2 and  # Price near lower Bollinger Band
                current_price < current_bb_middle):  # Below middle line
                
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    strategy_name=self.name,
                    metadata={
                        "rsi": float(current_rsi),
                        "bb_position": float(bb_position),
                        "bb_upper": float(current_bb_upper),
                        "bb_lower": float(current_bb_lower),
                        "rsi_threshold": rsi_oversold
                    }
                )
            
            # Overbought conditions (sell signal)
            elif (current_rsi > rsi_overbought and 
                  bb_position > 0.8 and  # Price near upper Bollinger Band
                  current_price > current_bb_middle):  # Above middle line
                
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    strategy_name=self.name,
                    metadata={
                        "rsi": float(current_rsi),
                        "bb_position": float(bb_position),
                        "bb_upper": float(current_bb_upper),
                        "bb_lower": float(current_bb_lower),
                        "rsi_threshold": rsi_overbought
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in mean reversion signal generation: {e}")
            return None
    
    async def _generate_momentum_signal(
        self,
        symbol: Symbol,
        data: pd.DataFrame,
        regime_params: Dict[str, float]
    ) -> Optional[TradingSignal]:
        """Generate momentum signal with regime adaptation."""
        try:
            # Calculate momentum indicators
            roc = await self.indicators.calculate_rate_of_change(data, period=20)
            stoch_result = await self.indicators.calculate_stochastic(data, k_period=14, d_period=3)
            
            if roc.empty or not stoch_result:
                return None
            
            stoch_k = stoch_result.get('%K', pd.Series())
            stoch_d = stoch_result.get('%D', pd.Series())
            
            if stoch_k.empty or stoch_d.empty:
                return None
            
            current_price = data['close'].iloc[-1]
            current_roc = roc.iloc[-1]
            current_stoch_k = stoch_k.iloc[-1]
            current_stoch_d = stoch_d.iloc[-1]
            
            # Price momentum confirmation
            price_momentum = (current_price - data['close'].iloc[-5]) / data['close'].iloc[-5]
            
            # Bullish momentum conditions
            if (current_roc > 0.02 and  # 2% rate of change
                current_stoch_k > current_stoch_d and  # Stochastic bullish
                current_stoch_k < 80 and  # Not overbought
                price_momentum > 0.01):  # Positive recent momentum
                
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    strategy_name=self.name,
                    metadata={
                        "roc": float(current_roc),
                        "stoch_k": float(current_stoch_k),
                        "stoch_d": float(current_stoch_d),
                        "price_momentum": float(price_momentum)
                    }
                )
            
            # Bearish momentum conditions
            elif (current_roc < -0.02 and  # -2% rate of change
                  current_stoch_k < current_stoch_d and  # Stochastic bearish
                  current_stoch_k > 20 and  # Not oversold
                  price_momentum < -0.01):  # Negative recent momentum
                
                return TradingSignal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    strategy_name=self.name,
                    metadata={
                        "roc": float(current_roc),
                        "stoch_k": float(current_stoch_k),
                        "stoch_d": float(current_stoch_d),
                        "price_momentum": float(price_momentum)
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in momentum signal generation: {e}")
            return None
    
    async def _combine_signals(
        self,
        signals: List[TradingSignal],
        regime_params: Dict[str, float],
        enable_single_strategy: bool = False
    ) -> Optional[TradingSignal]:
        """Combine multiple strategy signals using weighted voting."""
        try:
            if not signals:
                return None
            
            # If single strategy signals are enabled and we have a strong signal, use it
            if enable_single_strategy and len(signals) == 1:
                signal = signals[0]
                signal.confidence = 0.75  # Give single strategy signals decent confidence
                signal.metadata["signal_combination"] = "single_strategy"
                return signal
            
            # Get strategy weights from regime parameters
            trend_weight = regime_params.get("trend_weight", 0.4)
            mean_reversion_weight = regime_params.get("mean_reversion_weight", 0.35)
            momentum_weight = regime_params.get("momentum_weight", 0.25)
            
            weights = {
                "trend_following": trend_weight,
                "mean_reversion": mean_reversion_weight,
                "momentum": momentum_weight
            }
            
            # Calculate weighted vote
            buy_score = 0.0
            sell_score = 0.0
            total_weight = 0.0
            
            for signal in signals:
                strategy_type = signal.metadata.get("strategy_type", "unknown")
                weight = weights.get(strategy_type, 0.0)
                
                if signal.signal_type == SignalType.BUY:
                    buy_score += weight
                elif signal.signal_type == SignalType.SELL:
                    sell_score += weight
                
                total_weight += weight
            
            # Determine combined signal
            if total_weight == 0:
                return None
            
            buy_percentage = buy_score / total_weight
            sell_percentage = sell_score / total_weight
            
            # Relaxed consensus for paper trading
            consensus_threshold = 0.40  # 40% consensus required for more trades
            
            if buy_percentage >= consensus_threshold:
                combined_signal_type = SignalType.BUY
                signal_strength = buy_percentage
            elif sell_percentage >= consensus_threshold:
                combined_signal_type = SignalType.SELL
                signal_strength = sell_percentage
            else:
                return None  # No consensus
            
            # Use the first signal as template
            base_signal = signals[0]
            
            return TradingSignal(
                symbol=base_signal.symbol,
                signal_type=combined_signal_type,
                price=base_signal.price,
                strategy_name=self.name,
                confidence=signal_strength,  # Initial confidence based on consensus
                metadata={
                    "signal_combination": "weighted_voting",
                    "buy_score": buy_score,
                    "sell_score": sell_score,
                    "total_weight": total_weight,
                    "consensus_strength": signal_strength,
                    "contributing_strategies": [s.metadata.get("strategy_type") for s in signals]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error combining signals: {e}")
            return None
    
    async def _check_volume_confirmation(self, data: pd.DataFrame) -> float:
        """Check volume confirmation for signals."""
        try:
            if 'volume' not in data.columns or len(data) < 20:
                return 1.0  # Neutral if no volume data
            
            current_volume = data['volume'].iloc[-1]
            avg_volume = data['volume'].tail(20).mean()
            
            return current_volume / avg_volume if avg_volume > 0 else 1.0
            
        except Exception as e:
            return 1.0
    
    async def calculate_position_size(
        self,
        signal: TradingSignal,
        portfolio: Portfolio
    ) -> int:
        """Calculate optimal position size using advanced sizing."""
        if not self.config["enable_advanced_sizing"]:
            # Fallback to simple sizing
            return await self._simple_position_sizing(signal, portfolio)
        
        return await self.position_sizer.calculate_optimal_position_size(
            signal, portfolio, signal.confidence
        )
    
    async def _simple_position_sizing(
        self,
        signal: TradingSignal,
        portfolio: Portfolio
    ) -> int:
        """Simple fallback position sizing."""
        try:
            risk_amount = portfolio.equity * 0.02  # 2% risk
            shares = int(risk_amount / signal.price) if signal.price > 0 else 0
            return max(0, shares)
        except:
            return 0
    
    async def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        self.config.update(parameters)
        
        # Update from custom_settings if available
        if "custom_settings" in parameters:
            custom = parameters["custom_settings"]
            if "min_signal_confidence" in custom:
                self.config["min_signal_confidence"] = custom["min_signal_confidence"]
            if "enable_single_strategy_trades" in custom:
                self.config["enable_single_strategy_trades"] = custom["enable_single_strategy_trades"]
    
    async def get_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters."""
        return self.config.copy()
    
    async def get_required_data_period(self) -> int:
        """Get minimum data period required in days."""
        return 100  # Need 100 days for comprehensive analysis
    
    async def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate generated signal."""
        return (signal.symbol is not None and 
                signal.signal_type in [SignalType.BUY, SignalType.SELL] and
                signal.price is not None and 
                signal.price > 0 and
                signal.confidence >= 0)