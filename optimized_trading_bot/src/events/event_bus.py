"""
Event bus implementation for the trading bot.

This module provides a high-performance, async event bus for
decoupled communication between system components.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Set, Optional, Callable, Any
import uuid
from datetime import datetime, timezone

from .interfaces import IEventBus, IEventHandler
from core.domain import Event


class EventBus(IEventBus):
    """
    High-performance async event bus implementation.
    
    Features:
    - Priority-based handler execution
    - Error isolation (one handler failure doesn't affect others)
    - Event batching for performance
    - Dead letter queue for failed events
    - Metrics collection
    """
    
    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        self.logger = logging.getLogger(__name__)
        
        # Handler registry: event_type -> list of (handler, priority) tuples
        self._handlers: Dict[str, List[tuple[IEventHandler, int]]] = defaultdict(list)
        
        # Event processing
        self._event_queue = asyncio.Queue(maxsize=max_queue_size)
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Dead letter queue for failed events
        self._dead_letter_queue: List[tuple[Event, Exception]] = []
        
        # Metrics
        self._metrics = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handlers_executed': 0,
            'handlers_failed': 0
        }
        
        # Middleware functions
        self._middleware: List[Callable[[Event], Event]] = []
    
    async def start(self) -> None:
        """Start the event bus processing."""
        if self._running:
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        self.logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus processing."""
        if not self._running:
            return
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Event bus stopped")
    
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        try:
            if not self._running:
                await self.start()
            
            # Apply middleware
            processed_event = await self._apply_middleware(event)
            
            # Add to queue for async processing
            try:
                self._event_queue.put_nowait(processed_event)
                self._metrics['events_published'] += 1
            except asyncio.QueueFull:
                self.logger.error("Event queue full, dropping event")
                self._metrics['events_failed'] += 1
        
        except Exception as e:
            self.logger.error(f"Failed to publish event {event.id}: {e}")
            self._metrics['events_failed'] += 1
    
    async def publish_batch(self, events: List[Event]) -> None:
        """Publish multiple events in batch."""
        for event in events:
            await self.publish(event)
    
    async def subscribe(
        self,
        event_type: str,
        handler: IEventHandler,
        priority: int = 0
    ) -> None:
        """Subscribe handler to event type with priority."""
        if not handler.can_handle(event_type):
            raise ValueError(f"Handler {handler.handler_name} cannot handle {event_type}")
        
        # Add handler with priority
        self._handlers[event_type].append((handler, priority))
        
        # Sort handlers by priority (higher priority first)
        self._handlers[event_type].sort(key=lambda x: x[1], reverse=True)
        
        self.logger.debug(f"Subscribed {handler.handler_name} to {event_type} with priority {priority}")
    
    async def unsubscribe(
        self,
        event_type: str,
        handler: IEventHandler
    ) -> None:
        """Unsubscribe handler from event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                (h, p) for h, p in self._handlers[event_type] if h != handler
            ]
            
            if not self._handlers[event_type]:
                del self._handlers[event_type]
        
        self.logger.debug(f"Unsubscribed {handler.handler_name} from {event_type}")
    
    async def get_subscribers(self, event_type: str) -> List[IEventHandler]:
        """Get all subscribers for event type."""
        return [handler for handler, _ in self._handlers.get(event_type, [])]
    
    async def clear_subscribers(self, event_type: Optional[str] = None) -> None:
        """Clear subscribers for event type or all if None."""
        if event_type:
            if event_type in self._handlers:
                del self._handlers[event_type]
        else:
            self._handlers.clear()
    
    async def add_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Add middleware function to process events."""
        self._middleware.append(middleware)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            **self._metrics,
            'queue_size': self._event_queue.qsize(),
            'dead_letter_queue_size': len(self._dead_letter_queue),
            'handler_count': sum(len(handlers) for handlers in self._handlers.values()),
            'event_types': list(self._handlers.keys())
        }
    
    async def get_dead_letter_events(self) -> List[tuple[Event, Exception]]:
        """Get events that failed processing."""
        return self._dead_letter_queue.copy()
    
    async def retry_dead_letter_events(self) -> None:
        """Retry processing dead letter events."""
        retry_events = self._dead_letter_queue.copy()
        self._dead_letter_queue.clear()
        
        for event, _ in retry_events:
            await self.publish(event)
    
    async def _process_events(self) -> None:
        """Main event processing loop."""
        while self._running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._handle_event(event)
                self._metrics['events_processed'] += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in event processing loop: {e}")
    
    async def _handle_event(self, event: Event) -> None:
        """Handle a single event by dispatching to all subscribers."""
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            self.logger.debug(f"No handlers for event type: {event.event_type}")
            return
        
        # Create tasks for all handlers
        tasks = []
        for handler, priority in handlers:
            task = asyncio.create_task(
                self._execute_handler(handler, event),
                name=f"handler_{handler.handler_name}_{event.id}"
            )
            tasks.append(task)
        
        # Wait for all handlers to complete (with error isolation)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_handler(self, handler: IEventHandler, event: Event) -> None:
        """Execute a single event handler with error handling."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            await handler.handle(event)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            self._metrics['handlers_executed'] += 1
            
            if execution_time > 1.0:  # Log slow handlers
                self.logger.warning(
                    f"Slow handler {handler.handler_name} took {execution_time:.2f}s "
                    f"for event {event.event_type}"
                )
        
        except Exception as e:
            self.logger.error(
                f"Handler {handler.handler_name} failed for event {event.event_type}: {e}"
            )
            self._metrics['handlers_failed'] += 1
            
            # Add to dead letter queue if it's a critical event
            if event.data.get('critical', False):
                self._dead_letter_queue.append((event, e))
    
    async def _apply_middleware(self, event: Event) -> Event:
        """Apply middleware functions to event."""
        processed_event = event
        
        for middleware in self._middleware:
            try:
                processed_event = middleware(processed_event)
            except Exception as e:
                self.logger.error(f"Middleware failed: {e}")
        
        return processed_event


# Enhanced Event classes for the trading bot
class TradingEvent(Event):
    """Trading-specific event with additional metadata."""
    
    def __init__(
        self,
        event_type: str,
        order: Optional[Any] = None,
        position: Optional[Any] = None,
        trade: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(event_type=event_type, **kwargs)
        self.order = order
        self.position = position
        self.trade = trade


class MarketDataEvent(Event):
    """Market data event with symbol and data."""
    
    def __init__(
        self,
        event_type: str,
        symbol: str,
        quote: Optional[Any] = None,
        bar: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(event_type=event_type, **kwargs)
        self.symbol = symbol
        self.quote = quote
        self.bar = bar


class RiskEvent(Event):
    """Risk management event with severity levels."""
    
    def __init__(
        self,
        event_type: str,
        risk_type: str,
        severity: str = "medium",
        message: str = "",
        affected_symbols: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(event_type=event_type, **kwargs)
        self.risk_type = risk_type
        self.severity = severity
        self.message = message
        self.affected_symbols = affected_symbols or []


class SystemEvent(Event):
    """System-level event for monitoring and health."""
    
    def __init__(
        self,
        event_type: str,
        component: str,
        status: str,
        metrics: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(event_type=event_type, **kwargs)
        self.component = component
        self.status = status
        self.metrics = metrics or {}