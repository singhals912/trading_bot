"""
Configuration management for the trading bot.

This package provides centralized configuration management with validation,
environment-specific settings, and type safety.
"""

from .interfaces import IConfigurationProvider, IConfigurationValidator
from .models import (
    TradingConfig, RiskConfig, DataConfig, MonitoringConfig, 
    NotificationConfig, BotConfiguration
)
from .manager import ConfigurationManager
from .providers import EnvironmentConfigProvider, FileConfigProvider

__all__ = [
    'IConfigurationProvider',
    'IConfigurationValidator',
    'TradingConfig',
    'RiskConfig', 
    'DataConfig',
    'MonitoringConfig',
    'NotificationConfig',
    'BotConfiguration',
    'ConfigurationManager',
    'EnvironmentConfigProvider',
    'FileConfigProvider'
]