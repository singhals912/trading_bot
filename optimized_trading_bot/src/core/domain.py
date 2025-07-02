"""
Domain models for the trading bot system.

This module contains the core data structures and business entities
used throughout the trading system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIALLY_FILLED = "partially_filled"


class PositionSide(Enum):
    """Position side enumeration."""
    LONG = "long"
    SHORT = "short"


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class StrategyType(Enum):
    """Strategy type enumeration."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    COMBINED = "combined"
    ML_ENHANCED = "ml_enhanced"


class MarketSession(Enum):
    """Market session types."""
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"


@dataclass(frozen=True)
class Symbol:
    """Represents a tradeable symbol."""
    ticker: str
    exchange: str = "NASDAQ"
    currency: str = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    def __str__(self) -> str:
        return self.ticker


@dataclass(frozen=True)
class Quote:
    """Real-time market quote."""
    symbol: Symbol
    bid: Decimal
    ask: Decimal
    bid_size: int
    ask_size: int
    timestamp: datetime
    
    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread."""
        return self.ask - self.bid
    
    @property
    def spread_pct(self) -> Decimal:
        """Calculate spread as percentage of ask price."""
        return (self.spread / self.ask) * 100 if self.ask > 0 else Decimal(0)
    
    @property
    def mid_price(self) -> Decimal:
        """Calculate mid-point price."""
        return (self.bid + self.ask) / 2


@dataclass(frozen=True)
class Bar:
    """OHLCV bar data."""
    symbol: Symbol
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    
    @property
    def typical_price(self) -> Decimal:
        """Calculate typical price (HLC/3)."""
        return (self.high + self.low + self.close) / 3
    
    @property
    def range_pct(self) -> Decimal:
        """Calculate range as percentage of close."""
        range_val = self.high - self.low
        return (range_val / self.close) * 100 if self.close > 0 else Decimal(0)


@dataclass
class TradingSignal:
    """Trading signal with confidence and metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: Symbol = field(default_factory=lambda: Symbol(""))
    signal_type: SignalType = SignalType.HOLD
    confidence: float = 0.0
    price: Optional[Decimal] = None
    strategy_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate signal data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass
class Order:
    """Trading order representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: Symbol = field(default_factory=lambda: Symbol(""))
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    quantity: int = 0
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    filled_quantity: int = 0
    filled_price: Optional[Decimal] = None
    commission: Decimal = field(default_factory=lambda: Decimal(0))
    broker_order_id: Optional[str] = None
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity
    
    @property
    def notional_value(self) -> Optional[Decimal]:
        """Calculate notional value of order."""
        if self.price is not None:
            return self.price * self.quantity
        return None


@dataclass
class Position:
    """Trading position representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: Symbol = field(default_factory=lambda: Symbol(""))
    side: PositionSide = PositionSide.LONG
    quantity: int = 0
    entry_price: Decimal = field(default_factory=lambda: Decimal(0))
    current_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    strategy_name: str = ""
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    entry_order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def market_value(self) -> Optional[Decimal]:
        """Calculate current market value."""
        if self.current_price is not None:
            return self.current_price * abs(self.quantity)
        return None
    
    @property
    def unrealized_pnl(self) -> Optional[Decimal]:
        """Calculate unrealized P&L."""
        if self.current_price is None:
            return None
            
        if self.side == PositionSide.LONG:
            return (self.current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - self.current_price) * abs(self.quantity)
    
    @property
    def unrealized_pnl_pct(self) -> Optional[float]:
        """Calculate unrealized P&L percentage."""
        if self.unrealized_pnl is None or self.entry_price == 0:
            return None
        return float((self.unrealized_pnl / (self.entry_price * abs(self.quantity))) * 100)


