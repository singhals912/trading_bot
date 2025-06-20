import asyncio
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import logging

@dataclass
class CircuitBreakerState:
    """Circuit breaker pattern for API resilience"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.states: Dict[str, CircuitBreakerState] = {}
        
    def record_success(self, service: str):
        if service in self.states:
            self.states[service].failure_count = 0
            self.states[service].state = 'CLOSED'
            
    def record_failure(self, service: str):
        if service not in self.states:
            self.states[service] = CircuitBreakerState()
            
        state = self.states[service]
        state.failure_count += 1
        state.last_failure_time = datetime.now()
        
        if state.failure_count >= self.failure_threshold:
            state.state = 'OPEN'
            
    def is_available(self, service: str) -> bool:
        if service not in self.states:
            return True
            
        state = self.states[service]
        
        if state.state == 'CLOSED':
            return True
            
        if state.state == 'OPEN':
            if datetime.now() - state.last_failure_time > timedelta(seconds=self.recovery_timeout):
                state.state = 'HALF_OPEN'
                return True
            return False
            
        return True  # HALF_OPEN - allow one request

class ErrorRecoverySystem:
    """Comprehensive error recovery and monitoring"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.circuit_breaker = CircuitBreaker()
        self.error_history = deque(maxlen=1000)
        self.recovery_strategies = {
            'APIError': self._handle_api_error,
            'DataError': self._handle_data_error,
            'OrderError': self._handle_order_error,
            'ConnectionError': self._handle_connection_error
        }
        
    async def execute_with_recovery(self, func: Callable, *args, **kwargs):
        """Execute function with automatic recovery"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if not self.circuit_breaker.is_available(func.__name__):
                    raise Exception(f"Circuit breaker OPEN for {func.__name__}")
                    
                result = await func(*args, **kwargs)
                self.circuit_breaker.record_success(func.__name__)
                return result
                
            except Exception as e:
                self.circuit_breaker.record_failure(func.__name__)
                self.error_history.append({
                    'timestamp': datetime.now(),
                    'function': func.__name__,
                    'error': str(e),
                    'attempt': attempt + 1
                })
                
                error_type = type(e).__name__
                if error_type in self.recovery_strategies:
                    recovery_result = await self.recovery_strategies[error_type](e, func, args, kwargs)
                    if recovery_result:
                        return recovery_result
                        
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    await self._handle_critical_failure(func.__name__, e)
                    raise
                    
    async def _handle_api_error(self, error, func, args, kwargs):
        """Handle API-specific errors"""
        if '429' in str(error):  # Rate limit
            await asyncio.sleep(60)  # Wait 1 minute
            return await func(*args, **kwargs)
        elif '401' in str(error):  # Auth error
            # Attempt to refresh credentials
            await self.bot.refresh_credentials()
            return await func(*args, **kwargs)
        return None
        
    async def _handle_data_error(self, error, func, args, kwargs):
        """Handle data-related errors"""
        self.bot.logger.warning(f"Data error detected: {str(error)}")
        
        # If it's a missing data error, try alternative data source
        if 'missing' in str(error).lower() or 'not found' in str(error).lower():
            try:
                # Switch to backup data source or fetch from alternative endpoint
                self.bot.logger.info("Attempting to use backup data source")
                # You can implement specific backup logic here
                return None
            except Exception as backup_error:
                self.bot.logger.error(f"Backup data source also failed: {str(backup_error)}")
                
        # If it's a data validation error, try to clean/fix the data
        elif 'invalid' in str(error).lower() or 'format' in str(error).lower():
            self.bot.logger.info("Attempting to clean/validate data")
            # Implement data cleaning logic here
            return None
            
        return None
        
    async def _handle_order_error(self, error, func, args, kwargs):
        """Handle order-related errors"""
        self.bot.logger.warning(f"Order error detected: {str(error)}")
        
        # Handle insufficient buying power
        if 'buying power' in str(error).lower() or 'insufficient' in str(error).lower():
            self.bot.logger.info("Insufficient buying power - reducing order size")
            # Try to reduce order size by 50%
            if 'qty' in kwargs:
                kwargs['qty'] = float(kwargs['qty']) * 0.5
                return await func(*args, **kwargs)
            elif len(args) >= 2:  # Assuming qty is second argument
                new_args = list(args)
                new_args[1] = float(new_args[1]) * 0.5
                return await func(*tuple(new_args), **kwargs)
                
        # Handle order rejection due to market conditions
        elif 'rejected' in str(error).lower() or 'market closed' in str(error).lower():
            self.bot.logger.info("Order rejected - market may be closed or volatile")
            # Could implement logic to queue order for market open
            return None
            
        # Handle duplicate order errors
        elif 'duplicate' in str(error).lower():
            self.bot.logger.info("Duplicate order detected - skipping")
            return None
            
        return None
        
    async def _handle_connection_error(self, error, func, args, kwargs):
        """Handle network connectivity issues"""
        self.bot.logger.warning("Connection error detected, switching to backup data source")
        # Implement backup data source logic
        return None
        
    async def _handle_critical_failure(self, function_name: str, error: Exception):
        """Handle critical failures that can't be recovered"""
        self.bot.logger.critical(f"Critical failure in {function_name}: {str(error)}")
        
        # Send alert (email/SMS)
        await self.send_alert(
            subject="Trading Bot Critical Failure",
            message=f"Function {function_name} failed after all retries: {str(error)}"
        )
        
        # Initiate safe shutdown if needed
        if function_name in ['submit_order', 'get_account_info']:
            await self.bot.emergency_shutdown()
            
    async def send_alert(self, subject: str, message: str):
        """Send alert notification (implement your preferred method)"""
        # Placeholder for alert implementation
        # Could send email, SMS, Slack notification, etc.
        self.bot.logger.critical(f"ALERT - {subject}: {message}")

