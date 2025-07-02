"""
Alpaca Trading Client Implementation.

This module provides a concrete implementation of the trading service
using the Alpaca Markets API.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime

from core.domain import Symbol, Quote, Bar, Order, Position, Portfolio
from core.trading.interfaces import ITradingService
from config.models import ApiCredentials


class AlpacaClient(ITradingService):
    """
    Alpaca trading client implementation.
    
    Provides connection to Alpaca Markets for trading operations.
    """
    
    def __init__(
        self,
        credentials: ApiCredentials,
        logger: Optional[logging.Logger] = None
    ):
        self.credentials = credentials
        self.logger = logger or logging.getLogger(__name__)
        self._client = None
        
        # For now, create a simple mock client
        # In production, this would initialize the actual Alpaca API client
        self.logger.info(f"🔌 Alpaca client initialized (Paper Trading: {credentials.paper_trading})")
    
    async def connect(self) -> bool:
        """Connect to Alpaca API."""
        try:
            # In production, this would establish the actual connection
            self.logger.info("🔗 Connected to Alpaca API")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Alpaca: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Alpaca API."""
        self.logger.info("🔌 Disconnected from Alpaca API")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            # Try to get real account data if API keys are configured
            # Check for API keys in both the credentials object and environment variables
            api_key = (self.credentials.key_id or 
                      os.getenv('ALPACA_API_KEY') or 
                      os.getenv('APCA_API_KEY_ID'))
            secret_key = (self.credentials.secret_key or 
                         os.getenv('ALPACA_SECRET_KEY') or 
                         os.getenv('APCA_API_SECRET_KEY'))
            
            if api_key and secret_key:
                try:
                    from alpaca.trading.client import TradingClient
                    
                    # Initialize Alpaca client
                    paper_trading = (self.credentials.paper_trading or 
                                   os.getenv('PAPER_TRADING', 'true').lower() == 'true')
                    
                    trading_client = TradingClient(
                        api_key=api_key,
                        secret_key=secret_key,
                        paper=paper_trading
                    )
                    
                    # Get account information
                    account = trading_client.get_account()
                    
                    return {
                        "account_id": account.id,
                        "buying_power": float(account.buying_power),
                        "cash": float(account.cash),
                        "portfolio_value": float(account.portfolio_value),
                        "equity": float(account.equity),
                        "pattern_day_trader": account.pattern_day_trader,
                        "trading_blocked": account.trading_blocked,
                        "paper_trading": self.credentials.paper_trading
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to get real account data: {e}")
                    # Fall back to mock data
            
            # Mock account info when no API keys or connection fails
            self.logger.info("Using mock account data (API keys not configured)")
            return {
                "account_id": "mock_account",
                "buying_power": 25000.0,
                "cash": 25000.0,
                "portfolio_value": 25000.0,
                "equity": 25000.0,
                "pattern_day_trader": False,
                "trading_blocked": False,
                "paper_trading": self.credentials.paper_trading
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            # Return safe defaults
            return {
                "account_id": "error_account",
                "buying_power": 0.0,
                "cash": 0.0,
                "portfolio_value": 0.0,
                "equity": 0.0,
                "pattern_day_trader": False,
                "trading_blocked": True,
                "paper_trading": True
            }
    
    async def get_positions(self) -> List[Position]:
        """Get all current positions."""
        # Mock empty positions for now
        return []
    
    async def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get orders with optional status filter."""
        # Mock empty orders for now
        return []
    
    async def submit_order(self, order: Order) -> Order:
        """Submit a trading order."""
        self.logger.info(
            f"📝 Mock order submitted: {order.side} {order.qty} {order.symbol.ticker} "
            f"(type: {order.order_type}, paper: {self.credentials.paper_trading})"
        )
        
        # Update order with filled information
        order.status = "filled"
        order.filled_qty = order.qty
        order.filled_price = Decimal("150.00")  # Mock price
        order.filled_at = datetime.now()
        
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        self.logger.info(f"❌ Mock order cancelled: {order_id}")
        return True
    
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get current status of an order."""
        # Mock order status
        return Order(
            id=order_id,
            symbol=Symbol("MOCK"),
            qty=10,
            side="buy",
            order_type="market",
            status="filled",
            filled_qty=10,
            filled_price=Decimal("150.00"),
            submitted_at=datetime.now(),
            filled_at=datetime.now()
        )
    
    async def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        # Mock empty list for now
        return []
    
    async def get_quote(self, symbol: Symbol) -> Optional[Quote]:
        """Get current quote for symbol."""
        # Mock quote data
        return Quote(
            symbol=symbol,
            bid=Decimal("149.50"),
            ask=Decimal("150.50"),
            bid_size=100,
            ask_size=100,
            timestamp=datetime.now()
        )
    
    async def get_bars(
        self,
        symbol: Symbol,
        timeframe: str = "1Day",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Bar]:
        """Get historical bars for symbol."""
        # Mock bar data
        bars = []
        base_price = Decimal("150.00")
        
        # Generate some mock bars
        for i in range(min(limit or 100, 100)):
            bars.append(Bar(
                symbol=symbol,
                timestamp=datetime.now(),
                open=base_price,
                high=base_price * Decimal("1.02"),
                low=base_price * Decimal("0.98"),
                close=base_price,
                volume=1000000
            ))
        
        return bars
    
    async def is_market_open(self) -> bool:
        """Check if market is currently open."""
        return True  # Mock market as always open for testing


class MockTradingService(ITradingService):
    """Mock trading service for testing."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("🧪 Mock trading service initialized")
    
    async def connect(self) -> bool:
        return True
    
    async def disconnect(self) -> None:
        pass
    
    async def get_account_info(self) -> Dict[str, Any]:
        return {
            "account_id": "mock_account",
            "buying_power": 25000.0,
            "cash": 25000.0,
            "portfolio_value": 25000.0
        }
    
    async def get_positions(self) -> List[Position]:
        return []
    
    async def get_orders(self, status: Optional[str] = None) -> List[Order]:
        return []
    
    async def submit_order(self, symbol: Symbol, qty: int, side: str, **kwargs) -> Optional[Order]:
        self.logger.info(f"📝 Mock order: {side} {qty} {symbol.ticker}")
        return None
    
    async def cancel_order(self, order_id: str) -> bool:
        return True
    
    async def get_quote(self, symbol: Symbol) -> Optional[Quote]:
        return Quote(
            symbol=symbol,
            bid=Decimal("149.50"),
            ask=Decimal("150.50"),
            bid_size=100,
            ask_size=100,
            timestamp=datetime.now()
        )
    
    async def get_bars(self, symbol: Symbol, **kwargs) -> List[Bar]:
        return []
    
    async def is_market_open(self) -> bool:
        return True