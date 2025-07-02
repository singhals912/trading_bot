"""
Market Regime Detection Service.

This module provides sophisticated market regime detection to dynamically
adjust trading parameters based on current market conditions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from enum import Enum

from core.domain import Symbol, Quote, Bar
from core.data.interfaces import IHistoricalDataProvider
from utils.technical_indicators import TechnicalIndicators


class MarketRegime(Enum):
    """Market regime types."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    CHOPPY = "choppy"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"


class MarketRegimeDetector:
    """
    Advanced market regime detection using multiple indicators.
    
    Combines volatility analysis, trend strength, and market stress
    indicators to determine the current market environment.
    """
    
    def __init__(
        self,
        data_provider: IHistoricalDataProvider,
        logger: Optional[logging.Logger] = None
    ):
        self.data_provider = data_provider
        self.logger = logger or logging.getLogger(__name__)
        self.indicators = TechnicalIndicators()
        
        # Regime detection parameters
        self.vix_high_threshold = 30
        self.vix_low_threshold = 15
        self.adx_trend_threshold = 25
        self.volatility_percentile_lookback = 252  # 1 year
        
        # Cache for regime detection
        self._regime_cache: Dict[str, Tuple[MarketRegime, datetime]] = {}
        self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
    
    async def detect_market_regime(
        self,
        symbol: Optional[Symbol] = None
    ) -> MarketRegime:
        """
        Detect current market regime.
        
        Args:
            symbol: Specific symbol to analyze, or None for market-wide regime
            
        Returns:
            Current market regime
        """
        try:
            # Use SPY as market proxy if no symbol specified
            analysis_symbol = symbol or Symbol("SPY")
            cache_key = analysis_symbol.ticker
            
            # Check cache first
            if cache_key in self._regime_cache:
                regime, timestamp = self._regime_cache[cache_key]
                if datetime.now() - timestamp < self._cache_duration:
                    return regime
            
            # Get market data for analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=100)  # ~4 months of data
            
            historical_data = await self.data_provider.get_bars_dataframe(
                analysis_symbol,
                timeframe="1D",
                start_date=start_date,
                end_date=end_date
            )
            
            if historical_data.empty:
                self.logger.warning(f"No data available for regime detection: {analysis_symbol.ticker}")
                return MarketRegime.CHOPPY  # Default safe regime
            
            # Analyze market regime using multiple methods
            volatility_regime = await self._analyze_volatility_regime(historical_data)
            trend_regime = await self._analyze_trend_regime(historical_data)
            stress_regime = await self._analyze_market_stress(analysis_symbol)
            
            # Combine regimes with priority (stress > volatility > trend)
            final_regime = self._combine_regime_signals(
                volatility_regime, trend_regime, stress_regime
            )
            
            # Cache the result
            self._regime_cache[cache_key] = (final_regime, datetime.now())
            
            self.logger.info(f"Market regime detected for {analysis_symbol.ticker}: {final_regime.value}")
            return final_regime
            
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return MarketRegime.CHOPPY  # Safe default
    
    async def get_regime_parameters(self, regime: MarketRegime) -> Dict[str, float]:
        """
        Get trading parameters optimized for specific market regime.
        
        Args:
            regime: Current market regime
            
        Returns:
            Dictionary of parameters optimized for the regime
        """
        parameter_map = {
            MarketRegime.TRENDING_UP: {
                "rsi_oversold": 25,
                "rsi_overbought": 80,
                "stop_loss_pct": 0.015,
                "take_profit_pct": 0.06,
                "position_size_multiplier": 1.2,
                "max_correlation": 0.7,
                "trend_weight": 0.6,
                "mean_reversion_weight": 0.2,
                "momentum_weight": 0.2
            },
            MarketRegime.TRENDING_DOWN: {
                "rsi_oversold": 20,
                "rsi_overbought": 75,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.04,
                "position_size_multiplier": 0.8,
                "max_correlation": 0.6,
                "trend_weight": 0.5,
                "mean_reversion_weight": 0.3,
                "momentum_weight": 0.2
            },
            MarketRegime.CHOPPY: {
                "rsi_oversold": 35,
                "rsi_overbought": 65,
                "stop_loss_pct": 0.025,
                "take_profit_pct": 0.03,
                "position_size_multiplier": 0.7,
                "max_correlation": 0.5,
                "trend_weight": 0.2,
                "mean_reversion_weight": 0.6,
                "momentum_weight": 0.2
            },
            MarketRegime.HIGH_VOLATILITY: {
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "stop_loss_pct": 0.03,
                "take_profit_pct": 0.025,
                "position_size_multiplier": 0.5,
                "max_correlation": 0.4,
                "trend_weight": 0.3,
                "mean_reversion_weight": 0.5,
                "momentum_weight": 0.2
            },
            MarketRegime.LOW_VOLATILITY: {
                "rsi_oversold": 25,
                "rsi_overbought": 75,
                "stop_loss_pct": 0.012,
                "take_profit_pct": 0.05,
                "position_size_multiplier": 1.3,
                "max_correlation": 0.75,
                "trend_weight": 0.5,
                "mean_reversion_weight": 0.3,
                "momentum_weight": 0.2
            },
            MarketRegime.CRISIS: {
                "rsi_oversold": 40,
                "rsi_overbought": 60,
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.02,
                "position_size_multiplier": 0.3,
                "max_correlation": 0.3,
                "trend_weight": 0.2,
                "mean_reversion_weight": 0.4,
                "momentum_weight": 0.4
            }
        }
        
        return parameter_map.get(regime, parameter_map[MarketRegime.CHOPPY])
    
    async def _analyze_volatility_regime(self, data: pd.DataFrame) -> MarketRegime:
        """Analyze volatility-based regime."""
        try:
            # Calculate realized volatility (20-day rolling)
            returns = data['close'].pct_change().dropna()
            volatility = returns.rolling(window=20).std() * np.sqrt(252)
            current_vol = volatility.iloc[-1]
            
            # Calculate volatility percentiles
            vol_percentile = (volatility < current_vol).mean() * 100
            
            # Try to get VIX data for additional context
            vix_regime = await self._get_vix_regime()
            
            # Combine realized vol and VIX
            if vix_regime == MarketRegime.CRISIS or vol_percentile > 90:
                return MarketRegime.HIGH_VOLATILITY
            elif vix_regime == MarketRegime.HIGH_VOLATILITY or vol_percentile > 75:
                return MarketRegime.HIGH_VOLATILITY
            elif vol_percentile < 25:
                return MarketRegime.LOW_VOLATILITY
            else:
                return MarketRegime.CHOPPY
                
        except Exception as e:
            self.logger.error(f"Error in volatility regime analysis: {e}")
            return MarketRegime.CHOPPY
    
    async def _analyze_trend_regime(self, data: pd.DataFrame) -> MarketRegime:
        """Analyze trend-based regime."""
        try:
            # Calculate ADX for trend strength
            adx = await self.indicators.calculate_adx(data)
            if adx.empty:
                return MarketRegime.CHOPPY
            
            current_adx = adx.iloc[-1]
            
            # Calculate directional movement
            di_plus = await self.indicators.calculate_di_plus(data)
            di_minus = await self.indicators.calculate_di_minus(data)
            
            if current_adx > self.adx_trend_threshold:
                if not di_plus.empty and not di_minus.empty:
                    if di_plus.iloc[-1] > di_minus.iloc[-1]:
                        return MarketRegime.TRENDING_UP
                    else:
                        return MarketRegime.TRENDING_DOWN
                else:
                    # Fallback to price trend
                    sma_50 = data['close'].rolling(window=50).mean()
                    sma_200 = data['close'].rolling(window=200).mean()
                    
                    if len(sma_50) > 0 and len(sma_200) > 0:
                        if sma_50.iloc[-1] > sma_200.iloc[-1]:
                            return MarketRegime.TRENDING_UP
                        else:
                            return MarketRegime.TRENDING_DOWN
            
            return MarketRegime.CHOPPY
            
        except Exception as e:
            self.logger.error(f"Error in trend regime analysis: {e}")
            return MarketRegime.CHOPPY
    
    async def _analyze_market_stress(self, symbol: Symbol) -> MarketRegime:
        """Analyze market stress indicators."""
        try:
            # Check for crisis indicators
            # This would be enhanced with more sophisticated stress indicators
            
            # Simple implementation: check for extreme price movements
            data = await self.data_provider.get_bars_dataframe(
                symbol,
                timeframe="1D",
                limit=10
            )
            
            if not data.empty and len(data) >= 5:
                # Check for consecutive large moves (potential crisis)
                daily_returns = data['close'].pct_change().abs()
                large_moves = (daily_returns > 0.05).sum()  # >5% moves
                
                if large_moves >= 3:  # 3+ large moves in last 10 days
                    return MarketRegime.CRISIS
            
            return MarketRegime.CHOPPY  # Default
            
        except Exception as e:
            self.logger.error(f"Error in market stress analysis: {e}")
            return MarketRegime.CHOPPY
    
    async def _get_vix_regime(self) -> MarketRegime:
        """Get VIX-based volatility regime."""
        try:
            vix_symbol = Symbol("VIX")
            vix_data = await self.data_provider.get_bars_dataframe(
                vix_symbol,
                timeframe="1D",
                limit=1
            )
            
            if not vix_data.empty:
                current_vix = vix_data['close'].iloc[-1]
                
                if current_vix > 40:
                    return MarketRegime.CRISIS
                elif current_vix > self.vix_high_threshold:
                    return MarketRegime.HIGH_VOLATILITY
                elif current_vix < self.vix_low_threshold:
                    return MarketRegime.LOW_VOLATILITY
                else:
                    return MarketRegime.CHOPPY
            
        except Exception as e:
            self.logger.debug(f"VIX data not available: {e}")
        
        return MarketRegime.CHOPPY
    
    def _combine_regime_signals(
        self,
        volatility_regime: MarketRegime,
        trend_regime: MarketRegime,
        stress_regime: MarketRegime
    ) -> MarketRegime:
        """Combine multiple regime signals with priority."""
        
        # Crisis takes highest priority
        if stress_regime == MarketRegime.CRISIS:
            return MarketRegime.CRISIS
        
        # High volatility takes second priority
        if volatility_regime == MarketRegime.HIGH_VOLATILITY:
            return MarketRegime.HIGH_VOLATILITY
        
        # Low volatility with trend
        if volatility_regime == MarketRegime.LOW_VOLATILITY:
            if trend_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
                return trend_regime
            else:
                return MarketRegime.LOW_VOLATILITY
        
        # Default to trend regime or choppy
        if trend_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            return trend_regime
        
        return MarketRegime.CHOPPY
    
    async def get_regime_history(
        self,
        symbol: Symbol,
        days: int = 30
    ) -> List[Tuple[datetime, MarketRegime]]:
        """Get historical regime analysis."""
        try:
            history = []
            end_date = datetime.now()
            
            for i in range(days):
                date = end_date - timedelta(days=i)
                # This would be implemented with historical regime detection
                # For now, return current regime
                regime = await self.detect_market_regime(symbol)
                history.append((date, regime))
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting regime history: {e}")
            return []