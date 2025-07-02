"""
Strategy interfaces.

This module defines the contracts for trading strategies, signal generation,
backtesting, and strategy optimization.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime
import pandas as pd

from ..domain import (
    Symbol, TradingSignal, SignalType, StrategyType,
    Bar, Quote, PerformanceMetrics
)


class IStrategy(ABC):
    """Base interface for trading strategies."""
    
    @abstractmethod
    async def generate_signal(
        self,
        symbol: Symbol,
        current_data: Optional[pd.DataFrame] = None
    ) -> Optional[TradingSignal]:
        """Generate trading signal for a symbol."""
        pass
    
    @abstractmethod
    async def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        pass
    
    @abstractmethod
    async def get_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters."""
        pass
    
    @abstractmethod
    async def get_required_data_period(self) -> int:
        """Get minimum data period required in days."""
        pass
    
    @abstractmethod
    async def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate generated signal."""
        pass
    
    @property
    @abstractmethod
    def strategy_type(self) -> StrategyType:
        """Get strategy type."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get strategy name."""
        pass


class ITrendStrategy(ABC):
    """Interface for trend-following strategies."""
    
    @abstractmethod
    async def calculate_trend_strength(
        self,
        symbol: Symbol,
        data: pd.DataFrame
    ) -> float:
        """Calculate trend strength (0-1)."""
        pass
    
    @abstractmethod
    async def identify_trend_direction(
        self,
        symbol: Symbol,
        data: pd.DataFrame
    ) -> str:
        """Identify trend direction: 'up', 'down', 'sideways'."""
        pass
    
    @abstractmethod
    async def calculate_moving_averages(
        self,
        data: pd.DataFrame,
        periods: List[int]
    ) -> Dict[int, pd.Series]:
        """Calculate multiple moving averages."""
        pass
    
    @abstractmethod
    async def calculate_macd(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        pass


class IMeanReversionStrategy(ABC):
    """Interface for mean reversion strategies."""
    
    @abstractmethod
    async def calculate_mean_reversion_score(
        self,
        symbol: Symbol,
        data: pd.DataFrame
    ) -> float:
        """Calculate mean reversion score (0-1)."""
        pass
    
    @abstractmethod
    async def calculate_rsi(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate RSI indicator."""
        pass
    
    @abstractmethod
    async def calculate_bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        pass
    
    @abstractmethod
    async def calculate_z_score(
        self,
        data: pd.DataFrame,
        period: int = 20
    ) -> pd.Series:
        """Calculate Z-score for mean reversion."""
        pass


class IMomentumStrategy(ABC):
    """Interface for momentum strategies."""
    
    @abstractmethod
    async def calculate_momentum_score(
        self,
        symbol: Symbol,
        data: pd.DataFrame
    ) -> float:
        """Calculate momentum score (0-1)."""
        pass
    
    @abstractmethod
    async def calculate_rate_of_change(
        self,
        data: pd.DataFrame,
        period: int = 10
    ) -> pd.Series:
        """Calculate rate of change."""
        pass
    
    @abstractmethod
    async def calculate_stochastic(
        self,
        data: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """Calculate Stochastic oscillator."""
        pass


class IMLStrategy(ABC):
    """Interface for machine learning strategies."""
    
    @abstractmethod
    async def train_model(
        self,
        training_data: pd.DataFrame,
        target_column: str = "returns"
    ) -> bool:
        """Train the ML model."""
        pass
    
    @abstractmethod
    async def predict_signal(
        self,
        symbol: Symbol,
        features: pd.DataFrame
    ) -> TradingSignal:
        """Generate signal using ML model."""
        pass
    
    @abstractmethod
    async def extract_features(
        self,
        symbol: Symbol,
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """Extract features for ML model."""
        pass
    
    @abstractmethod
    async def evaluate_model(
        self,
        test_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Evaluate model performance."""
        pass
    
    @abstractmethod
    async def retrain_if_needed(self) -> bool:
        """Check if model needs retraining and retrain if needed."""
        pass


class IStrategyComposer(ABC):
    """Interface for combining multiple strategies."""
    
    @abstractmethod
    async def add_strategy(self, strategy: IStrategy, weight: float = 1.0) -> None:
        """Add strategy to the composition."""
        pass
    
    @abstractmethod
    async def remove_strategy(self, strategy_name: str) -> None:
        """Remove strategy from composition."""
        pass
    
    @abstractmethod
    async def generate_composite_signal(
        self,
        symbol: Symbol,
        current_data: Optional[pd.DataFrame] = None
    ) -> Optional[TradingSignal]:
        """Generate composite signal from all strategies."""
        pass
    
    @abstractmethod
    async def update_weights(self, weights: Dict[str, float]) -> None:
        """Update strategy weights."""
        pass
    
    @abstractmethod
    async def get_strategy_performance(self) -> Dict[str, PerformanceMetrics]:
        """Get performance metrics for each strategy."""
        pass


class ISignalFilter(ABC):
    """Interface for filtering trading signals."""
    
    @abstractmethod
    async def filter_signal(
        self,
        signal: TradingSignal,
        context: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """Filter and potentially modify trading signal."""
        pass
    
    @abstractmethod
    async def validate_market_conditions(self, symbol: Symbol) -> bool:
        """Validate current market conditions for trading."""
        pass
    
    @abstractmethod
    async def check_volume_filter(self, symbol: Symbol, min_volume: int) -> bool:
        """Check if symbol meets volume requirements."""
        pass
    
    @abstractmethod
    async def check_volatility_filter(
        self,
        symbol: Symbol,
        min_volatility: float,
        max_volatility: float
    ) -> bool:
        """Check if symbol meets volatility requirements."""
        pass


class IBacktester(ABC):
    """Interface for strategy backtesting."""
    
    @abstractmethod
    async def run_backtest(
        self,
        strategy: IStrategy,
        symbols: List[Symbol],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        """Run backtest for strategy."""
        pass
    
    @abstractmethod
    async def calculate_performance_metrics(
        self,
        trades: List[Dict[str, Any]],
        portfolio_values: List[float]
    ) -> PerformanceMetrics:
        """Calculate performance metrics from backtest results."""
        pass
    
    @abstractmethod
    async def generate_backtest_report(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive backtest report."""
        pass
    
    @abstractmethod
    async def plot_results(
        self,
        results: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> None:
        """Plot backtest results."""
        pass


class IStrategyOptimizer(ABC):
    """Interface for strategy parameter optimization."""
    
    @abstractmethod
    async def optimize_parameters(
        self,
        strategy: IStrategy,
        parameter_ranges: Dict[str, tuple],
        optimization_metric: str = "sharpe_ratio",
        symbols: Optional[List[Symbol]] = None
    ) -> Dict[str, Any]:
        """Optimize strategy parameters."""
        pass
    
    @abstractmethod
    async def walk_forward_analysis(
        self,
        strategy: IStrategy,
        symbols: List[Symbol],
        optimization_window: int = 252,
        test_window: int = 63
    ) -> Dict[str, Any]:
        """Perform walk-forward analysis."""
        pass
    
    @abstractmethod
    async def monte_carlo_simulation(
        self,
        strategy: IStrategy,
        symbols: List[Symbol],
        num_simulations: int = 1000
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation for strategy."""
        pass


class ITechnicalIndicators(ABC):
    """Interface for technical indicator calculations."""
    
    @abstractmethod
    async def calculate_atr(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Average True Range."""
        pass
    
    @abstractmethod
    async def calculate_adx(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """Calculate Average Directional Index."""
        pass
    
    @abstractmethod
    async def calculate_obv(self, data: pd.DataFrame) -> pd.Series:
        """Calculate On Balance Volume."""
        pass
    
    @abstractmethod
    async def calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price."""
        pass
    
    @abstractmethod
    async def calculate_ichimoku(
        self,
        data: pd.DataFrame,
        conversion_period: int = 9,
        base_period: int = 26,
        leading_span_b_period: int = 52
    ) -> Dict[str, pd.Series]:
        """Calculate Ichimoku Cloud indicators."""
        pass