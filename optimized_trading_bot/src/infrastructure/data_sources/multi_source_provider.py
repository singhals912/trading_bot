"""
Multi-Source Data Provider Implementation.

This module provides a data provider that can fetch data from multiple sources
with fallback support and caching.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from core.domain import Symbol, Quote, Bar
from core.data.interfaces import IHistoricalDataProvider, IQuoteProvider
from config.models import DataConfig


class MultiSourceDataProvider(IHistoricalDataProvider, IQuoteProvider):
    """
    Multi-source data provider with fallback support.
    
    Provides market data from multiple sources with automatic fallback
    and intelligent caching.
    """
    
    def __init__(
        self,
        config: DataConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._cache = {}
        
        self.logger.info(f"📊 Multi-source data provider initialized (primary: {config.primary_provider})")
    
    async def get_quote(self, symbol: Symbol) -> Optional[Quote]:
        """Get current quote for symbol."""
        try:
            # Check cache first
            cache_key = f"quote_{symbol.ticker}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now() - timestamp).total_seconds() < self.config.cache_ttl_quotes:
                    return cached_data
            
            # Mock quote data for now
            quote = Quote(
                symbol=symbol,
                bid=Decimal("149.50"),
                ask=Decimal("150.50"),
                bid_size=100,
                ask_size=100,
                timestamp=datetime.now()
            )
            
            # Cache the result
            self._cache[cache_key] = (quote, datetime.now())
            
            return quote
            
        except Exception as e:
            self.logger.error(f"Error getting quote for {symbol.ticker}: {e}")
            return None
    
    async def get_bars(
        self,
        symbol: Symbol,
        timeframe: str = "1Day",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Bar]:
        """Get historical bars for symbol."""
        try:
            # Check cache first
            cache_key = f"bars_{symbol.ticker}_{timeframe}_{start_date}_{end_date}_{limit}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now() - timestamp).total_seconds() < self.config.cache_ttl_bars:
                    return cached_data
            
            # Generate mock historical data for now
            bars = []
            num_bars = limit or 100
            base_price = Decimal("150.00")
            
            for i in range(num_bars):
                # Create realistic price movement
                price_change = (i % 10 - 5) * Decimal("0.50")  # Simple oscillation
                current_price = base_price + price_change
                
                bars.append(Bar(
                    symbol=symbol,
                    timestamp=datetime.now() - timedelta(days=num_bars-i),
                    open=current_price * Decimal("0.999"),
                    high=current_price * Decimal("1.015"),
                    low=current_price * Decimal("0.985"),
                    close=current_price,
                    volume=1000000 + (i * 50000)
                ))
            
            # Cache the result
            self._cache[cache_key] = (bars, datetime.now())
            
            self.logger.debug(f"Generated {len(bars)} bars for {symbol.ticker}")
            return bars
            
        except Exception as e:
            self.logger.error(f"Error getting bars for {symbol.ticker}: {e}")
            return []
    
    async def get_bars_dataframe(
        self,
        symbol: Symbol,
        timeframe: str = "1Day",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Get historical bars as pandas DataFrame."""
        try:
            bars = await self.get_bars(symbol, timeframe, start_date, end_date, limit)
            
            if not bars:
                return pd.DataFrame()
            
            # Convert bars to DataFrame
            data = []
            for bar in bars:
                data.append({
                    'timestamp': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': bar.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error creating DataFrame for {symbol.ticker}: {e}")
            return pd.DataFrame()
    
    async def get_quotes(self, symbols: List[Symbol]) -> Dict[Symbol, Quote]:
        """Get quotes for multiple symbols."""
        quotes = {}
        
        for symbol in symbols:
            quote = await self.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        return quotes
    
    async def stream_quotes(self, symbols: List[Symbol]):
        """Stream real-time quotes for symbols."""
        # Mock streaming - just yield quotes periodically
        import asyncio
        while True:
            for symbol in symbols:
                quote = await self.get_quote(symbol)
                if quote:
                    yield quote
            await asyncio.sleep(1)  # Wait 1 second between updates
    
    async def get_multiple_symbols_data(
        self,
        symbols: List[Symbol],
        timeframe: str = "1D",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[Symbol, pd.DataFrame]:
        """Get historical data for multiple symbols."""
        data = {}
        
        for symbol in symbols:
            df = await self.get_bars_dataframe(symbol, timeframe, start_date, end_date)
            if not df.empty:
                data[symbol] = df
        
        return data
    
    async def is_market_open(self) -> bool:
        """Check if market is currently open."""
        # Mock market as always open for testing
        return True
    
    async def get_market_calendar(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get market calendar."""
        # Mock calendar data
        return [
            {
                "date": datetime.now().date(),
                "open": datetime.now().replace(hour=9, minute=30),
                "close": datetime.now().replace(hour=16, minute=0),
                "session_open": datetime.now().replace(hour=4, minute=0),
                "session_close": datetime.now().replace(hour=20, minute=0)
            }
        ]
    
    async def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self.logger.info("🗑️ Data cache cleared")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys())
        }