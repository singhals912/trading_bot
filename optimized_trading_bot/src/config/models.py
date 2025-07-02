"""
Configuration data models.

This module contains typed configuration classes with validation
for all aspects of the trading bot.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from decimal import Decimal
from enum import Enum


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EnvironmentType(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ApiCredentials:
    """API credentials configuration."""
    key_id: str
    secret_key: str
    base_url: Optional[str] = None
    paper_trading: bool = True
    
    def __post_init__(self):
        if not self.key_id or not self.secret_key:
            raise ValueError("API key_id and secret_key are required")


@dataclass
class TradingConfig:
    """Trading engine configuration."""
    # Capital Management
    total_capital: Decimal = field(default_factory=lambda: Decimal("50000"))
    trading_capital: Decimal = field(default_factory=lambda: Decimal("10000"))
    cash_reserve_pct: float = 0.05  # 5% cash reserve
    
    # Position Management
    max_positions: int = 3
    max_position_size_pct: float = 0.1  # 10% of portfolio per position
    min_position_size: Decimal = field(default_factory=lambda: Decimal("100"))
    
    # Order Management
    default_order_type: str = "limit"
    order_timeout_seconds: int = 300
    max_slippage_pct: float = 0.01  # 1% max slippage
    
    # Trading Sessions
    enable_extended_hours: bool = True
    pre_market_start: str = "04:00"
    regular_market_start: str = "09:30"
    regular_market_end: str = "16:00"
    after_hours_end: str = "20:00"
    
    # Strategy Settings
    strategy_type: str = "combined"
    strategy_weights: Dict[str, float] = field(default_factory=lambda: {
        "trend_following": 0.4,
        "mean_reversion": 0.3,
        "momentum": 0.3
    })
    
    def __post_init__(self):
        if self.trading_capital > self.total_capital:
            raise ValueError("Trading capital cannot exceed total capital")
        if not 0 < self.max_position_size_pct <= 1:
            raise ValueError("Max position size percentage must be between 0 and 1")
        if self.max_positions <= 0:
            raise ValueError("Max positions must be positive")


@dataclass  
class RiskConfig:
    """Risk management configuration."""
    # Daily Limits
    max_daily_loss_pct: float = 0.02  # 2% max daily loss
    max_daily_trades: int = 20
    max_consecutive_losses: int = 3
    
    # Position Risk
    default_stop_loss_pct: float = 0.02  # 2% stop loss
    default_take_profit_pct: float = 0.04  # 4% take profit
    trailing_stop_enabled: bool = True
    trailing_stop_pct: float = 0.01  # 1% trailing stop
    
    # Portfolio Risk
    max_correlation: float = 0.7  # Max 70% correlation between positions
    max_sector_concentration: float = 0.5  # Max 50% in one sector
    max_portfolio_volatility: float = 0.2  # Max 20% annualized volatility
    
    # Volatility Management
    volatility_lookback_days: int = 30
    volatility_adjustment_factor: float = 1.5
    atr_multiplier: float = 2.0
    
    # Circuit Breakers
    enable_circuit_breakers: bool = True
    max_drawdown_halt: float = 0.1  # Halt at 10% drawdown
    volatility_halt_threshold: float = 0.05  # Halt at 5% daily volatility
    
    def __post_init__(self):
        if not 0 < self.max_daily_loss_pct <= 1:
            raise ValueError("Max daily loss percentage must be between 0 and 1")
        if not 0 < self.max_correlation <= 1:
            raise ValueError("Max correlation must be between 0 and 1")


@dataclass
class DataConfig:
    """Data provider configuration."""
    # Primary Data Source
    primary_provider: str = "alpaca"
    backup_providers: List[str] = field(default_factory=lambda: [
        "yfinance", "alpha_vantage", "iex"
    ])
    
    # Data Caching
    enable_caching: bool = True
    cache_provider: str = "redis"  # redis, memory, file
    cache_ttl_quotes: int = 5  # seconds
    cache_ttl_bars: int = 300  # seconds
    cache_ttl_fundamentals: int = 86400  # 24 hours
    
    # Data Quality
    enable_data_validation: bool = True
    max_price_change_pct: float = 0.2  # 20% max price change filter
    min_volume_threshold: int = 100000
    
    # Historical Data
    default_timeframe: str = "1D"
    max_historical_days: int = 365
    warm_up_period_days: int = 100
    
    # Real-time Data
    enable_streaming: bool = True
    stream_buffer_size: int = 1000
    reconnect_attempts: int = 5
    reconnect_delay_seconds: int = 5
    
    # Rate Limiting
    api_calls_per_minute: int = 200
    api_calls_per_hour: int = 10000
    enable_rate_limiting: bool = True


@dataclass
class NotificationConfig:
    """Notification system configuration."""
    # General Settings
    enable_notifications: bool = True
    notification_levels: List[str] = field(default_factory=lambda: [
        "critical", "error", "warning"
    ])
    
    # Email Configuration
    email_enabled: bool = False
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    
    # SMS Configuration (Twilio)
    sms_enabled: bool = False
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    sms_recipients: List[str] = field(default_factory=list)
    
    # Webhook Configuration
    webhook_enabled: bool = False
    webhook_urls: List[str] = field(default_factory=list)
    webhook_timeout_seconds: int = 10
    
    # Alert Throttling
    enable_throttling: bool = True
    min_alert_interval_seconds: int = 300  # 5 minutes
    max_alerts_per_hour: int = 20


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    # General Monitoring
    enable_monitoring: bool = True
    metrics_collection_interval: int = 60  # seconds
    health_check_interval: int = 30  # seconds
    
    # Dashboard
    dashboard_enabled: bool = True
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8080
    dashboard_auto_refresh: int = 30  # seconds
    
    # Remote Access
    enable_remote_access: bool = True
    ngrok_enabled: bool = True
    ngrok_auth_token: Optional[str] = None
    
    # Metrics Export
    prometheus_enabled: bool = True
    prometheus_port: int = 8000
    prometheus_metrics_prefix: str = "trading_bot"
    
    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = True
    log_file_path: str = "logs/trading_bot.log"
    log_max_file_size: str = "10MB"
    log_backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance Monitoring
    enable_profiling: bool = False
    profile_output_dir: str = "logs/profiles"
    track_memory_usage: bool = True
    track_cpu_usage: bool = True


@dataclass
class MLConfig:
    """Machine Learning configuration."""
    # General ML Settings
    enable_ml: bool = False
    model_type: str = "ensemble"  # ensemble, xgboost, lstm, transformer
    feature_engineering_enabled: bool = True
    
    # Model Training
    training_data_days: int = 252  # 1 year
    retrain_interval_days: int = 30
    min_training_samples: int = 1000
    validation_split: float = 0.2
    
    # Feature Engineering
    technical_indicators: List[str] = field(default_factory=lambda: [
        "rsi", "macd", "bollinger", "atr", "sma", "ema"
    ])
    fundamental_features: bool = False
    sentiment_features: bool = False
    
    # Model Performance
    min_accuracy_threshold: float = 0.55
    min_sharpe_ratio: float = 1.0
    max_drawdown_threshold: float = 0.15
    
    # Prediction
    confidence_threshold: float = 0.6
    enable_ensemble_voting: bool = True
    prediction_horizon_hours: int = 24


@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    # General Settings
    initial_capital: Decimal = field(default_factory=lambda: Decimal("100000"))
    commission_per_trade: Decimal = field(default_factory=lambda: Decimal("1.0"))
    slippage_model: str = "percentage"  # fixed, percentage, volume
    slippage_value: float = 0.001  # 0.1%
    
    # Time Settings
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    benchmark_symbol: str = "SPY"
    
    # Execution Settings
    order_delay_seconds: int = 0
    partial_fill_enabled: bool = True
    after_hours_trading: bool = False
    
    # Reporting
    generate_plots: bool = True
    plot_output_dir: str = "backtests/plots"
    save_trade_log: bool = True
    trade_log_path: str = "backtests/trades.csv"


@dataclass
class BotConfiguration:
    """Main bot configuration container."""
    # Environment
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    bot_name: str = "OptimizedTradingBot"
    version: str = "2.0.0"
    
    # Core Configurations
    api_credentials: ApiCredentials = field(default_factory=lambda: ApiCredentials("", ""))
    trading: TradingConfig = field(default_factory=TradingConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    data: DataConfig = field(default_factory=DataConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Optional Configurations
    ml: Optional[MLConfig] = None
    backtest: Optional[BacktestConfig] = None
    
    # Custom Settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate the complete configuration."""
        # Validate capital allocation
        if self.trading.trading_capital > self.trading.total_capital:
            raise ValueError("Trading capital cannot exceed total capital")
        
        # Validate risk settings
        max_position_value = (
            self.trading.trading_capital * 
            Decimal(str(self.trading.max_position_size_pct))
        )
        max_total_exposure = max_position_value * self.trading.max_positions
        if max_total_exposure > self.trading.trading_capital:
            raise ValueError("Maximum total exposure exceeds trading capital")
        
        # Validate environment-specific settings
        if self.environment == EnvironmentType.PRODUCTION:
            if self.api_credentials.paper_trading:
                raise ValueError("Production environment cannot use paper trading")
            if not self.notifications.enable_notifications:
                raise ValueError("Production environment must have notifications enabled")
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == EnvironmentType.PRODUCTION
    
    def is_paper_trading(self) -> bool:
        """Check if using paper trading."""
        return self.api_credentials.paper_trading
    
    def get_effective_capital(self) -> Decimal:
        """Get effective trading capital after reserves."""
        reserve_amount = self.trading.total_capital * Decimal(str(self.trading.cash_reserve_pct))
        return min(self.trading.trading_capital, self.trading.total_capital - reserve_amount)