@dataclass
class Trade:
    """Completed trade representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: Symbol = field(default_factory=lambda: Symbol(""))
    side: OrderSide = OrderSide.BUY
    quantity: int = 0
    entry_price: Decimal = field(default_factory=lambda: Decimal(0))
    exit_price: Decimal = field(default_factory=lambda: Decimal(0))
    entry_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exit_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    strategy_name: str = ""
    commission: Decimal = field(default_factory=lambda: Decimal(0))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def gross_pnl(self) -> Decimal:
        """Calculate gross P&L."""
        if self.side == OrderSide.BUY:
            return (self.exit_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - self.exit_price) * self.quantity
    
    @property
    def net_pnl(self) -> Decimal:
        """Calculate net P&L after commissions."""
        return self.gross_pnl - self.commission
    
    @property
    def return_pct(self) -> float:
        """Calculate return percentage."""
        if self.entry_price == 0:
            return 0.0
        return float((self.gross_pnl / (self.entry_price * self.quantity)) * 100)
    
    @property
    def duration(self) -> float:
        """Calculate trade duration in hours."""
        delta = self.exit_time - self.entry_time
        return delta.total_seconds() / 3600


@dataclass
class Portfolio:
    """Portfolio representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cash: Decimal = field(default_factory=lambda: Decimal(0))
    positions: Dict[str, Position] = field(default_factory=dict)
    equity: Decimal = field(default_factory=lambda: Decimal(0))
    buying_power: Decimal = field(default_factory=lambda: Decimal(0))
    day_trade_count: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def total_market_value(self) -> Decimal:
        """Calculate total market value of positions."""
        total = Decimal(0)
        for position in self.positions.values():
            if position.market_value is not None:
                total += position.market_value
        return total
    
    @property
    def total_unrealized_pnl(self) -> Decimal:
        """Calculate total unrealized P&L."""
        total = Decimal(0)
        for position in self.positions.values():
            if position.unrealized_pnl is not None:
                total += position.unrealized_pnl
        return total
    
    @property
    def position_count(self) -> int:
        """Get number of open positions."""
        return len(self.positions)


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio/position."""
    value_at_risk: Optional[Decimal] = None
    expected_shortfall: Optional[Decimal] = None
    beta: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    correlation_score: Optional[float] = None
    leverage: Optional[float] = None
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PerformanceMetrics:
    """Performance metrics for strategies/portfolio."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: Decimal = field(default_factory=lambda: Decimal(0))
    gross_profit: Decimal = field(default_factory=lambda: Decimal(0))
    gross_loss: Decimal = field(default_factory=lambda: Decimal(0))
    largest_win: Decimal = field(default_factory=lambda: Decimal(0))
    largest_loss: Decimal = field(default_factory=lambda: Decimal(0))
    avg_win: Decimal = field(default_factory=lambda: Decimal(0))
    avg_loss: Decimal = field(default_factory=lambda: Decimal(0))
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    def update_from_trade(self, trade: Trade) -> None:
        """Update metrics from a completed trade."""
        self.total_trades += 1
        self.total_pnl += trade.net_pnl
        
        if trade.net_pnl > 0:
            self.winning_trades += 1
            self.gross_profit += trade.net_pnl
            self.largest_win = max(self.largest_win, trade.net_pnl)
        else:
            self.losing_trades += 1
            self.gross_loss += abs(trade.net_pnl)
            self.largest_loss = min(self.largest_loss, trade.net_pnl)
        
        # Recalculate derived metrics
        self._calculate_derived_metrics()
    
    def _calculate_derived_metrics(self) -> None:
        """Calculate derived performance metrics."""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
            
        if self.winning_trades > 0:
            self.avg_win = self.gross_profit / self.winning_trades
            
        if self.losing_trades > 0:
            self.avg_loss = self.gross_loss / self.losing_trades
            
        if self.gross_loss > 0:
            self.profit_factor = float(self.gross_profit / self.gross_loss)


# Event types for the event system
@dataclass
class Event:
    """Base event class."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketDataEvent(Event):
    """Market data update event."""
    symbol: Symbol = field(default_factory=lambda: Symbol(""))
    quote: Optional[Quote] = None
    bar: Optional[Bar] = None
    event_type: str = "market_data"


@dataclass
class TradingEvent(Event):
    """Trading-related event."""
    order: Optional[Order] = None
    position: Optional[Position] = None
    trade: Optional[Trade] = None
    event_type: str = "trading"


@dataclass
class RiskEvent(Event):
    """Risk-related event."""
    risk_type: str = ""
    severity: str = "medium"  # low, medium, high, critical
    message: str = ""
    affected_symbols: List[Symbol] = field(default_factory=list)
    event_type: str = "risk"