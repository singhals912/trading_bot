#!/usr/bin/env python3
"""
Trading Bot with Remote Mobile Monitoring - FIXED VERSION
Automatically sets up ngrok tunnel for remote access with complete configuration
"""

import os
import sys
import threading
import time
import json
import subprocess
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables.")

class RemoteMonitoringManager:
    """Manages remote access tunnel and monitoring"""
    
    def __init__(self, port=8080):
        self.port = port
        self.ngrok_process = None
        self.public_url = None
        self.tunnel_active = False
        
    def start_tunnel(self):
        """Start ngrok tunnel for remote access"""
        print("🌐 Starting remote access tunnel...")
        
        try:
            # Start ngrok
            self.ngrok_process = subprocess.Popen(
                ['ngrok', 'http', str(self.port), '--log=stdout'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for tunnel to be ready
            time.sleep(5)
            
            # Get public URL
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('tunnels'):
                    tunnel = data['tunnels'][0]
                    self.public_url = tunnel['public_url']
                    self.tunnel_active = True
                    
                    print(f"✅ Remote access tunnel active!")
                    print(f"🌐 Public URL: {self.public_url}")
                    print(f"📱 Access from anywhere: {self.public_url}")
                    
                    # Save URL to file for easy access
                    with open('remote_access_url.txt', 'w') as f:
                        f.write(f"Trading Bot Remote Access URL\n")
                        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"URL: {self.public_url}\n")
                        f.write(f"\nAccess this URL from any device with internet connection\n")
                    
                    return True
                    
        except Exception as e:
            print(f"⚠️ Failed to start tunnel: {e}")
            print("📝 Fallback: Bot will run with local access only")
            
        return False
    
    def stop_tunnel(self):
        """Stop the tunnel"""
        if self.ngrok_process:
            self.ngrok_process.terminate()
            self.tunnel_active = False
            print("🛑 Remote access tunnel stopped")
    
    def get_access_info(self):
        """Get current access information"""
        info = {
            'local_url': f'http://localhost:{self.port}',
            'remote_url': self.public_url if self.tunnel_active else None,
            'tunnel_active': self.tunnel_active
        }
        return info

def create_complete_config():
    """Create complete configuration with all required parameters"""
    print("⚙️ Creating complete bot configuration...")
    
    config = {
        # API Configuration
        'API_KEY': os.getenv('APCA_API_KEY_ID'),
        'SECRET_KEY': os.getenv('APCA_API_SECRET_KEY'),
        'PAPER_TRADING': os.getenv('PAPER_TRADING', 'True').lower() == 'true',
        
        # Required Strategy Parameter
        'STRATEGY': os.getenv('STRATEGY', 'combined'),  # Default to combined strategy
        
        # Capital Management
        'TOTAL_CAPITAL': int(os.getenv('TOTAL_CAPITAL', '50000')),
        'TRADING_CAPITAL': int(os.getenv('TRADING_CAPITAL', '10000')),
        'RISK_PCT': float(os.getenv('RISK_PCT', '0.015')),  # 1.5%
        'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', '3')),
        'MAX_DAILY_LOSS': float(os.getenv('MAX_DAILY_LOSS', '0.02')),  # 2%
        
        # Trading Parameters
        'USE_ML_SIGNALS': os.getenv('USE_ML_SIGNALS', 'False').lower() == 'true',
        'USE_ADAPTIVE_STOPS': True,
        'EXTENDED_HOURS_ENABLED': True,
        'PRE_MARKET_RISK_REDUCTION': 0.3,
        
        # Risk Management
        'STOP_LOSS_PCT': float(os.getenv('STOP_LOSS_PCT', '0.02')),  # 2%
        'TAKE_PROFIT_PCT': float(os.getenv('TAKE_PROFIT_PCT', '0.04')),  # 4%
        'MAX_LOSS_STREAK': int(os.getenv('MAX_LOSS_STREAK', '3')),
        
        # System Configuration
        'AUTO_RECOVERY_ENABLED': True,
        'SMART_ALERTS_ENABLED': True,
        'CLOSE_ON_SHUTDOWN': False,
        'MAX_CONSECUTIVE_ERRORS': 10,
        'HEALTH_CHECK_INTERVAL': 300,
        'STATE_SAVE_INTERVAL': 60,
        'SYMBOL_CACHE_DURATION': 300,
        'MAX_DAILY_API_CALLS': 1000,
        'FALLBACK_MODE_ENABLED': True,
        
        # Data Sources
        'USE_FUNDAMENTAL_DATA': bool(os.getenv('ALPHA_VANTAGE_KEY')),
        'USE_ECONOMIC_DATA': bool(os.getenv('FRED_API_KEY')),
        'USE_NEWS_SENTIMENT': bool(os.getenv('NEWS_API_KEY')),
        
        # Monitoring
        'monitoring': {
            'alerts_enabled': True,
            'alert_check_interval': 300,
            'daily_digest_enabled': True,
            'dashboard_enabled': True
        },
        
        # Notifications
        'email_enabled': bool(os.getenv('EMAIL_SENDER')),
        'sms_enabled': bool(os.getenv('TWILIO_SID')),
        'telegram_enabled': False,
        'discord_enabled': False,
        
        # Symbol Selection
        'SYMBOLS': os.getenv('SYMBOLS', 'AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,NFLX,SPY,QQQ').split(','),
        'MIN_VOLUME': int(os.getenv('MIN_VOLUME', '1000000')),
        'MIN_PRICE': float(os.getenv('MIN_PRICE', '10.0')),
        'MAX_PRICE': float(os.getenv('MAX_PRICE', '500.0')),
        
        # Technical Analysis
        'RSI_PERIOD': int(os.getenv('RSI_PERIOD', '14')),
        'SMA_SHORT': int(os.getenv('SMA_SHORT', '20')),
        'SMA_LONG': int(os.getenv('SMA_LONG', '50')),
        'BOLLINGER_PERIOD': int(os.getenv('BOLLINGER_PERIOD', '20')),
        'BOLLINGER_STD': float(os.getenv('BOLLINGER_STD', '2.0')),
    }
    
    print("✅ Complete configuration created")
    return config

