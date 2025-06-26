#!/usr/bin/env python3
"""
Quick Fix Script - Add missing config and fix ngrok
"""

import os
import subprocess
import sys
from pathlib import Path

def fix_ngrok():
    """Kill existing ngrok processes and restart"""
    print("🔧 Fixing ngrok tunnel...")
    
    try:
        # Kill any existing ngrok processes
        subprocess.run(['pkill', '-f', 'ngrok'], check=False)
        print("✅ Cleared existing ngrok processes")
        
        # Wait a moment
        import time
        time.sleep(2)
        
        return True
    except Exception as e:
        print(f"⚠️ ngrok cleanup: {e}")
        return False

def add_missing_config_to_env():
    """Add missing configuration to .env file"""
    print("📝 Adding missing configuration to .env...")
    
    env_file = Path('.env')
    
    # Required configuration that's missing
    missing_config = """

# =============================================================================
# REQUIRED TRADING BOT CONFIGURATION (Auto-added by fix script)
# =============================================================================

# Strategy Configuration
STRATEGY=combined
TOTAL_CAPITAL=50000
TRADING_CAPITAL=10000

# Risk Management
STOP_LOSS_PCT=0.02
TAKE_PROFIT_PCT=0.04
MAX_LOSS_STREAK=3

# Symbol Selection
SYMBOLS=AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,NFLX,SPY,QQQ
MIN_VOLUME=1000000
MIN_PRICE=10.0
MAX_PRICE=500.0

# Technical Analysis
RSI_PERIOD=14
SMA_SHORT=20
SMA_LONG=50
BOLLINGER_PERIOD=20
BOLLINGER_STD=2.0

# Extended Configuration
USE_ML_SIGNALS=False
USE_ADAPTIVE_STOPS=True
EXTENDED_HOURS_ENABLED=True
PRE_MARKET_RISK_REDUCTION=0.3
AUTO_RECOVERY_ENABLED=True
SMART_ALERTS_ENABLED=True
CLOSE_ON_SHUTDOWN=False
MAX_CONSECUTIVE_ERRORS=10
HEALTH_CHECK_INTERVAL=300
STATE_SAVE_INTERVAL=60
SYMBOL_CACHE_DURATION=300
MAX_DAILY_API_CALLS=1000
FALLBACK_MODE_ENABLED=True

"""
    
    if env_file.exists():
        # Read existing content
        with open(env_file, 'r') as f:
            existing_content = f.read()
        
        # Check if STRATEGY is already there
        if 'STRATEGY=' not in existing_content:
            # Append missing config
            with open(env_file, 'a') as f:
                f.write(missing_config)
            print("✅ Added missing configuration to .env")
            return True
        else:
            print("✅ Configuration already exists in .env")
            return True
    else:
        print("❌ .env file not found")
        return False

