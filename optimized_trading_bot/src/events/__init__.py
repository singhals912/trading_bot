"""
Event system for the trading bot.

This package provides a pub/sub event system for loose coupling between
components and real-time event processing.
"""

from .interfaces import IEventBus, IEventHandler
from .event_bus import EventBus

__all__ = [
    'IEventBus',
    'IEventHandler', 
    'EventBus'
]