"""
Notification service interfaces and data models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class NotificationLevel(Enum):
    """Notification severity levels."""
    CRITICAL = "critical"
    ERROR = "error" 
    WARNING = "warning"
    INFO = "info"


@dataclass
class NotificationMessage:
    """Notification message data structure."""
    level: NotificationLevel
    title: str
    message: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data or {},
            'tags': self.tags or []
        }


class INotificationService(ABC):
    """Interface for notification services."""
    
    @abstractmethod
    async def send_notification(self, notification: NotificationMessage) -> bool:
        """
        Send a notification.
        
        Args:
            notification: The notification message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the notification service connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Get the service name for identification."""
        pass
    
    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the service is enabled."""
        pass