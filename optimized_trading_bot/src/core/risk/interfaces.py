"""
Risk management interfaces.

This module defines the contracts for risk management services including
position sizing, portfolio risk, correlation analysis, and risk monitoring.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from ..domain import (
    Position, Portfolio, Symbol, TradingSignal, RiskMetrics,
    RiskEvent, Order
)


class IRiskManager(ABC):
    """Main interface for risk management operations."""
    
    @abstractmethod
    async def assess_trade_risk(
        self,
        signal: TradingSignal,
        quantity: int,
        portfolio: Portfolio
    ) -> Dict[str, Any]:
        """Assess risk for a potential trade."""
        pass
    
    @abstractmethod
    async def can_open_position(
        self,
        signal: TradingSignal,
        quantity: int,
        portfolio: Portfolio
    ) -> Tuple[bool, str]:
        """Check if position can be opened based on risk limits."""
        pass
    
    @abstractmethod
    async def calculate_position_size(
        self,
        signal: TradingSignal,
        portfolio: Portfolio,
        risk_amount: Decimal
    ) -> int:
        """Calculate optimal position size for trade."""
        pass
    
    @abstractmethod
    async def check_portfolio_limits(self, portfolio: Portfolio) -> List[RiskEvent]:
        """Check portfolio against risk limits."""
        pass
    
    @abstractmethod
    async def get_risk_metrics(self, portfolio: Portfolio) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        pass


class IPositionSizer(ABC):
    """Interface for position sizing algorithms."""
    
    @abstractmethod
    async def calculate_size_fixed_dollar(
        self,
        signal: TradingSignal,
        risk_amount: Decimal
    ) -> int:
        """Calculate position size using fixed dollar risk."""
        pass
    
    @abstractmethod
    async def calculate_size_kelly_criterion(
        self,
        signal: TradingSignal,
        win_rate: float,
        avg_win: Decimal,
        avg_loss: Decimal,
        portfolio_value: Decimal
    ) -> int:
        """Calculate position size using Kelly Criterion."""
        pass
    
    @abstractmethod
    async def calculate_size_volatility_adjusted(
        self,
        signal: TradingSignal,
        volatility: float,
        target_volatility: float,
        portfolio_value: Decimal
    ) -> int:
        """Calculate position size adjusted for volatility."""
        pass
    
    @abstractmethod
    async def calculate_size_correlation_adjusted(
        self,
        signal: TradingSignal,
        portfolio: Portfolio,
        correlation_limit: float = 0.7
    ) -> int:
        """Calculate position size adjusted for portfolio correlation."""
        pass


class IStopLossManager(ABC):
    """Interface for stop loss management."""
    
    @abstractmethod
    async def calculate_stop_loss(
        self,
        position: Position,
        method: str = "atr"
    ) -> Optional[Decimal]:
        """Calculate stop loss price for position."""
        pass
    
    @abstractmethod
    async def update_trailing_stop(
        self,
        position: Position,
        current_price: Decimal
    ) -> Optional[Decimal]:
        """Update trailing stop loss."""
        pass
    
    @abstractmethod
    async def check_stop_conditions(self, position: Position) -> bool:
        """Check if stop loss should be triggered."""
        pass
    
    @abstractmethod
    async def calculate_atr_stop(
        self,
        symbol: Symbol,
        entry_price: Decimal,
        atr_multiplier: float = 2.0
    ) -> Optional[Decimal]:
        """Calculate ATR-based stop loss."""
        pass
    
    @abstractmethod
    async def calculate_support_resistance_stop(
        self,
        symbol: Symbol,
        entry_price: Decimal
    ) -> Optional[Decimal]:
        """Calculate stop loss based on support/resistance."""
        pass


class ICorrelationAnalyzer(ABC):
    """Interface for portfolio correlation analysis."""
    
    @abstractmethod
    async def calculate_correlation_matrix(
        self,
        symbols: List[Symbol],
        period_days: int = 30
    ) -> Dict[Tuple[Symbol, Symbol], float]:
        """Calculate correlation matrix for symbols."""
        pass
    
    @abstractmethod
    async def get_portfolio_correlation(self, portfolio: Portfolio) -> float:
        """Calculate average correlation of portfolio positions."""
        pass
    
    @abstractmethod
    async def assess_correlation_risk(
        self,
        new_symbol: Symbol,
        portfolio: Portfolio,
        threshold: float = 0.7
    ) -> Tuple[bool, float]:
        """Assess correlation risk of adding new symbol."""
        pass
    
    @abstractmethod
    async def find_diversification_opportunities(
        self,
        portfolio: Portfolio,
        candidate_symbols: List[Symbol]
    ) -> List[Symbol]:
        """Find symbols that would improve portfolio diversification."""
        pass


class IVolatilityAnalyzer(ABC):
    """Interface for volatility analysis."""
    
    @abstractmethod
    async def calculate_realized_volatility(
        self,
        symbol: Symbol,
        period_days: int = 30
    ) -> Optional[float]:
        """Calculate realized volatility for symbol."""
        pass
    
    @abstractmethod
    async def calculate_portfolio_volatility(self, portfolio: Portfolio) -> Optional[float]:
        """Calculate portfolio volatility."""
        pass
    
    @abstractmethod
    async def calculate_var(
        self,
        portfolio: Portfolio,
        confidence_level: float = 0.95,
        time_horizon_days: int = 1
    ) -> Optional[Decimal]:
        """Calculate Value at Risk."""
        pass
    
    @abstractmethod
    async def calculate_expected_shortfall(
        self,
        portfolio: Portfolio,
        confidence_level: float = 0.95
    ) -> Optional[Decimal]:
        """Calculate Expected Shortfall (CVaR)."""
        pass


class IDrawdownAnalyzer(ABC):
    """Interface for drawdown analysis."""
    
    @abstractmethod
    async def calculate_current_drawdown(self, portfolio: Portfolio) -> float:
        """Calculate current portfolio drawdown."""
        pass
    
    @abstractmethod
    async def calculate_maximum_drawdown(
        self,
        portfolio_history: List[Portfolio]
    ) -> float:
        """Calculate maximum historical drawdown."""
        pass
    
    @abstractmethod
    async def estimate_recovery_time(
        self,
        current_drawdown: float,
        historical_data: List[Portfolio]
    ) -> Optional[int]:
        """Estimate drawdown recovery time in days."""
        pass
    
    @abstractmethod
    async def check_drawdown_limits(
        self,
        portfolio: Portfolio,
        max_drawdown: float = 0.1
    ) -> bool:
        """Check if drawdown exceeds limits."""
        pass


class IRiskMonitor(ABC):
    """Interface for continuous risk monitoring."""
    
    @abstractmethod
    async def monitor_positions(self, positions: List[Position]) -> List[RiskEvent]:
        """Monitor positions for risk events."""
        pass
    
    @abstractmethod
    async def monitor_portfolio(self, portfolio: Portfolio) -> List[RiskEvent]:
        """Monitor portfolio for risk events."""
        pass
    
    @abstractmethod
    async def check_concentration_risk(self, portfolio: Portfolio) -> List[RiskEvent]:
        """Check for position concentration risk."""
        pass
    
    @abstractmethod
    async def check_leverage_risk(self, portfolio: Portfolio) -> List[RiskEvent]:
        """Check for excessive leverage."""
        pass
    
    @abstractmethod
    async def check_liquidity_risk(self, positions: List[Position]) -> List[RiskEvent]:
        """Check for liquidity risk in positions."""
        pass
    
    @abstractmethod
    async def generate_risk_report(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Generate comprehensive risk report."""
        pass


class ICircuitBreaker(ABC):
    """Interface for circuit breaker functionality."""
    
    @abstractmethod
    async def check_daily_loss_limit(
        self,
        portfolio: Portfolio,
        daily_loss_limit: float
    ) -> bool:
        """Check if daily loss limit is breached."""
        pass
    
    @abstractmethod
    async def check_position_limit(
        self,
        portfolio: Portfolio,
        max_positions: int
    ) -> bool:
        """Check if position limit is breached."""
        pass
    
    @abstractmethod
    async def check_exposure_limit(
        self,
        portfolio: Portfolio,
        max_exposure: float
    ) -> bool:
        """Check if exposure limit is breached."""
        pass
    
    @abstractmethod
    async def trigger_emergency_stop(self, reason: str) -> None:
        """Trigger emergency trading stop."""
        pass
    
    @abstractmethod
    async def is_trading_halted(self) -> bool:
        """Check if trading is currently halted."""
        pass