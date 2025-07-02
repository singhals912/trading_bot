"""
Configuration management interfaces.

This module defines the contracts for configuration providers,
validators, and management operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from .models import BotConfiguration

T = TypeVar('T')


class IConfigurationProvider(ABC):
    """Interface for configuration data providers."""
    
    @abstractmethod
    async def load_configuration(self) -> Dict[str, Any]:
        """Load configuration data from source."""
        pass
    
    @abstractmethod
    async def save_configuration(self, config: Dict[str, Any]) -> bool:
        """Save configuration data to source."""
        pass
    
    @abstractmethod
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get specific configuration value."""
        pass
    
    @abstractmethod
    async def set_value(self, key: str, value: Any) -> bool:
        """Set specific configuration value."""
        pass
    
    @abstractmethod
    async def has_key(self, key: str) -> bool:
        """Check if configuration key exists."""
        pass
    
    @abstractmethod
    async def get_all_keys(self) -> List[str]:
        """Get all configuration keys."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name for identification."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Get provider priority (higher = more important)."""
        pass


class IConfigurationValidator(ABC):
    """Interface for configuration validation."""
    
    @abstractmethod
    async def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate configuration data.
        
        Returns:
            Dict with validation errors keyed by configuration section.
            Empty dict if validation passes.
        """
        pass
    
    @abstractmethod
    async def validate_section(self, section: str, data: Dict[str, Any]) -> List[str]:
        """Validate specific configuration section."""
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Get configuration schema for validation."""
        pass
    
    @abstractmethod
    async def get_required_fields(self) -> List[str]:
        """Get list of required configuration fields."""
        pass


class IConfigurationWatcher(ABC):
    """Interface for watching configuration changes."""
    
    @abstractmethod
    async def start_watching(self) -> None:
        """Start watching for configuration changes."""
        pass
    
    @abstractmethod
    async def stop_watching(self) -> None:
        """Stop watching for configuration changes."""
        pass
    
    @abstractmethod
    async def add_change_callback(self, callback: callable) -> str:
        """Add callback for configuration changes."""
        pass
    
    @abstractmethod
    async def remove_change_callback(self, callback_id: str) -> bool:
        """Remove configuration change callback."""
        pass


class IConfigurationManager(ABC):
    """Interface for configuration management operations."""
    
    @abstractmethod
    async def load_configuration(self) -> BotConfiguration:
        """Load and build complete configuration."""
        pass
    
    @abstractmethod
    async def reload_configuration(self) -> BotConfiguration:
        """Reload configuration from all sources."""
        pass
    
    @abstractmethod
    async def add_provider(self, provider: IConfigurationProvider) -> None:
        """Add configuration provider."""
        pass
    
    @abstractmethod
    async def remove_provider(self, provider_name: str) -> bool:
        """Remove configuration provider."""
        pass
    
    @abstractmethod
    async def get_configuration(self) -> BotConfiguration:
        """Get current configuration."""
        pass
    
    @abstractmethod
    async def update_configuration(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values."""
        pass
    
    @abstractmethod
    async def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate current configuration."""
        pass
    
    @abstractmethod
    async def export_configuration(self, format: str = "yaml") -> str:
        """Export configuration to string format."""
        pass
    
    @abstractmethod
    async def import_configuration(self, config_data: str, format: str = "yaml") -> bool:
        """Import configuration from string format."""
        pass


class IConfigurationEncryption(ABC):
    """Interface for configuration encryption/decryption."""
    
    @abstractmethod
    async def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive configuration value."""
        pass
    
    @abstractmethod
    async def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration value."""
        pass
    
    @abstractmethod
    async def is_encrypted(self, value: str) -> bool:
        """Check if value is encrypted."""
        pass
    
    @abstractmethod
    async def encrypt_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in configuration section."""
        pass
    
    @abstractmethod
    async def decrypt_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in configuration section."""
        pass
    
    @abstractmethod
    def get_sensitive_fields(self) -> List[str]:
        """Get list of fields that should be encrypted."""
        pass


class IConfigurationCache(ABC):
    """Interface for configuration caching."""
    
    @abstractmethod
    async def cache_configuration(self, config: BotConfiguration, ttl: int = 300) -> None:
        """Cache configuration with TTL."""
        pass
    
    @abstractmethod
    async def get_cached_configuration(self) -> Optional[BotConfiguration]:
        """Get cached configuration if available."""
        pass
    
    @abstractmethod
    async def invalidate_cache(self) -> None:
        """Invalidate cached configuration."""
        pass
    
    @abstractmethod
    async def is_cache_valid(self) -> bool:
        """Check if cached configuration is still valid."""
        pass