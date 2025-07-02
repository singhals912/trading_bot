"""
Email notification service implementation using SMTP.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config.models import NotificationConfig
from .interfaces import INotificationService, NotificationMessage, NotificationLevel


class EmailNotificationService(INotificationService):
    """Email notification service using SMTP."""
    
    def __init__(
        self,
        config: NotificationConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # Email formatting templates
        self._level_colors = {
            NotificationLevel.CRITICAL: "#DC3545",  # Red
            NotificationLevel.ERROR: "#FD7E14",     # Orange  
            NotificationLevel.WARNING: "#FFC107",   # Yellow
            NotificationLevel.INFO: "#28A745"       # Green
        }
        
        self._level_icons = {
            NotificationLevel.CRITICAL: "🚨",
            NotificationLevel.ERROR: "❌", 
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.INFO: "ℹ️"
        }
    
    @property
    def service_name(self) -> str:
        """Get service name."""
        return "email"
    
    @property
    def is_enabled(self) -> bool:
        """Check if email service is enabled."""
        return (
            self.config.email_enabled and
            bool(self.config.email_smtp_host) and
            bool(self.config.email_username) and
            bool(self.config.email_password) and
            bool(self.config.email_recipients)
        )
    
    async def send_notification(self, notification: NotificationMessage) -> bool:
        """Send email notification."""
        if not self.is_enabled:
            self.logger.warning("Email service not properly configured")
            return False
        
        try:
            # Run SMTP operations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._send_email_sync,
                notification
            )
            
            if result:
                self.logger.info(f"✅ Email notification sent: {notification.title}")
            else:
                self.logger.error(f"❌ Failed to send email: {notification.title}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Email notification error: {e}")
            return False
    
    def _send_email_sync(self, notification: NotificationMessage) -> bool:
        """Synchronous email sending (runs in thread pool)."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{notification.level.value.upper()}] {notification.title}"
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.email_recipients)
            
            # Create HTML and text content
            html_content = self._create_html_email(notification)
            text_content = self._create_text_email(notification)
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(
                self.config.email_smtp_host, 
                self.config.email_smtp_port
            ) as server:
                server.starttls()
                server.login(
                    self.config.email_username,
                    self.config.email_password
                )
                
                text = msg.as_string()
                server.sendmail(
                    self.config.email_username,
                    self.config.email_recipients,
                    text
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP error: {e}")
            return False
    
    def _create_html_email(self, notification: NotificationMessage) -> str:
        """Create HTML email content."""
        level_color = self._level_colors[notification.level]
        level_icon = self._level_icons[notification.level]
        
        # Format additional data
        data_section = ""
        if notification.data:
            data_items = []
            for key, value in notification.data.items():
                data_items.append(f"<li><strong>{key}:</strong> {value}</li>")
            data_section = f"""
            <h3>Additional Information</h3>
            <ul>
                {''.join(data_items)}
            </ul>
            """
        
        # Format tags
        tags_section = ""
        if notification.tags:
            tag_badges = [f'<span style="background: #6C757D; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{tag}</span>' for tag in notification.tags]
            tags_section = f"""
            <h3>Tags</h3>
            <p>{' '.join(tag_badges)}</p>
            """
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background: {level_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 0.9em; color: #6c757d; }}
                .timestamp {{ font-size: 0.9em; color: #6c757d; }}
                .message {{ line-height: 1.6; margin: 15px 0; }}
                h1 {{ margin: 0; font-size: 1.5em; }}
                h3 {{ color: #333; border-bottom: 2px solid #e9ecef; padding-bottom: 5px; }}
                ul {{ padding-left: 20px; }}
                li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{level_icon} {notification.title}</h1>
                    <div class="timestamp">{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                </div>
                <div class="content">
                    <div class="message">
                        {notification.message.replace(chr(10), '<br>')}
                    </div>
                    {data_section}
                    {tags_section}
                </div>
                <div class="footer">
                    <p>📈 Enhanced Trading Bot Alert System</p>
                    <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_text_email(self, notification: NotificationMessage) -> str:
        """Create plain text email content."""
        level_icon = self._level_icons[notification.level]
        
        text = f"""
{level_icon} {notification.title}
{'=' * 50}

Level: {notification.level.value.upper()}
Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{notification.message}
"""
        
        # Add data section
        if notification.data:
            text += "\n\nAdditional Information:\n"
            for key, value in notification.data.items():
                text += f"  {key}: {value}\n"
        
        # Add tags
        if notification.tags:
            text += f"\nTags: {', '.join(notification.tags)}\n"
        
        text += f"""
{'=' * 50}
📈 Enhanced Trading Bot Alert System
Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return text
    
    async def test_connection(self) -> bool:
        """Test SMTP connection."""
        if not self.is_enabled:
            return False
        
        try:
            test_notification = NotificationMessage(
                level=NotificationLevel.INFO,
                title="Email Service Test",
                message="This is a test email from your Enhanced Trading Bot. If you receive this, email notifications are working correctly!",
                timestamp=datetime.now(),
                data={
                    "service": "email",
                    "test_type": "connection_test",
                    "bot_version": "enhanced_v2.0"
                },
                tags=["test", "email", "connection"]
            )
            
            return await self.send_notification(test_notification)
            
        except Exception as e:
            self.logger.error(f"Email test connection failed: {e}")
            return False