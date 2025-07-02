"""
Notification infrastructure for the trading bot.

This module provides email, SMS, and webhook notification services
for trading events, risk alerts, and system notifications.
"""

from .interfaces import INotificationService, NotificationMessage, NotificationLevel
from .email_service import EmailNotificationService
from .notification_manager import NotificationManager

__all__ = [
    'INotificationService',
    'NotificationMessage', 
    'NotificationLevel',
    'EmailNotificationService',
    'NotificationManager'
]