class HealthMonitor:
    """System health monitoring and auto-recovery"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.health_checks = {
            'api_connection': self._check_api_connection,
            'data_feed': self._check_data_feed,
            'order_system': self._check_order_system,
            'risk_limits': self._check_risk_limits,
            'memory_usage': self._check_memory_usage
        }
        self.last_check_results = {}
        
    async def run_health_checks(self) -> Dict[str, bool]:
        """Run all health checks"""
        results = {}
        for check_name, check_func in self.health_checks.items():
            try:
                results[check_name] = await check_func()
            except Exception as e:
                self.bot.logger.error(f"Health check {check_name} failed: {str(e)}")
                results[check_name] = False
                
        self.last_check_results = results
        return results
        
    async def _check_api_connection(self) -> bool:
        """Verify API connectivity"""
        try:
            clock = self.bot.trade_client.get_clock()
            return clock is not None
        except:
            return False
            
    async def _check_data_feed(self) -> bool:
        """Check if data feed is working"""
        try:
            # Check if recent data is available
            # This is a placeholder - implement based on your data source
            return True
        except:
            return False
            
    async def _check_order_system(self) -> bool:
        """Check if order system is functional"""
        try:
            # Test order system without placing actual orders
            # This is a placeholder - implement based on your broker API
            return True
        except:
            return False
            
    async def _check_risk_limits(self) -> bool:
        """Check if risk limits are being respected"""
        try:
            # Implement risk limit checking logic
            return True
        except:
            return False
            
    async def _check_memory_usage(self) -> bool:
        """Monitor memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_percent = process.memory_percent()
            
            if memory_percent > 80:
                self.bot.logger.warning(f"High memory usage: {memory_percent}%")
                # Trigger garbage collection
                import gc
                gc.collect()
                
            return memory_percent < 90
        except ImportError:
            # psutil not available, skip this check
            return True
        except:
            return False

class AutoRecoveryManager:
    """Automatic recovery from various failure scenarios"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.recovery_actions = {
            'stale_positions': self._recover_stale_positions,
            'orphaned_orders': self._recover_orphaned_orders,
            'data_gaps': self._recover_data_gaps,
            'sync_issues': self._recover_sync_issues
        }
        
    async def perform_recovery_scan(self):
        """Scan for issues and auto-recover"""
        for issue_type, recovery_func in self.recovery_actions.items():
            try:
                await recovery_func()
            except Exception as e:
                self.bot.logger.error(f"Recovery failed for {issue_type}: {str(e)}")
                
    async def _recover_stale_positions(self):
        """Detect and handle stale positions"""
        current_time = datetime.now()
        
        for symbol, position in list(self.bot.positions.items()):
            # Check if position data is stale (>1 hour old)
            if current_time - position.timestamp > timedelta(hours=1):
                try:
                    # Refresh position data
                    actual_position = self.bot.trade_client.get_position(symbol)
                    if actual_position:
                        position.quantity = float(actual_position.qty)
                        position.timestamp = current_time
                    else:
                        # Position doesn't exist in broker
                        del self.bot.positions[symbol]
                        self.bot.logger.warning(f"Removed stale position for {symbol}")
                except:
                    pass
                    
    async def _recover_orphaned_orders(self):
        """Detect and cancel orphaned orders"""
        try:
            open_orders = self.bot.trade_client.get_orders(status='open')
            
            for order in open_orders:
                # Check if order is orphaned (>30 minutes old and not in tracking)
                order_age = datetime.now() - order.created_at.replace(tzinfo=None)
                if order_age > timedelta(minutes=30):
                    if order.symbol not in self.bot.positions:
                        self.bot.trade_client.cancel_order_by_id(order.id)
                        self.bot.logger.info(f"Cancelled orphaned order for {order.symbol}")
        except:
            pass
            
    async def _recover_data_gaps(self):
        """Detect and fill data gaps"""
        try:
            # Implement logic to detect missing data and backfill
            # This is a placeholder - implement based on your data needs
            pass
        except Exception as e:
            self.bot.logger.error(f"Data gap recovery failed: {str(e)}")
            
    async def _recover_sync_issues(self):
        """Detect and fix synchronization issues"""
        try:
            # Implement logic to detect and fix sync issues between 
            # your bot's state and the broker's actual state
            pass
        except Exception as e:
            self.bot.logger.error(f"Sync recovery failed: {str(e)}")