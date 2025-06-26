#!/usr/bin/env python3
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
                        f.write(f"Remote Access URL: {tunnel_url}\n")
                        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
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
        
        print("\n" + "=" * 50)
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
            print("\n🛑 Stopping...")
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
