"""
Event system interfaces.

This module defines the contracts for the event-driven architecture
including event bus, handlers, and event processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type
import asyncio

from core.domain import Event


class IEventHandler(ABC):
    """Interface for event handlers."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event."""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Check if handler can process event type."""
        pass
    
    @property
    @abstractmethod
    def handler_name(self) -> str:
        """Get handler name for logging/debugging."""
        pass


class IEventBus(ABC):
    """Interface for event bus operations."""
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: IEventHandler,
        priority: int = 0
    ) -> None:
        """Subscribe handler to event type."""
        pass
    
    @abstractmethod
    async def unsubscribe(
        self,
        event_type: str,
        handler: IEventHandler
    ) -> None:
        """Unsubscribe handler from event type."""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[Event]) -> None:
        """Publish multiple events in batch."""
        pass
    
    @abstractmethod
    async def get_subscribers(self, event_type: str) -> List[IEventHandler]:
        """Get all subscribers for event type."""
        pass
    
    @abstractmethod
    async def clear_subscribers(self, event_type: Optional[str] = None) -> None:
        """Clear subscribers for event type or all if None."""
        pass


class IEventStore(ABC):
    """Interface for event persistence."""
    
    @abstractmethod
    async def store_event(self, event: Event) -> None:
        """Store event for persistence/replay."""
        pass
    
    @abstractmethod
    async def get_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """Retrieve stored events with filters."""
        pass
    
    @abstractmethod
    async def replay_events(
        self,
        event_types: List[str],
        start_time: str,
        end_time: str
    ) -> None:
        """Replay events within time range."""
        pass


class IEventProcessor(ABC):
    """Interface for event processing pipelines."""
    
    @abstractmethod
    async def process_event(self, event: Event) -> Optional[Event]:
        """Process and potentially transform event."""
        pass
    
    @abstractmethod
    async def add_middleware(
        self,
        middleware: Callable[[Event], Event],
        priority: int = 0
    ) -> None:
        """Add middleware to processing pipeline."""
        pass
    
    @abstractmethod
    async def remove_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Remove middleware from processing pipeline."""
        pass


class IEventScheduler(ABC):
    """Interface for scheduled event processing."""
    
    @abstractmethod
    async def schedule_event(
        self,
        event: Event,
        delay_seconds: float
    ) -> str:
        """Schedule event for future delivery."""
        pass
    
    @abstractmethod
    async def schedule_recurring_event(
        self,
        event: Event,
        interval_seconds: float,
        max_occurrences: Optional[int] = None
    ) -> str:
        """Schedule recurring event."""
        pass
    
    @abstractmethod
    async def cancel_scheduled_event(self, schedule_id: str) -> bool:
        """Cancel scheduled event."""
        pass
    
    @abstractmethod
    async def get_scheduled_events(self) -> List[Dict[str, Any]]:
        """Get all scheduled events."""
        pass