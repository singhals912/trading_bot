"""
Trading service interfaces.

This module defines the contracts for trading-related services including
order execution, position management, and portfolio operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..domain import (
    Order, Position, Portfolio, Symbol, OrderSide, OrderType,
    TradingSignal, Trade
)


class ITradingService(ABC):
    """Interface for trading operations."""
    
    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        """Submit an order to the broker."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get current status of an order."""
        pass
    
    @abstractmethod
    async def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        pass


class IPositionManager(ABC):
    """Interface for position management operations."""
    
    @abstractmethod
    async def open_position(self, signal: TradingSignal, quantity: int) -> Optional[Position]:
        """Open a new position based on trading signal."""
        pass
    
    @abstractmethod
    async def close_position(self, position_id: str, reason: str = "") -> Optional[Trade]:
        """Close an existing position."""
        pass
    
    @abstractmethod
    async def update_position_prices(self, position_id: str, current_price: Decimal) -> Position:
        """Update position with current market price."""
        pass
    
    @abstractmethod
    async def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID."""
        pass
    
    @abstractmethod
    async def get_positions_by_symbol(self, symbol: Symbol) -> List[Position]:
        """Get all positions for a symbol."""
        pass
    
    @abstractmethod
    async def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    async def check_stop_loss(self, position: Position) -> bool:
        """Check if position should be closed due to stop loss."""
        pass
    
    @abstractmethod
    async def check_take_profit(self, position: Position) -> bool:
        """Check if position should be closed due to take profit."""
        pass


class IPortfolioManager(ABC):
    """Interface for portfolio management operations."""
    
    @abstractmethod
    async def get_portfolio(self) -> Portfolio:
        """Get current portfolio state."""
        pass
    
    @abstractmethod
    async def update_portfolio(self) -> Portfolio:
        """Update portfolio with latest data."""
        pass
    
    @abstractmethod
    async def calculate_buying_power(self) -> Decimal:
        """Calculate available buying power."""
        pass
    
    @abstractmethod
    async def calculate_position_size(
        self, 
        symbol: Symbol, 
        signal: TradingSignal,
        risk_amount: Decimal
    ) -> int:
        """Calculate optimal position size for a trade."""
        pass
    
    @abstractmethod
    async def get_portfolio_value(self) -> Decimal:
        """Get total portfolio value."""
        pass
    
    @abstractmethod
    async def get_cash_balance(self) -> Decimal:
        """Get available cash balance."""
        pass


class IOrderExecutor(ABC):
    """Interface for intelligent order execution."""
    
    @abstractmethod
    async def execute_market_order(
        self,
        symbol: Symbol,
        side: OrderSide,
        quantity: int
    ) -> Order:
        """Execute a market order with optimal timing."""
        pass
    
    @abstractmethod
    async def execute_limit_order(
        self,
        symbol: Symbol,
        side: OrderSide,
        quantity: int,
        limit_price: Decimal
    ) -> Order:
        """Execute a limit order with intelligent pricing."""
        pass
    
    @abstractmethod
    async def execute_smart_order(
        self,
        symbol: Symbol,
        side: OrderSide,
        quantity: int,
        max_slippage: float = 0.01
    ) -> Order:
        """Execute order with optimal strategy (market vs limit)."""
        pass
    
    @abstractmethod
    def calculate_optimal_limit_price(
        self,
        symbol: Symbol,
        side: OrderSide,
        spread_threshold: float = 0.005
    ) -> Optional[Decimal]:
        """Calculate optimal limit price based on market conditions."""
        pass


class ITradeAnalyzer(ABC):
    """Interface for trade analysis and reporting."""
    
    @abstractmethod
    async def analyze_trade(self, trade: Trade) -> Dict[str, Any]:
        """Analyze a completed trade for insights."""
        pass
    
    @abstractmethod
    async def get_trade_history(
        self,
        symbol: Optional[Symbol] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Trade]:
        """Get trade history with optional filters."""
        pass
    
    @abstractmethod
    async def calculate_strategy_performance(self, strategy_name: str) -> Dict[str, Any]:
        """Calculate performance metrics for a specific strategy."""
        pass
    
    @abstractmethod
    async def generate_trade_report(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive trade report."""
        pass