def main():
    """Main function with remote monitoring"""
    print("🚀 TRADING BOT WITH REMOTE MOBILE MONITORING")
    print("=" * 60)
    
    # Validate API keys
    if not os.getenv('APCA_API_KEY_ID') or not os.getenv('APCA_API_SECRET_KEY'):
        print("❌ Missing Alpaca API keys in .env file")
        print("📝 Please add APCA_API_KEY_ID and APCA_API_SECRET_KEY to your .env file")
        sys.exit(1)
    
    # Get monitoring port
    port = int(os.getenv('MOBILE_MONITORING_PORT', '8080'))
    remote_access = os.getenv('REMOTE_ACCESS_ENABLED', 'True').lower() == 'true'
    
    # Setup remote access manager
    if remote_access:
        remote_manager = RemoteMonitoringManager(port)
        tunnel_started = remote_manager.start_tunnel()
        
        if tunnel_started:
            print("🎉 Remote access successfully configured!")
        else:
            print("⚠️ Remote access failed, using local access only")
    else:
        print("📍 Remote access disabled, using local access only")
        remote_manager = None
    
    # Create complete bot configuration
    config = create_complete_config()
    
    try:
        # Import and create trading bot
        print("🤖 Creating trading bot...")
        
        # Try to import the enhanced bot first, then fallback to base bot
        try:
            from enhanced_autonomous_bot import IndustryGradeAutonomousBot
            bot = IndustryGradeAutonomousBot(config)
            print("✅ Using IndustryGradeAutonomousBot")
        except ImportError:
            try:
                from algo_trading_bot_v5 import AlgoTradingBot
                bot = AlgoTradingBot(config)
                print("✅ Using AlgoTradingBot")
            except ImportError:
                print("❌ Could not import trading bot")
                print("📝 Make sure either enhanced_autonomous_bot.py or algo_trading_bot_v5.py exists")
                sys.exit(1)
        
        # Apply enhancements if using base bot
        if bot.__class__.__name__ == 'AlgoTradingBot':
            try:
                from enhanced_algo_bot_fixes import apply_enhanced_fixes
                apply_enhanced_fixes(bot)
                print("✅ Enhanced fixes applied")
            except ImportError:
                print("⚠️ Enhanced fixes not available (continuing without)")
            
            # Apply robust data provider
            try:
                from api_fallback_system import integrate_robust_data_provider
                integrate_robust_data_provider(bot)
                print("✅ Robust data provider integrated")
            except ImportError:
                print("⚠️ Robust data provider not available (continuing without)")
        
        # Setup mobile monitoring
        print("📱 Setting up mobile monitoring...")
        try:
            from mobile_monitoring import setup_mobile_monitoring
            monitor = setup_mobile_monitoring(bot, port)
            
            if monitor:
                print("✅ Mobile monitoring active!")
                
                # Show access information
                if remote_manager:
                    access_info = remote_manager.get_access_info()
                    print("\n🌐 ACCESS INFORMATION:")
                    print(f"   Local: {access_info['local_url']}")
                    if access_info['remote_url']:
                        print(f"   Remote: {access_info['remote_url']}")
                        print("   📱 Use the remote URL to access from anywhere!")
                        
                        # Also save to a JSON file for easy programmatic access
                        access_data = {
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'local_url': access_info['local_url'],
                            'remote_url': access_info['remote_url'],
                            'tunnel_active': True
                        }
                        with open('current_access_urls.json', 'w') as f:
                            json.dump(access_data, f, indent=2)
                else:
                    print(f"\n🏠 Local access: http://localhost:{port}")
            
        except Exception as e:
            print(f"⚠️ Mobile monitoring failed: {e}")
            print("   Bot will continue running without mobile monitoring")
        
        # Show final instructions
        print("\n" + "=" * 60)
        print("🏁 TRADING BOT STARTED WITH REMOTE MONITORING")
        
        if remote_manager and remote_manager.tunnel_active:
            print(f"📱 Remote URL: {remote_manager.public_url}")
            print("   Save this URL to access from your phone anywhere!")
            print("   URL also saved to: remote_access_url.txt")
            print("   Access info saved to: current_access_urls.json")
        
        print(f"\n📊 Dashboard Features:")
        print(f"   • Real-time bot status and performance")
        print(f"   • Daily P&L tracking")
        print(f"   • Active positions monitoring")
        print(f"   • System health metrics")
        print(f"   • Auto-refresh every 30 seconds")
        
        print("\n🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start the trading bot
        try:
            # Check if bot has enhanced run method
            if hasattr(bot, 'run_autonomous'):
                print("🏃 Starting autonomous trading mode...")
                import asyncio
                asyncio.run(bot.run_autonomous())
            elif hasattr(bot, 'run'):
                print("🏃 Starting standard trading mode...")
                bot.run()
            else:
                print("❌ Bot doesn't have a run method")
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
        except Exception as e:
            print(f"\n💥 Trading error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if remote_manager:
                remote_manager.stop_tunnel()
            print("✅ Cleanup completed")
                
    except Exception as e:
        print(f"💥 Startup failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Still try to cleanup tunnel
        if 'remote_manager' in locals() and remote_manager:
            remote_manager.stop_tunnel()
        
        sys.exit(1)

if __name__ == "__main__":
    main()