"""
Configuration providers for the trading bot.

This module provides different sources for configuration data including
files, environment variables, and other sources.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import yaml
import json

from .interfaces import IConfigurationProvider


class FileConfigProvider(IConfigurationProvider):
    """
    Configuration provider that loads from YAML or JSON files.
    """
    
    def __init__(
        self,
        config_file_path: Union[str, Path],
        logger: Optional[logging.Logger] = None
    ):
        self.config_file_path = Path(config_file_path)
        self.logger = logger or logging.getLogger(__name__)
        self._config = None
    
    async def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if not self.config_file_path.exists():
                self.logger.warning(f"Config file not found: {self.config_file_path}")
                return {}
            
            with open(self.config_file_path, 'r') as f:
                if self.config_file_path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f) or {}
                elif self.config_file_path.suffix.lower() == '.json':
                    config = json.load(f) or {}
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_file_path.suffix}")
            
            self.logger.info(f"Loaded configuration from {self.config_file_path}")
            self._config = config
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_file_path}: {e}")
            return {}
    
    async def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_file_path, 'w') as f:
                if self.config_file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(config, f, default_flow_style=False, indent=2)
                elif self.config_file_path.suffix.lower() == '.json':
                    json.dump(config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_file_path.suffix}")
            self._config = config
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config to {self.config_file_path}: {e}")
            return False
    
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get specific configuration value."""
        if self._config is None:
            await self.load_configuration()
        
        keys = key.split('.')
        value = self._config or {}
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    async def set_value(self, key: str, value: Any) -> bool:
        """Set specific configuration value."""
        if self._config is None:
            await self.load_configuration()
        
        if self._config is None:
            self._config = {}
        
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        return await self.save_configuration(self._config)
    
    async def has_key(self, key: str) -> bool:
        """Check if configuration key exists."""
        try:
            if self._config is None:
                await self.load_configuration()
            
            keys = key.split('.')
            value = self._config or {}
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return False
            return True
        except:
            return False
    
    async def get_all_keys(self) -> List[str]:
        """Get all configuration keys."""
        if self._config is None:
            await self.load_configuration()
        
        config = self._config or {}
        keys = []
        
        def _extract_keys(obj, prefix=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    keys.append(current_key)
                    if isinstance(value, dict):
                        _extract_keys(value, current_key)
        
        _extract_keys(config)
        return keys
    
    @property
    def provider_name(self) -> str:
        """Get provider name for identification."""
        return f"file:{self.config_file_path.name}"
    
    @property
    def priority(self) -> int:
        """Get provider priority (higher = more important)."""
        return 20  # Medium priority


class EnvironmentConfigProvider(IConfigurationProvider):
    """
    Configuration provider that loads from environment variables.
    """
    
    def __init__(
        self,
        prefix: str = "TRADING_BOT_",
        logger: Optional[logging.Logger] = None
    ):
        self.prefix = prefix
        self.logger = logger or logging.getLogger(__name__)
    
    async def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        try:
            config = {}
            
            # API Configuration - check both prefixed and Alpaca standard names
            api_key_id = (os.getenv(f"{self.prefix}API_KEY_ID") or 
                         os.getenv("APCA_API_KEY_ID") or 
                         os.getenv("ALPACA_API_KEY_ID"))
            api_secret_key = (os.getenv(f"{self.prefix}API_SECRET_KEY") or 
                             os.getenv("APCA_API_SECRET_KEY") or 
                             os.getenv("ALPACA_API_SECRET_KEY"))
            
            if api_key_id or api_secret_key:
                config['api'] = {
                    'key_id': api_key_id or '',
                    'secret_key': api_secret_key or '',
                    'base_url': os.getenv(f"{self.prefix}API_BASE_URL", 'https://paper-api.alpaca.markets'),
                    'paper_trading': os.getenv("PAPER_TRADING", 'true').lower() == 'true'
                }
            
            # Trading Configuration
            trading_config = {}
            if os.getenv(f"{self.prefix}MAX_POSITIONS"):
                trading_config['max_positions'] = int(os.getenv(f"{self.prefix}MAX_POSITIONS"))
            if os.getenv(f"{self.prefix}POSITION_SIZE_PERCENT"):
                trading_config['position_size_percent'] = float(os.getenv(f"{self.prefix}POSITION_SIZE_PERCENT"))
            if os.getenv(f"{self.prefix}PAPER_TRADING"):
                trading_config['paper_trading'] = os.getenv(f"{self.prefix}PAPER_TRADING").lower() == 'true'
            
            if trading_config:
                config['trading'] = trading_config
            
            # Risk Configuration
            risk_config = {}
            if os.getenv(f"{self.prefix}MAX_PORTFOLIO_RISK"):
                risk_config['max_portfolio_risk'] = float(os.getenv(f"{self.prefix}MAX_PORTFOLIO_RISK"))
            if os.getenv(f"{self.prefix}MAX_POSITION_RISK"):
                risk_config['max_position_risk'] = float(os.getenv(f"{self.prefix}MAX_POSITION_RISK"))
            if os.getenv(f"{self.prefix}STOP_LOSS_PERCENT"):
                risk_config['stop_loss_percent'] = float(os.getenv(f"{self.prefix}STOP_LOSS_PERCENT"))
            
            if risk_config:
                config['risk'] = risk_config
            
            # Data Configuration
            data_config = {}
            if os.getenv(f"{self.prefix}DATA_PROVIDER"):
                data_config['provider'] = os.getenv(f"{self.prefix}DATA_PROVIDER")
            if os.getenv(f"{self.prefix}HISTORICAL_DAYS"):
                data_config['historical_days'] = int(os.getenv(f"{self.prefix}HISTORICAL_DAYS"))
            if os.getenv(f"{self.prefix}REAL_TIME"):
                data_config['real_time'] = os.getenv(f"{self.prefix}REAL_TIME").lower() == 'true'
            
            if data_config:
                config['data'] = data_config
            
            # Monitoring Configuration
            monitoring_config = {}
            if os.getenv(f"{self.prefix}ENABLE_METRICS"):
                monitoring_config['enable_metrics'] = os.getenv(f"{self.prefix}ENABLE_METRICS").lower() == 'true'
            if os.getenv(f"{self.prefix}METRICS_PORT"):
                monitoring_config['metrics_port'] = int(os.getenv(f"{self.prefix}METRICS_PORT"))
            if os.getenv(f"{self.prefix}LOG_LEVEL"):
                monitoring_config['log_level'] = os.getenv(f"{self.prefix}LOG_LEVEL")
            
            if monitoring_config:
                config['monitoring'] = monitoring_config
            
            # Notification Configuration
            notification_config = {}
            if os.getenv(f"{self.prefix}ENABLE_NOTIFICATIONS"):
                notification_config['enabled'] = os.getenv(f"{self.prefix}ENABLE_NOTIFICATIONS").lower() == 'true'
            if os.getenv(f"{self.prefix}EMAIL_ENABLED"):
                notification_config['email_enabled'] = os.getenv(f"{self.prefix}EMAIL_ENABLED").lower() == 'true'
            if os.getenv(f"{self.prefix}SLACK_ENABLED"):
                notification_config['slack_enabled'] = os.getenv(f"{self.prefix}SLACK_ENABLED").lower() == 'true'
            if os.getenv(f"{self.prefix}WEBHOOK_URL"):
                notification_config['webhook_url'] = os.getenv(f"{self.prefix}WEBHOOK_URL")
            
            if notification_config:
                config['notifications'] = notification_config
            
            if config:
                self.logger.info(f"Loaded configuration from environment variables (prefix: {self.prefix})")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config from environment: {e}")
            return {}
    
    async def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Save configuration (not supported for environment provider)."""
        return False
    
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get specific configuration value from environment."""
        env_key = f"{self.prefix}{key.upper().replace('.', '_')}"
        return os.getenv(env_key, default)
    
    async def set_value(self, key: str, value: Any) -> bool:
        """Set specific configuration value (not supported for environment provider)."""
        return False
    
    async def has_key(self, key: str) -> bool:
        """Check if configuration key exists in environment."""
        env_key = f"{self.prefix}{key.upper().replace('.', '_')}"
        return env_key in os.environ
    
    async def get_all_keys(self) -> List[str]:
        """Get all configuration keys from environment."""
        keys = []
        for env_key in os.environ:
            if env_key.startswith(self.prefix):
                config_key = env_key[len(self.prefix):].lower().replace('_', '.')
                keys.append(config_key)
        return keys
    
    @property
    def provider_name(self) -> str:
        """Get provider name for identification."""
        return f"environment:{self.prefix}"
    
    @property
    def priority(self) -> int:
        """Get provider priority (highest priority)."""
        return 100


class DefaultConfigProvider(IConfigurationProvider):
    """
    Configuration provider that provides default values.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._config = None
    
    async def load_configuration(self) -> Dict[str, Any]:
        """Load default configuration."""
        if self._config is None:
            self._config = {
                'trading': {
                    'max_positions': 3,
                    'position_size_percent': 0.02,
                    'paper_trading': True,
                    'hours_start': '09:30',
                    'hours_end': '16:00',
                    'after_hours': False
                },
                'risk': {
                    'max_portfolio_risk': 0.10,
                    'max_position_risk': 0.025,  # Slightly more aggressive as requested
                    'stop_loss_percent': 0.02,
                    'take_profit_percent': 0.04,
                    'max_drawdown_percent': 0.15,
                    'circuit_breaker': True
                },
                'data': {
                    'provider': 'alpaca',
                    'historical_days': 100,
                    'real_time': True,
                    'cache_enabled': True,
                    'cache_duration': 5
                },
                'monitoring': {
                    'enable_metrics': True,
                    'metrics_port': 8000,
                    'dashboard_enabled': True,
                    'dashboard_port': 8080,
                    'log_level': 'INFO'
                },
                'notifications': {
                    'enabled': False,
                    'email_enabled': False,
                    'slack_enabled': False,
                    'webhook_url': ''
                },
                'api': {
                    'base_url': 'https://paper-api.alpaca.markets',
                    'paper_trading': True
                },
                'custom': {
                    'min_signal_confidence': 0.65,  # More aggressive threshold
                    'consensus_threshold': 0.55,    # More aggressive consensus
                    'max_correlation': 0.65,        # Slightly higher correlation limit
                    'confidence_multiplier': 1.3    # Boost for high-confidence signals
                }
            }
        return self._config.copy()
    
    async def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Save configuration (not supported for default provider)."""
        return False
    
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get specific configuration value."""
        config = await self.load_configuration()
        keys = key.split('.')
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    async def set_value(self, key: str, value: Any) -> bool:
        """Set specific configuration value (not supported for default provider)."""
        return False
    
    async def has_key(self, key: str) -> bool:
        """Check if configuration key exists."""
        try:
            config = await self.load_configuration()
            keys = key.split('.')
            value = config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return False
            return True
        except:
            return False
    
    async def get_all_keys(self) -> List[str]:
        """Get all configuration keys."""
        config = await self.load_configuration()
        keys = []
        
        def _extract_keys(obj, prefix=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    keys.append(current_key)
                    if isinstance(value, dict):
                        _extract_keys(value, current_key)
        
        _extract_keys(config)
        return keys
    
    @property
    def provider_name(self) -> str:
        """Get provider name for identification."""
        return "default"
    
    @property
    def priority(self) -> int:
        """Get provider priority (lower = less important)."""
        return 0  # Lowest priority