def create_simple_startup_script():
    """Create a simple, working startup script"""
    
    script_content = '''#!/usr/bin/env python3
"""
Simple Trading Bot Startup - No Complex Dependencies
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
except ImportError:
    print("⚠️ python-dotenv not available")

def start_simple_ngrok(port=8080):
    """Start ngrok with better error handling"""
    print(f"🌐 Starting ngrok tunnel on port {port}...")
    
    try:
        # Kill any existing ngrok processes
        subprocess.run(['pkill', '-f', 'ngrok'], check=False)
        time.sleep(2)
        
        # Start new ngrok process
        process = subprocess.Popen(
            ['ngrok', 'http', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(5)
        
        # Get tunnel URL
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                data = response.json()
                if data.get('tunnels'):
                    tunnel_url = data['tunnels'][0]['public_url']
                    print(f"✅ ngrok tunnel active: {tunnel_url}")
                    
                    # Save URL
                    with open('remote_url.txt', 'w') as f:
                        f.write(f"Remote Access URL: {tunnel_url}\\n")
                        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                    
                    return tunnel_url, process
            
            print("⚠️ Could not get tunnel URL, but ngrok started")
            return None, process
            
        except Exception as e:
            print(f"⚠️ Tunnel URL check failed: {e}")
            return None, process
            
    except Exception as e:
        print(f"❌ ngrok failed: {e}")
        return None, None

def main():
    """Simple main function"""
    print("🚀 SIMPLE TRADING BOT WITH REMOTE ACCESS")
    print("=" * 50)
    
    # Check API keys
    if not os.getenv('APCA_API_KEY_ID'):
        print("❌ Missing APCA_API_KEY_ID in .env")
        sys.exit(1)
    
    if not os.getenv('APCA_API_SECRET_KEY'):
        print("❌ Missing APCA_API_SECRET_KEY in .env")
        sys.exit(1)
    
    print("✅ API keys found")
    
    # Start ngrok
    tunnel_url, ngrok_process = start_simple_ngrok()
    
    # Create basic config
    config = {
        'API_KEY': os.getenv('APCA_API_KEY_ID'),
        'SECRET_KEY': os.getenv('APCA_API_SECRET_KEY'),
        'PAPER_TRADING': True,  # Safe default
        'STRATEGY': os.getenv('STRATEGY', 'combined'),
        'TRADING_CAPITAL': int(os.getenv('TRADING_CAPITAL', '10000')),
        'RISK_PCT': float(os.getenv('RISK_PCT', '0.015')),
        'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', '3')),
        'MAX_DAILY_LOSS': float(os.getenv('MAX_DAILY_LOSS', '0.02')),
        'STOP_LOSS_PCT': float(os.getenv('STOP_LOSS_PCT', '0.02')),
        'TAKE_PROFIT_PCT': float(os.getenv('TAKE_PROFIT_PCT', '0.04')),
        'SYMBOLS': os.getenv('SYMBOLS', 'AAPL,MSFT,GOOGL').split(','),
        'USE_ML_SIGNALS': False,
        'EXTENDED_HOURS_ENABLED': True,
        'AUTO_RECOVERY_ENABLED': True,
        'FALLBACK_MODE_ENABLED': True
    }
    
    try:
        print("🤖 Creating trading bot...")
        
        # Import bot
        from algo_trading_bot_v5 import AlgoTradingBot
        bot = AlgoTradingBot(config)
        print("✅ Bot created successfully")
        
        # Apply fixes if available
        try:
            from enhanced_algo_bot_fixes import apply_enhanced_fixes
            apply_enhanced_fixes(bot)
            print("✅ Enhanced fixes applied")
        except:
            print("⚠️ Enhanced fixes not available")
        
        # Start mobile monitoring
        try:
            from mobile_monitoring import setup_mobile_monitoring
            monitor = setup_mobile_monitoring(bot, 8080)
            if monitor:
                print("✅ Mobile monitoring started")
                if tunnel_url:
                    print(f"📱 Remote access: {tunnel_url}")
                else:
                    print("🏠 Local access: http://localhost:8080")
        except Exception as e:
            print(f"⚠️ Mobile monitoring failed: {e}")
        
        print("\\n" + "=" * 50)
        print("🏁 TRADING BOT STARTED")
        if tunnel_url:
            print(f"📱 Remote URL: {tunnel_url}")
            print("   (URL saved to remote_url.txt)")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50)
        
        # Start bot
        try:
            if hasattr(bot, 'run_autonomous'):
                import asyncio
                asyncio.run(bot.run_autonomous())
            else:
                bot.run()
        except KeyboardInterrupt:
            print("\\n🛑 Stopping...")
        finally:
            if ngrok_process:
                ngrok_process.terminate()
                print("✅ ngrok stopped")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        
        if 'ngrok_process' in locals() and ngrok_process:
            ngrok_process.terminate()

if __name__ == "__main__":
    main()
'''
    
    # Save script
    script_file = Path('simple_bot_start.py')
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # Make executable
    try:
        os.chmod(script_file, 0o755)
    except:
        pass
    
    print(f"📝 Created {script_file}")
    return script_file

def main():
    """Quick fix main function"""
    print("🔧 QUICK FIX FOR TRADING BOT")
    print("=" * 40)
    
    # Step 1: Fix ngrok
    fix_ngrok()
    
    # Step 2: Add missing config
    if add_missing_config_to_env():
        print("✅ Configuration fixed")
    else:
        print("❌ Could not fix configuration")
        return
    
    # Step 3: Create simple startup script
    script_file = create_simple_startup_script()
    
    print("\n🎉 FIXES APPLIED!")
    print("=" * 40)
    print(f"🚀 Run: python {script_file}")
    print("📱 This will start your bot with remote access")
    print("✅ All required configuration has been added")

if __name__ == "__main__":
    main()