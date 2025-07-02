"""
Technical Indicators Utility Module.

This module provides optimized implementations of technical indicators
used throughout the trading system.
"""

import logging
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np


class TechnicalIndicators:
    """
    Optimized technical indicators implementation.
    
    All methods are designed to be fast and memory-efficient for
    real-time trading applications.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    async def calculate_rsi(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Relative Strength Index (RSI)."""
        try:
            if 'close' not in data.columns or len(data) < period + 1:
                return pd.Series(dtype=float)
            
            close_prices = data['close']
            delta = close_prices.diff()
            
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)  # Fill NaN with neutral value
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_macd(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            if 'close' not in data.columns or len(data) < slow_period + signal_period:
                return {}
            
            close_prices = data['close']
            
            # Calculate EMAs
            ema_fast = close_prices.ewm(span=fast_period).mean()
            ema_slow = close_prices.ewm(span=slow_period).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return {}
    
    async def calculate_bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        try:
            if 'close' not in data.columns or len(data) < period:
                return {}
            
            close_prices = data['close']
            
            # Calculate middle line (SMA)
            middle = close_prices.rolling(window=period).mean()
            
            # Calculate standard deviation
            std = close_prices.rolling(window=period).std()
            
            # Calculate upper and lower bands
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return {}
    
    async def calculate_atr(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Average True Range (ATR)."""
        try:
            if not all(col in data.columns for col in ['high', 'low', 'close']) or len(data) < period + 1:
                return pd.Series(dtype=float)
            
            high = data['high']
            low = data['low']
            close = data['close']
            prev_close = close.shift(1)
            
            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate ATR
            atr = true_range.rolling(window=period).mean()
            
            return atr.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_adx(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Average Directional Index (ADX)."""
        try:
            if not all(col in data.columns for col in ['high', 'low', 'close']) or len(data) < period * 2:
                return pd.Series(dtype=float)
            
            high = data['high']
            low = data['low']
            close = data['close']
            
            # Calculate True Range
            atr_series = await self.calculate_atr(data, period)
            
            # Calculate Directional Movement
            plus_dm = high.diff()
            minus_dm = -low.diff()
            
            # Set conditions
            plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
            minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
            
            # Calculate smoothed DM
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_series)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_series)
            
            # Calculate DX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            
            # Calculate ADX
            adx = dx.rolling(window=period).mean()
            
            return adx.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_di_plus(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate +DI (Directional Indicator Plus)."""
        try:
            if not all(col in data.columns for col in ['high', 'low']) or len(data) < period + 1:
                return pd.Series(dtype=float)
            
            high = data['high']
            plus_dm = high.diff()
            plus_dm = plus_dm.where(plus_dm > 0, 0)
            
            atr_series = await self.calculate_atr(data, period)
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_series)
            
            return plus_di.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculating +DI: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_di_minus(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate -DI (Directional Indicator Minus)."""
        try:
            if not all(col in data.columns for col in ['high', 'low']) or len(data) < period + 1:
                return pd.Series(dtype=float)
            
            low = data['low']
            minus_dm = -low.diff()
            minus_dm = minus_dm.where(minus_dm > 0, 0)
            
            atr_series = await self.calculate_atr(data, period)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_series)
            
            return minus_di.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculating -DI: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_stochastic(
        self,
        data: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator."""
        try:
            if not all(col in data.columns for col in ['high', 'low', 'close']) or len(data) < k_period:
                return {}
            
            high = data['high']
            low = data['low']
            close = data['close']
            
            # Calculate %K
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            
            # Calculate %D (smoothed %K)
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                '%K': k_percent.fillna(50),
                '%D': d_percent.fillna(50)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic: {e}")
            return {}
    
    async def calculate_rate_of_change(
        self,
        data: pd.DataFrame,
        period: int = 10
    ) -> pd.Series:
        """Calculate Rate of Change (ROC)."""
        try:
            if 'close' not in data.columns or len(data) < period + 1:
                return pd.Series(dtype=float)
            
            close_prices = data['close']
            roc = (close_prices / close_prices.shift(period) - 1) * 100
            
            return roc.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculating ROC: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_obv(self, data: pd.DataFrame) -> pd.Series:
        """Calculate On Balance Volume (OBV)."""
        try:
            if not all(col in data.columns for col in ['close', 'volume']) or len(data) < 2:
                return pd.Series(dtype=float)
            
            close_prices = data['close']
            volume = data['volume']
            
            price_change = close_prices.diff()
            
            # Determine volume direction
            volume_direction = np.where(price_change > 0, volume,
                                     np.where(price_change < 0, -volume, 0))
            
            obv = pd.Series(volume_direction, index=data.index).cumsum()
            
            return obv.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculating OBV: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price (VWAP)."""
        try:
            if not all(col in data.columns for col in ['high', 'low', 'close', 'volume']):
                return pd.Series(dtype=float)
            
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            volume = data['volume']
            
            # Calculate cumulative values
            cum_vol_price = (typical_price * volume).cumsum()
            cum_volume = volume.cumsum()
            
            vwap = cum_vol_price / cum_volume
            
            return vwap.fillna(typical_price)
            
        except Exception as e:
            self.logger.error(f"Error calculating VWAP: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_williams_r(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Williams %R."""
        try:
            if not all(col in data.columns for col in ['high', 'low', 'close']) or len(data) < period:
                return pd.Series(dtype=float)
            
            high = data['high']
            low = data['low']
            close = data['close']
            
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            
            williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
            
            return williams_r.fillna(-50)
            
        except Exception as e:
            self.logger.error(f"Error calculating Williams %R: {e}")
            return pd.Series(dtype=float)
    
    async def calculate_commodity_channel_index(
        self,
        data: pd.DataFrame,
        period: int = 20
    ) -> pd.Series:
        """Calculate Commodity Channel Index (CCI)."""
        try:
            if not all(col in data.columns for col in ['high', 'low', 'close']) or len(data) < period:
                return pd.Series(dtype=float)
            
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            
            # Calculate SMA of typical price
            sma_tp = typical_price.rolling(window=period).mean()
            
            # Calculate mean deviation
            mean_deviation = typical_price.rolling(window=period).apply(
                lambda x: np.mean(np.abs(x - x.mean()))
            )
            
            # Calculate CCI
            cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
            
            return cci.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculating CCI: {e}")
            return pd.Series(dtype=float)