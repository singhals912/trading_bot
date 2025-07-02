"""
Notification manager that coordinates different notification services.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict, deque

from config.models import NotificationConfig
from core.domain import TradingEvent, RiskEvent, Event
from .interfaces import INotificationService, NotificationMessage, NotificationLevel
from .email_service import EmailNotificationService


class NotificationManager:
    """
    Manages multiple notification services and handles alert throttling.
    """
    
    def __init__(
        self,
        config: NotificationConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize services
        self.services: Dict[str, INotificationService] = {}
        self._initialize_services()
        
        # Throttling management
        self._alert_history: Dict[str, deque] = defaultdict(deque)
        self._throttled_alerts: Set[str] = set()
        
        self.logger.info(f"🔔 Notification manager initialized with {len(self.services)} services")
    
    def _initialize_services(self) -> None:
        """Initialize all enabled notification services."""
        
        # Email service
        if self.config.email_enabled:
            try:
                email_service = EmailNotificationService(self.config, self.logger)
                if email_service.is_enabled:
                    self.services['email'] = email_service
                    self.logger.info("📧 Email notification service enabled")
                else:
                    self.logger.warning("📧 Email service configured but missing credentials")
            except Exception as e:
                self.logger.error(f"Failed to initialize email service: {e}")
        
        # Future: SMS, webhook, and other services would be added here
        # self._initialize_sms_service()
        # self._initialize_webhook_service()
        
        if not self.services:
            self.logger.warning("⚠️ No notification services are enabled")
    
    async def send_notification(
        self,
        notification: NotificationMessage,
        services: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send notification through specified services.
        
        Args:
            notification: The notification to send
            services: List of service names to use (None = all enabled)
            
        Returns:
            Dictionary mapping service names to success status
        """
        if not self.services:
            self.logger.warning("No notification services available")
            return {}
        
        # Check throttling
        if not self._should_send_notification(notification):
            self.logger.info(f"⏳ Notification throttled: {notification.title}")
            return {}
        
        # Determine which services to use
        target_services = services or list(self.services.keys())
        target_services = [s for s in target_services if s in self.services]
        
        # Send notifications concurrently
        tasks = []
        for service_name in target_services:
            service = self.services[service_name]
            task = self._send_with_service(service, notification)
            tasks.append((service_name, task))
        
        # Wait for all to complete
        results = {}
        if tasks:
            completed_tasks = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            for (service_name, _), result in zip(tasks, completed_tasks):
                if isinstance(result, Exception):
                    self.logger.error(f"Service {service_name} failed: {result}")
                    results[service_name] = False
                else:
                    results[service_name] = result
        
        # Update throttling history
        self._update_alert_history(notification)
        
        return results
    
    async def _send_with_service(
        self,
        service: INotificationService,
        notification: NotificationMessage
    ) -> bool:
        """Send notification with a specific service."""
        try:
            return await service.send_notification(notification)
        except Exception as e:
            self.logger.error(f"Service {service.service_name} error: {e}")
            return False
    
    def _should_send_notification(self, notification: NotificationMessage) -> bool:
        """Check if notification should be sent based on throttling rules."""
        if not self.config.throttle_enabled:
            return True
        
        alert_key = f"{notification.level.value}:{notification.title}"
        now = datetime.now()
        
        # Check minimum interval
        if alert_key in self._alert_history:
            last_sent = self._alert_history[alert_key][-1] if self._alert_history[alert_key] else None
            if last_sent and now - last_sent < timedelta(minutes=self.config.throttle_interval_minutes):
                return False
        
        # Check max alerts per hour
        hour_ago = now - timedelta(hours=1)
        recent_alerts = [
            timestamp for timestamp in self._alert_history[alert_key]
            if timestamp > hour_ago
        ]
        
        if len(recent_alerts) >= self.config.throttle_max_per_hour:
            if alert_key not in self._throttled_alerts:
                self._throttled_alerts.add(alert_key)
                self.logger.warning(f"⏳ Alert throttled (max per hour): {alert_key}")
            return False
        
        # Remove from throttled set if we can send again
        self._throttled_alerts.discard(alert_key)
        return True
    
    def _update_alert_history(self, notification: NotificationMessage) -> None:
        """Update alert history for throttling."""
        if not self.config.throttle_enabled:
            return
        
        alert_key = f"{notification.level.value}:{notification.title}"
        now = datetime.now()
        
        # Add current timestamp
        self._alert_history[alert_key].append(now)
        
        # Clean old entries (keep last 24 hours)
        cutoff = now - timedelta(hours=24)
        while (self._alert_history[alert_key] and 
               self._alert_history[alert_key][0] < cutoff):
            self._alert_history[alert_key].popleft()
    
    async def send_trading_event(self, event: TradingEvent) -> Dict[str, bool]:
        """Send notification for trading events."""
        if not event.order and not event.position and not event.trade:
            return {}
        
        # Determine notification level and content
        if event.trade:
            level = NotificationLevel.INFO
            title = f"Trade Executed: {event.trade.symbol.ticker}"
            message = self._format_trade_message(event.trade)
            data = {
                "symbol": event.trade.symbol.ticker,
                "side": event.trade.side.value,
                "quantity": event.trade.quantity,
                "entry_price": float(event.trade.entry_price),
                "exit_price": float(event.trade.exit_price),
                "pnl": float(event.trade.net_pnl),
                "strategy": event.trade.strategy_name
            }
            tags = ["trade", "execution", event.trade.side.value]
            
        elif event.order and event.order.status.value in ["filled", "rejected"]:
            level = NotificationLevel.INFO if event.order.status.value == "filled" else NotificationLevel.WARNING
            title = f"Order {event.order.status.value.title()}: {event.order.symbol.ticker}"
            message = self._format_order_message(event.order)
            data = {
                "symbol": event.order.symbol.ticker,
                "side": event.order.side.value,
                "quantity": event.order.quantity,
                "order_type": event.order.order_type.value,
                "status": event.order.status.value
            }
            tags = ["order", event.order.status.value, event.order.side.value]
            
        else:
            return {}  # Skip other trading events
        
        notification = NotificationMessage(
            level=level,
            title=title,
            message=message,
            timestamp=event.timestamp,
            data=data,
            tags=tags
        )
        
        return await self.send_notification(notification)
    
    async def send_risk_event(self, event: RiskEvent) -> Dict[str, bool]:
        """Send notification for risk events."""
        # Determine notification level based on severity
        level_map = {
            "low": NotificationLevel.INFO,
            "medium": NotificationLevel.WARNING,
            "high": NotificationLevel.ERROR,
            "critical": NotificationLevel.CRITICAL
        }
        level = level_map.get(event.severity, NotificationLevel.WARNING)
        
        notification = NotificationMessage(
            level=level,
            title=f"Risk Alert: {event.risk_type.replace('_', ' ').title()}",
            message=event.message,
            timestamp=event.timestamp,
            data={
                "risk_type": event.risk_type,
                "severity": event.severity,
                "affected_symbols": [s.ticker for s in event.affected_symbols]
            },
            tags=["risk", event.severity, event.risk_type]
        )
        
        return await self.send_notification(notification)
    
    async def send_system_alert(
        self,
        level: NotificationLevel,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Send system alert notification."""
        notification = NotificationMessage(
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            data=data,
            tags=tags or ["system"]
        )
        
        return await self.send_notification(notification)
    
    def _format_trade_message(self, trade) -> str:
        """Format trade execution message."""
        pnl_sign = "+" if trade.net_pnl >= 0 else ""
        return f"""
Trade completed for {trade.symbol.ticker}:

Side: {trade.side.value.upper()}
Quantity: {trade.quantity}
Entry Price: ${trade.entry_price:.2f}
Exit Price: ${trade.exit_price:.2f}
P&L: {pnl_sign}${trade.net_pnl:.2f}
Return: {trade.return_pct:.2f}%
Duration: {trade.duration:.1f} hours
Strategy: {trade.strategy_name}

Trade executed at {trade.exit_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """.strip()
    
    def _format_order_message(self, order) -> str:
        """Format order status message."""
        return f"""
Order {order.status.value} for {order.symbol.ticker}:

Side: {order.side.value.upper()}
Type: {order.order_type.value.upper()}
Quantity: {order.quantity}
{f'Price: ${order.price:.2f}' if order.price else 'Price: Market'}
{f'Filled: {order.filled_quantity} @ ${order.filled_price:.2f}' if order.filled_price else ''}

Order ID: {order.id}
Status: {order.status.value.upper()}
Updated: {order.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """.strip()
    
    async def test_all_services(self) -> Dict[str, bool]:
        """Test all notification services."""
        results = {}
        
        for service_name, service in self.services.items():
            try:
                self.logger.info(f"🧪 Testing {service_name} service...")
                result = await service.test_connection()
                results[service_name] = result
                
                if result:
                    self.logger.info(f"✅ {service_name} service test passed")
                else:
                    self.logger.error(f"❌ {service_name} service test failed")
                    
            except Exception as e:
                self.logger.error(f"❌ {service_name} service test error: {e}")
                results[service_name] = False
        
        return results
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all notification services."""
        status = {}
        
        for service_name, service in self.services.items():
            status[service_name] = {
                "enabled": service.is_enabled,
                "service_name": service.service_name,
                "type": type(service).__name__
            }
        
        return status