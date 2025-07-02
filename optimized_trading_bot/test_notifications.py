#!/usr/bin/env python3
"""
Test script for email notifications.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.models import NotificationConfig
from infrastructure.notifications import EmailNotificationService, NotificationManager
from infrastructure.notifications.interfaces import NotificationMessage, NotificationLevel
from datetime import datetime


async def test_email_notifications():
    """Test email notification functionality."""
    print("🧪 Testing Email Notification System...")
    
    # Create notification config from environment variables
    config = NotificationConfig(
        email_enabled=True,
        email_smtp_host=os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com'),
        email_smtp_port=int(os.getenv('EMAIL_SMTP_PORT', '587')),
        email_username=os.getenv('EMAIL_USERNAME', 'singhals912@gmail.com'),
        email_password=os.getenv('EMAIL_PASSWORD', 'xvny qotn gbmf macu'),
        email_recipients=[os.getenv('NOTIFICATION_EMAIL', 'singhals912@gmail.com')],
        
        # Throttling disabled for testing
        throttle_enabled=False,
        throttle_interval_minutes=1,
        throttle_max_per_hour=10
    )
    
    print(f"📧 Email Config:")
    print(f"  Host: {config.email_smtp_host}")
    print(f"  Username: {config.email_username}")
    print(f"  Recipients: {config.email_recipients}")
    
    # Test 1: Email Service Direct Test
    print("\n🔍 Test 1: Email Service Connection Test")
    email_service = EmailNotificationService(config)
    
    if not email_service.is_enabled:
        print("❌ Email service not properly configured")
        return False
    
    connection_test = await email_service.test_connection()
    if connection_test:
        print("✅ Email service connection test passed!")
    else:
        print("❌ Email service connection test failed")
        return False
    
    # Test 2: Notification Manager Test
    print("\n🔍 Test 2: Notification Manager Test")
    notification_manager = NotificationManager(config)
    
    # Send a test trading notification
    test_notification = NotificationMessage(
        level=NotificationLevel.INFO,
        title="📈 Test Trade Notification",
        message="""
This is a test trade notification from your Enhanced Trading Bot!

Trade Details:
- Symbol: AAPL
- Side: BUY
- Quantity: 10 shares
- Price: $150.00
- P&L: +$25.50 (+1.7%)
- Strategy: Enhanced Combined

If you're receiving this email, your notification system is working perfectly! 🎉
        """.strip(),
        timestamp=datetime.now(),
        data={
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 10,
            "price": 150.00,
            "pnl": 25.50,
            "strategy": "enhanced_combined",
            "test": True
        },
        tags=["test", "trade", "notification"]
    )
    
    result = await notification_manager.send_notification(test_notification)
    if result.get('email', False):
        print("✅ Test trading notification sent successfully!")
    else:
        print("❌ Failed to send test trading notification")
        return False
    
    # Test 3: Risk Alert Test  
    print("\n🔍 Test 3: Risk Alert Test")
    risk_notification = NotificationMessage(
        level=NotificationLevel.WARNING,
        title="⚠️ Test Risk Alert",
        message="""
This is a test risk alert from your Enhanced Trading Bot.

Risk Alert Details:
- Risk Type: Portfolio Risk Threshold
- Severity: WARNING
- Current Risk: 8.5%
- Max Risk: 10.0%
- Affected Symbols: TSLA, NVDA

The bot is monitoring risk levels and will alert you when thresholds are approached.
        """.strip(),
        timestamp=datetime.now(),
        data={
            "risk_type": "portfolio_risk",
            "severity": "warning",
            "current_risk": 8.5,
            "max_risk": 10.0,
            "affected_symbols": ["TSLA", "NVDA"],
            "test": True
        },
        tags=["test", "risk", "warning"]
    )
    
    result = await notification_manager.send_notification(risk_notification)
    if result.get('email', False):
        print("✅ Test risk alert sent successfully!")
    else:
        print("❌ Failed to send test risk alert")
        return False
    
    # Test 4: System Alert Test
    print("\n🔍 Test 4: System Alert Test")
    result = await notification_manager.send_system_alert(
        level=NotificationLevel.INFO,
        title="🚀 System Notification Test",
        message="""
This is a test system notification from your Enhanced Trading Bot.

System Status:
- Bot Version: Enhanced v2.0
- Status: Running
- Uptime: 5 minutes
- Market Regime: High Volatility
- Active Positions: 0
- Available Cash: $98,248.74

All systems are operational and monitoring the markets! 📊
        """.strip(),
        data={
            "bot_version": "enhanced_v2.0",
            "status": "running",
            "uptime_minutes": 5,
            "market_regime": "high_volatility",
            "positions": 0,
            "cash": 98248.74,
            "test": True
        },
        tags=["test", "system", "status"]
    )
    
    if result.get('email', False):
        print("✅ Test system alert sent successfully!")
    else:
        print("❌ Failed to send test system alert")
        return False
    
    print("\n🎉 All email notification tests passed!")
    print("📬 Check your email inbox for the test notifications.")
    print(f"📧 Emails sent to: {', '.join(config.email_recipients)}")
    
    return True


async def main():
    """Main test function."""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        success = await test_email_notifications()
        
        if success:
            print("\n✅ Email notification system is working correctly!")
            print("🔔 You should receive 4 test emails shortly.")
            sys.exit(0)
        else:
            print("\n❌ Email notification system test failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())