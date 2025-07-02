"""
Event handlers for converting trading events to notifications.
"""

import logging
from typing import Optional
from datetime import datetime

from events.interfaces import IEventHandler
from core.domain import TradingEvent, RiskEvent, Event
from .notification_manager import NotificationManager
from .interfaces import NotificationLevel


class TradingNotificationHandler(IEventHandler):
    """Event handler for trading-related notifications."""
    
    def __init__(
        self,
        notification_manager: NotificationManager,
        logger: Optional[logging.Logger] = None
    ):
        self.notification_manager = notification_manager
        self.logger = logger or logging.getLogger(__name__)
        self._handled_orders = set()  # Track handled orders to avoid duplicates
    
    async def handle_event(self, event: Event) -> bool:
        """Handle trading events and send notifications."""
        try:
            if isinstance(event, TradingEvent):
                return await self._handle_trading_event(event)
            return True  # Not a trading event, but not an error
            
        except Exception as e:
            self.logger.error(f"Error handling trading notification: {e}")
            return False
    
    async def _handle_trading_event(self, event: TradingEvent) -> bool:
        """Handle specific trading event types."""
        try:
            # Handle completed trades
            if event.trade:
                return await self._handle_trade_completion(event)
            
            # Handle important order status changes
            elif event.order:
                return await self._handle_order_update(event)
            
            # Handle position changes
            elif event.position:
                return await self._handle_position_update(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in trading event handling: {e}")
            return False
    
    async def _handle_trade_completion(self, event: TradingEvent) -> bool:
        """Handle completed trade notifications."""
        trade = event.trade
        
        # Always notify on trade completion
        result = await self.notification_manager.send_trading_event(event)
        
        # Send additional alert for significant P&L
        if abs(trade.net_pnl) > 100:  # Significant trade (>$100 P&L)
            level = NotificationLevel.INFO if trade.net_pnl > 0 else NotificationLevel.WARNING
            title = f"Significant {'Profit' if trade.net_pnl > 0 else 'Loss'}: {trade.symbol.ticker}"
            
            await self.notification_manager.send_system_alert(
                level=level,
                title=title,
                message=f"Trade P&L: ${trade.net_pnl:.2f} ({trade.return_pct:.2f}%)",
                data={
                    "symbol": trade.symbol.ticker,
                    "pnl": float(trade.net_pnl),
                    "return_pct": trade.return_pct,
                    "strategy": trade.strategy_name
                },
                tags=["trade", "significant", "pnl"]
            )
        
        return bool(result)
    
    async def _handle_order_update(self, event: TradingEvent) -> bool:
        """Handle order status updates."""
        order = event.order
        order_key = f"{order.id}:{order.status.value}"
        
        # Avoid duplicate notifications for same order status
        if order_key in self._handled_orders:
            return True
        
        # Only notify on important status changes
        important_statuses = ["filled", "rejected", "cancelled"]
        if order.status.value not in important_statuses:
            return True
        
        # Send notification
        result = await self.notification_manager.send_trading_event(event)
        
        # Mark as handled
        self._handled_orders.add(order_key)
        
        # Clean up old handled orders (keep last 1000)
        if len(self._handled_orders) > 1000:
            # Convert to list, sort, and keep newest 500
            handled_list = list(self._handled_orders)
            self._handled_orders = set(handled_list[-500:])
        
        return bool(result)
    
    async def _handle_position_update(self, event: TradingEvent) -> bool:
        """Handle position updates (new positions, closures)."""
        position = event.position
        
        # For now, we'll be conservative and not send notifications for every position update
        # This could be enhanced to detect position openings/closings
        return True
    
    @property
    def priority(self) -> int:
        """Handler priority (higher = processed first)."""
        return 100


class RiskNotificationHandler(IEventHandler):
    """Event handler for risk-related notifications."""
    
    def __init__(
        self,
        notification_manager: NotificationManager,
        logger: Optional[logging.Logger] = None
    ):
        self.notification_manager = notification_manager
        self.logger = logger or logging.getLogger(__name__)
    
    async def handle_event(self, event: Event) -> bool:
        """Handle risk events and send notifications."""
        try:
            if isinstance(event, RiskEvent):
                return await self._handle_risk_event(event)
            return True  # Not a risk event
            
        except Exception as e:
            self.logger.error(f"Error handling risk notification: {e}")
            return False
    
    async def _handle_risk_event(self, event: RiskEvent) -> bool:
        """Handle specific risk events."""
        try:
            # Send risk notification
            result = await self.notification_manager.send_risk_event(event)
            
            # For critical events, also send a system alert
            if event.severity == "critical":
                await self.notification_manager.send_system_alert(
                    level=NotificationLevel.CRITICAL,
                    title="🚨 CRITICAL RISK ALERT",
                    message=f"Critical risk event detected: {event.message}",
                    data={
                        "risk_type": event.risk_type,
                        "affected_symbols": [s.ticker for s in event.affected_symbols],
                        "timestamp": event.timestamp.isoformat()
                    },
                    tags=["critical", "risk", "alert"]
                )
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Error in risk event handling: {e}")
            return False
    
    @property
    def priority(self) -> int:
        """Handler priority (higher = processed first)."""
        return 200  # Higher priority than trading events


class SystemNotificationHandler(IEventHandler):
    """Event handler for system-level notifications."""
    
    def __init__(
        self,
        notification_manager: NotificationManager,
        logger: Optional[logging.Logger] = None
    ):
        self.notification_manager = notification_manager
        self.logger = logger or logging.getLogger(__name__)
    
    async def handle_event(self, event: Event) -> bool:
        """Handle system events and send notifications."""
        try:
            # Handle generic events that might be system-related
            if event.event_type == "system":
                return await self._handle_system_event(event)
            
            # Handle startup/shutdown events
            elif "startup" in event.event_type or "shutdown" in event.event_type:
                return await self._handle_lifecycle_event(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling system notification: {e}")
            return False
    
    async def _handle_system_event(self, event: Event) -> bool:
        """Handle generic system events."""
        try:
            # Determine level based on event data
            level = NotificationLevel.INFO
            if "error" in event.data.get("message", "").lower():
                level = NotificationLevel.ERROR
            elif "warning" in event.data.get("message", "").lower():
                level = NotificationLevel.WARNING
            
            title = event.data.get("title", "System Event")
            message = event.data.get("message", "System event occurred")
            
            result = await self.notification_manager.send_system_alert(
                level=level,
                title=title,
                message=message,
                data=event.data,
                tags=["system", "event"]
            )
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Error in system event handling: {e}")
            return False
    
    async def _handle_lifecycle_event(self, event: Event) -> bool:
        """Handle bot startup/shutdown events."""
        try:
            if "startup" in event.event_type:
                level = NotificationLevel.INFO
                title = "🚀 Trading Bot Started"
                message = "Enhanced Trading Bot has started successfully"
                tags = ["system", "startup"]
            else:
                level = NotificationLevel.INFO  
                title = "🛑 Trading Bot Stopped"
                message = "Enhanced Trading Bot has been stopped"
                tags = ["system", "shutdown"]
            
            result = await self.notification_manager.send_system_alert(
                level=level,
                title=title,
                message=message,
                data=event.data,
                tags=tags
            )
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Error in lifecycle event handling: {e}")
            return False
    
    @property
    def priority(self) -> int:
        """Handler priority."""
        return 50  # Lower priority than risk/trading events