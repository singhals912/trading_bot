"""
Configuration Manager for the trading bot.

This module provides centralized configuration management with validation,
environment-specific settings, and type safety.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml

from .interfaces import IConfigurationProvider, IConfigurationValidator
from .models import BotConfiguration, TradingConfig, RiskConfig, DataConfig, MonitoringConfig, NotificationConfig


class ConfigurationManager:
    """
    Centralized configuration manager for the trading bot.
    
    Handles loading, validation, and management of configuration from
    multiple sources (files, environment variables, etc.).
    """
    
    def __init__(
        self,
        config_providers: List[IConfigurationProvider],
        validators: List[IConfigurationValidator] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.config_providers = config_providers
        self.validators = validators or []
        self.logger = logger or logging.getLogger(__name__)
        
        self._config: Optional[BotConfiguration] = None
        self._config_loaded = False
    
    async def load_configuration(self) -> BotConfiguration:
        """Load and validate configuration from all providers."""
        try:
            self.logger.info("Loading configuration from providers...")
            
            # Merge configuration from all providers
            merged_config = {}
            
            for provider in self.config_providers:
                try:
                    provider_config = await provider.load_configuration()
                    merged_config = self._merge_configs(merged_config, provider_config)
                    self.logger.debug(f"Loaded config from {provider.__class__.__name__}")
                except Exception as e:
                    self.logger.error(f"Failed to load config from {provider.__class__.__name__}: {e}")
                    continue
            
            # Create typed configuration
            self._config = self._create_typed_config(merged_config)
            
            # Validate configuration
            await self._validate_configuration()
            
            self._config_loaded = True
            self.logger.info("✅ Configuration loaded and validated successfully")
            
            return self._config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_typed_config(self, config_dict: Dict[str, Any]) -> BotConfiguration:
        """Create typed configuration from dictionary."""
        try:
            # Create trading config
            trading_config = TradingConfig(
                max_positions=config_dict.get('trading', {}).get('max_positions', 3),
                max_position_size_pct=config_dict.get('trading', {}).get('position_size_percent', 0.02),
                enable_extended_hours=config_dict.get('trading', {}).get('after_hours', False),
                regular_market_start=config_dict.get('trading', {}).get('hours_start', '09:30'),
                regular_market_end=config_dict.get('trading', {}).get('hours_end', '16:00')
            )
            
            # Create risk config
            risk_config = RiskConfig(
                max_daily_loss_pct=config_dict.get('risk', {}).get('max_position_risk', 0.02),
                default_stop_loss_pct=config_dict.get('risk', {}).get('stop_loss_percent', 0.02),
                default_take_profit_pct=config_dict.get('risk', {}).get('take_profit_percent', 0.04),
                max_drawdown_halt=config_dict.get('risk', {}).get('max_drawdown_percent', 0.15),
                enable_circuit_breakers=config_dict.get('risk', {}).get('circuit_breaker', True)
            )
            
            # Create data config
            data_config = DataConfig(
                primary_provider=config_dict.get('data', {}).get('provider', 'alpaca'),
                enable_caching=config_dict.get('data', {}).get('cache_enabled', True),
                cache_ttl_quotes=config_dict.get('data', {}).get('cache_duration', 5)
            )
            
            # Create monitoring config  
            monitoring_config = MonitoringConfig(
                enable_monitoring=config_dict.get('monitoring', {}).get('enable_metrics', True),
                prometheus_port=config_dict.get('monitoring', {}).get('metrics_port', 8000),
                dashboard_enabled=config_dict.get('monitoring', {}).get('dashboard_enabled', True),
                dashboard_port=config_dict.get('monitoring', {}).get('dashboard_port', 8080)
            )
            
            # Create notification config
            notification_config = NotificationConfig(
                enable_notifications=config_dict.get('notifications', {}).get('enabled', False),
                email_enabled=config_dict.get('notifications', {}).get('email_enabled', False)
            )
            
            # Create API credentials
            from .models import ApiCredentials
            api_credentials = ApiCredentials(
                key_id=config_dict.get('api', {}).get('key_id', 'placeholder'),
                secret_key=config_dict.get('api', {}).get('secret_key', 'placeholder'),
                base_url=config_dict.get('api', {}).get('base_url', 'https://paper-api.alpaca.markets'),
                paper_trading=config_dict.get('api', {}).get('paper_trading', True)
            )
            
            # Create main bot configuration
            bot_config = BotConfiguration(
                trading=trading_config,
                risk=risk_config,
                data=data_config,
                monitoring=monitoring_config,
                notifications=notification_config,
                api_credentials=api_credentials,
                custom_settings=config_dict.get('custom', {})
            )
            
            return bot_config
            
        except Exception as e:
            self.logger.error(f"Failed to create typed configuration: {e}")
            raise
    
    async def _validate_configuration(self) -> None:
        """Validate configuration using all validators."""
        if not self._config:
            raise ValueError("No configuration loaded")
        
        for validator in self.validators:
            try:
                await validator.validate(self._config)
                self.logger.debug(f"Configuration validated by {validator.__class__.__name__}")
            except Exception as e:
                self.logger.error(f"Configuration validation failed: {e}")
                raise
    
    def get_config(self) -> BotConfiguration:
        """Get the current configuration."""
        if not self._config_loaded or not self._config:
            raise RuntimeError("Configuration not loaded. Call load_configuration() first.")
        
        return self._config
    
    async def reload_configuration(self) -> BotConfiguration:
        """Reload configuration from all providers."""
        self._config = None
        self._config_loaded = False
        return await self.load_configuration()
    
    def is_loaded(self) -> bool:
        """Check if configuration is loaded."""
        return self._config_loaded


class DefaultConfigurationValidator(IConfigurationValidator):
    """Default configuration validator."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    async def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate configuration and return errors by section."""
        errors = {}
        
        # Convert BotConfiguration to dict if needed
        if hasattr(config, '__dict__'):
            config_dict = config.__dict__
        else:
            config_dict = config
        
        # Validate sections
        api_errors = await self.validate_section('api', config_dict.get('api', {}))
        if api_errors:
            errors['api'] = api_errors
            
        trading_errors = await self.validate_section('trading', config_dict.get('trading', {}))
        if trading_errors:
            errors['trading'] = trading_errors
            
        return errors
    
    async def validate_section(self, section: str, data: Dict[str, Any]) -> List[str]:
        """Validate specific configuration section."""
        errors = []
        
        if section == 'api':
            if not data.get('key_id'):
                errors.append("API key_id is required")
            if not data.get('secret_key'):
                errors.append("API secret_key is required")
        elif section == 'trading':
            max_positions = data.get('max_positions', 0)
            if max_positions <= 0:
                errors.append("max_positions must be greater than 0")
                
        return errors
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get configuration schema for validation."""
        return {
            "type": "object",
            "properties": {
                "api": {"type": "object"},
                "trading": {"type": "object"},
                "risk": {"type": "object"}
            }
        }
    
    async def get_required_fields(self) -> List[str]:
        """Get list of required configuration fields."""
        return ["api.key_id", "api.secret_key"]
    
    async def validate(self, config: BotConfiguration) -> None:
        """Validate configuration."""
        errors = []
        
        # Validate API credentials
        if not config.api_credentials.key_id or config.api_credentials.key_id == 'placeholder':
            errors.append("API key_id is required")
        
        if not config.api_credentials.secret_key or config.api_credentials.secret_key == 'placeholder':
            errors.append("API secret_key is required")
        
        # Validate trading configuration
        if config.trading.max_positions <= 0:
            errors.append("max_positions must be greater than 0")
        
        if config.trading.max_position_size_pct <= 0 or config.trading.max_position_size_pct > 1:
            errors.append("max_position_size_pct must be between 0 and 1")
        
        # Validate risk configuration
        if config.risk.max_daily_loss_pct <= 0 or config.risk.max_daily_loss_pct > 1:
            errors.append("max_daily_loss_pct must be between 0 and 1")
        
        if config.risk.default_stop_loss_pct <= 0 or config.risk.default_stop_loss_pct > 1:
            errors.append("default_stop_loss_pct must be between 0 and 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")