"""
Advanced Signal Analysis and Confidence Scoring.

This module provides sophisticated signal analysis including confidence scoring,
multi-timeframe validation, and signal quality assessment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from core.domain import Symbol, TradingSignal, SignalType, Quote, Bar
from core.data.interfaces import IHistoricalDataProvider, IQuoteProvider
from utils.technical_indicators import TechnicalIndicators
from .market_regime import MarketRegimeDetector, MarketRegime


class SignalConfidenceAnalyzer:
    """
    Advanced signal confidence analysis using multiple validation methods.
    
    Analyzes signal quality across multiple dimensions:
    - Volume confirmation
    - Multi-timeframe alignment  
    - Support/resistance confluence
    - Market regime alignment
    - Historical pattern validation
    """
    
    def __init__(
        self,
        data_provider: IHistoricalDataProvider,
        quote_provider: IQuoteProvider,
        regime_detector: MarketRegimeDetector,
        logger: Optional[logging.Logger] = None
    ):
        self.data_provider = data_provider
        self.quote_provider = quote_provider
        self.regime_detector = regime_detector
        self.logger = logger or logging.getLogger(__name__)
        self.indicators = TechnicalIndicators()
        
        # Confidence scoring weights
        self.confidence_weights = {
            "volume_confirmation": 0.25,
            "timeframe_alignment": 0.30,
            "support_resistance": 0.20,
            "regime_alignment": 0.15,
            "pattern_strength": 0.10
        }
    
    async def analyze_signal_confidence(
        self,
        signal: TradingSignal,
        historical_data: Optional[pd.DataFrame] = None
    ) -> float:
        """
        Calculate comprehensive confidence score for trading signal.
        
        Args:
            signal: Trading signal to analyze
            historical_data: Optional pre-loaded historical data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Get historical data if not provided
            if historical_data is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=100)
                historical_data = await self.data_provider.get_bars_dataframe(
                    signal.symbol,
                    timeframe="1D",
                    start_date=start_date,
                    end_date=end_date
                )
            
            if historical_data.empty:
                self.logger.warning(f"No historical data for confidence analysis: {signal.symbol.ticker}")
                return 0.3  # Low confidence default
            
            # Calculate individual confidence components
            confidence_scores = {}
            
            # 1. Volume confirmation
            confidence_scores["volume_confirmation"] = await self._analyze_volume_confirmation(
                signal, historical_data
            )
            
            # 2. Multi-timeframe alignment
            confidence_scores["timeframe_alignment"] = await self._analyze_timeframe_alignment(
                signal, historical_data
            )
            
            # 3. Support/resistance confluence
            confidence_scores["support_resistance"] = await self._analyze_support_resistance(
                signal, historical_data
            )
            
            # 4. Market regime alignment
            confidence_scores["regime_alignment"] = await self._analyze_regime_alignment(
                signal
            )
            
            # 5. Pattern strength
            confidence_scores["pattern_strength"] = await self._analyze_pattern_strength(
                signal, historical_data
            )
            
            # Calculate weighted confidence score
            total_confidence = 0.0
            total_weight = 0.0
            
            for component, score in confidence_scores.items():
                if score is not None:  # Only include valid scores
                    weight = self.confidence_weights[component]
                    total_confidence += score * weight
                    total_weight += weight
            
            # Normalize by actual weights used
            final_confidence = total_confidence / max(total_weight, 0.1)
            final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp to [0,1]
            
            self.logger.debug(
                f"Signal confidence for {signal.symbol.ticker}: {final_confidence:.3f} "
                f"(components: {confidence_scores})"
            )
            
            return final_confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating signal confidence: {e}")
            return 0.3  # Safe default
    
    async def _analyze_volume_confirmation(
        self,
        signal: TradingSignal,
        data: pd.DataFrame
    ) -> Optional[float]:
        """Analyze volume confirmation for signal."""
        try:
            if 'volume' not in data.columns or len(data) < 20:
                return None
            
            # Calculate average volume over last 20 days
            avg_volume_20 = data['volume'].tail(20).mean()
            current_volume = data['volume'].iloc[-1]
            
            volume_ratio = current_volume / avg_volume_20
            
            # Score based on volume confirmation
            if volume_ratio > 2.0:  # Very high volume
                return 1.0
            elif volume_ratio > 1.5:  # High volume
                return 0.8
            elif volume_ratio > 1.2:  # Above average volume
                return 0.6
            elif volume_ratio > 0.8:  # Normal volume
                return 0.4
            else:  # Low volume
                return 0.1
                
        except Exception as e:
            self.logger.debug(f"Error in volume confirmation analysis: {e}")
            return None
    
    async def _analyze_timeframe_alignment(
        self,
        signal: TradingSignal,
        daily_data: pd.DataFrame
    ) -> Optional[float]:
        """Analyze signal alignment across multiple timeframes."""
        try:
            alignment_score = 0.0
            timeframes_checked = 0
            
            # Check 4-hour timeframe
            try:
                four_hour_data = await self.data_provider.get_bars_dataframe(
                    signal.symbol,
                    timeframe="4H",
                    limit=50
                )
                if not four_hour_data.empty:
                    four_hour_signal = await self._generate_simple_signal(four_hour_data)
                    if four_hour_signal == signal.signal_type:
                        alignment_score += 0.4
                    timeframes_checked += 1
            except:
                pass
            
            # Check 1-hour timeframe
            try:
                one_hour_data = await self.data_provider.get_bars_dataframe(
                    signal.symbol,
                    timeframe="1H",
                    limit=50
                )
                if not one_hour_data.empty:
                    one_hour_signal = await self._generate_simple_signal(one_hour_data)
                    if one_hour_signal == signal.signal_type:
                        alignment_score += 0.3
                    timeframes_checked += 1
            except:
                pass
            
            # Daily timeframe (already have data)
            daily_signal = await self._generate_simple_signal(daily_data)
            if daily_signal == signal.signal_type:
                alignment_score += 0.3
            timeframes_checked += 1
            
            return alignment_score if timeframes_checked > 0 else None
            
        except Exception as e:
            self.logger.debug(f"Error in timeframe alignment analysis: {e}")
            return None
    
    async def _analyze_support_resistance(
        self,
        signal: TradingSignal,
        data: pd.DataFrame
    ) -> Optional[float]:
        """Analyze support/resistance confluence."""
        try:
            current_price = data['close'].iloc[-1]
            
            # Find support and resistance levels
            support_levels = await self._find_support_levels(data)
            resistance_levels = await self._find_resistance_levels(data)
            
            # Calculate distance to nearest levels
            support_distances = [abs(current_price - level) / current_price for level in support_levels]
            resistance_distances = [abs(current_price - level) / current_price for level in resistance_levels]
            
            min_support_distance = min(support_distances) if support_distances else 1.0
            min_resistance_distance = min(resistance_distances) if resistance_distances else 1.0
            
            # Score based on proximity to levels and signal direction
            if signal.signal_type == SignalType.BUY:
                # For buy signals, closer to support is better
                if min_support_distance < 0.02:  # Within 2%
                    return 0.9
                elif min_support_distance < 0.05:  # Within 5%
                    return 0.7
                else:
                    return 0.3
            elif signal.signal_type == SignalType.SELL:
                # For sell signals, closer to resistance is better
                if min_resistance_distance < 0.02:  # Within 2%
                    return 0.9
                elif min_resistance_distance < 0.05:  # Within 5%
                    return 0.7
                else:
                    return 0.3
            
            return 0.5  # Neutral for HOLD signals
            
        except Exception as e:
            self.logger.debug(f"Error in support/resistance analysis: {e}")
            return None
    
    async def _analyze_regime_alignment(self, signal: TradingSignal) -> Optional[float]:
        """Analyze alignment with current market regime."""
        try:
            current_regime = await self.regime_detector.detect_market_regime(signal.symbol)
            
            # Score based on signal-regime alignment
            alignment_scores = {
                (SignalType.BUY, MarketRegime.TRENDING_UP): 1.0,
                (SignalType.BUY, MarketRegime.LOW_VOLATILITY): 0.8,
                (SignalType.BUY, MarketRegime.CHOPPY): 0.5,
                (SignalType.BUY, MarketRegime.TRENDING_DOWN): 0.2,
                (SignalType.BUY, MarketRegime.HIGH_VOLATILITY): 0.3,
                (SignalType.BUY, MarketRegime.CRISIS): 0.1,
                
                (SignalType.SELL, MarketRegime.TRENDING_DOWN): 1.0,
                (SignalType.SELL, MarketRegime.HIGH_VOLATILITY): 0.8,
                (SignalType.SELL, MarketRegime.CRISIS): 0.9,
                (SignalType.SELL, MarketRegime.TRENDING_UP): 0.2,
                (SignalType.SELL, MarketRegime.LOW_VOLATILITY): 0.3,
                (SignalType.SELL, MarketRegime.CHOPPY): 0.6,
                
                (SignalType.HOLD, MarketRegime.CHOPPY): 0.8,
                (SignalType.HOLD, MarketRegime.CRISIS): 1.0,
                (SignalType.HOLD, MarketRegime.HIGH_VOLATILITY): 0.7,
            }
            
            return alignment_scores.get((signal.signal_type, current_regime), 0.5)
            
        except Exception as e:
            self.logger.debug(f"Error in regime alignment analysis: {e}")
            return None
    
    async def _analyze_pattern_strength(
        self,
        signal: TradingSignal,
        data: pd.DataFrame
    ) -> Optional[float]:
        """Analyze technical pattern strength."""
        try:
            # Calculate multiple indicators to assess pattern strength
            rsi = await self.indicators.calculate_rsi(data)
            macd_result = await self.indicators.calculate_macd(data)
            
            if rsi.empty or not macd_result:
                return 0.5
            
            current_rsi = rsi.iloc[-1]
            macd_line = macd_result.get('macd', pd.Series())
            signal_line = macd_result.get('signal', pd.Series())
            
            pattern_strength = 0.0
            
            # RSI strength assessment
            if signal.signal_type == SignalType.BUY:
                if current_rsi < 30:  # Oversold
                    pattern_strength += 0.4
                elif current_rsi < 40:
                    pattern_strength += 0.3
                elif current_rsi < 50:
                    pattern_strength += 0.2
            elif signal.signal_type == SignalType.SELL:
                if current_rsi > 70:  # Overbought
                    pattern_strength += 0.4
                elif current_rsi > 60:
                    pattern_strength += 0.3
                elif current_rsi > 50:
                    pattern_strength += 0.2
            
            # MACD confirmation
            if not macd_line.empty and not signal_line.empty and len(macd_line) > 1:
                macd_current = macd_line.iloc[-1]
                signal_current = signal_line.iloc[-1]
                macd_prev = macd_line.iloc[-2]
                signal_prev = signal_line.iloc[-2]
                
                # MACD crossover confirmation
                if signal.signal_type == SignalType.BUY:
                    if macd_current > signal_current and macd_prev <= signal_prev:
                        pattern_strength += 0.6  # Bullish crossover
                    elif macd_current > signal_current:
                        pattern_strength += 0.3  # Above signal line
                elif signal.signal_type == SignalType.SELL:
                    if macd_current < signal_current and macd_prev >= signal_prev:
                        pattern_strength += 0.6  # Bearish crossover
                    elif macd_current < signal_current:
                        pattern_strength += 0.3  # Below signal line
            
            return min(pattern_strength, 1.0)
            
        except Exception as e:
            self.logger.debug(f"Error in pattern strength analysis: {e}")
            return None
    
    async def _generate_simple_signal(self, data: pd.DataFrame) -> SignalType:
        """Generate simple signal for timeframe alignment check."""
        try:
            if len(data) < 20:
                return SignalType.HOLD
            
            # Simple moving average crossover
            sma_short = data['close'].rolling(window=10).mean()
            sma_long = data['close'].rolling(window=20).mean()
            
            if len(sma_short) < 2 or len(sma_long) < 2:
                return SignalType.HOLD
            
            current_short = sma_short.iloc[-1]
            current_long = sma_long.iloc[-1]
            prev_short = sma_short.iloc[-2]
            prev_long = sma_long.iloc[-2]
            
            # Bullish crossover
            if current_short > current_long and prev_short <= prev_long:
                return SignalType.BUY
            # Bearish crossover
            elif current_short < current_long and prev_short >= prev_long:
                return SignalType.SELL
            # Trending up
            elif current_short > current_long:
                return SignalType.BUY
            # Trending down
            elif current_short < current_long:
                return SignalType.SELL
            
            return SignalType.HOLD
            
        except Exception as e:
            return SignalType.HOLD
    
    async def _find_support_levels(self, data: pd.DataFrame) -> List[float]:
        """Find key support levels."""
        try:
            lows = data['low'].tail(50)  # Last 50 periods
            support_levels = []
            
            # Find local minima as potential support
            for i in range(2, len(lows) - 2):
                if (lows.iloc[i] < lows.iloc[i-1] and 
                    lows.iloc[i] < lows.iloc[i-2] and
                    lows.iloc[i] < lows.iloc[i+1] and 
                    lows.iloc[i] < lows.iloc[i+2]):
                    support_levels.append(lows.iloc[i])
            
            # Also include recent significant lows
            recent_lows = lows.tail(10).min()
            if recent_lows not in support_levels:
                support_levels.append(recent_lows)
            
            return sorted(support_levels)
            
        except Exception as e:
            return []
    
    async def _find_resistance_levels(self, data: pd.DataFrame) -> List[float]:
        """Find key resistance levels."""
        try:
            highs = data['high'].tail(50)  # Last 50 periods
            resistance_levels = []
            
            # Find local maxima as potential resistance
            for i in range(2, len(highs) - 2):
                if (highs.iloc[i] > highs.iloc[i-1] and 
                    highs.iloc[i] > highs.iloc[i-2] and
                    highs.iloc[i] > highs.iloc[i+1] and 
                    highs.iloc[i] > highs.iloc[i+2]):
                    resistance_levels.append(highs.iloc[i])
            
            # Also include recent significant highs
            recent_highs = highs.tail(10).max()
            if recent_highs not in resistance_levels:
                resistance_levels.append(recent_highs)
            
            return sorted(resistance_levels, reverse=True)
            
        except Exception as e:
            return []
    
    async def filter_signals_by_confidence(
        self,
        signals: List[TradingSignal],
        min_confidence: float = 0.6
    ) -> List[TradingSignal]:
        """Filter signals by minimum confidence threshold."""
        try:
            filtered_signals = []
            
            for signal in signals:
                confidence = await self.analyze_signal_confidence(signal)
                
                # Update signal with confidence score
                signal.confidence = confidence
                
                if confidence >= min_confidence:
                    filtered_signals.append(signal)
                    self.logger.info(
                        f"Signal passed confidence filter: {signal.symbol.ticker} "
                        f"({signal.signal_type.value}) - confidence: {confidence:.3f}"
                    )
                else:
                    self.logger.debug(
                        f"Signal filtered out: {signal.symbol.ticker} "
                        f"({signal.signal_type.value}) - confidence: {confidence:.3f} < {min_confidence}"
                    )
            
            return filtered_signals
            
        except Exception as e:
            self.logger.error(f"Error filtering signals by confidence: {e}")
            return signals  # Return original signals if filtering fails