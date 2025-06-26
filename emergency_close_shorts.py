#!/usr/bin/env python3
"""
EMERGENCY SCRIPT: Close all short positions immediately (FIXED VERSION)
Run this before restarting your bot with the fixes
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
except ImportError:
    print("❌ Missing alpaca-py. Install with: pip install alpaca-py")
    sys.exit(1)

def close_all_short_positions():
    """Close all short positions immediately - FIXED VERSION"""
    
    # Initialize Alpaca client
    try:
        client = TradingClient(
            api_key=os.getenv('APCA_API_KEY_ID'),
            secret_key=os.getenv('APCA_API_SECRET_KEY'),
            paper=True  # Assuming paper trading
        )
        print("✅ Connected to Alpaca")
    except Exception as e:
        print(f"❌ Failed to connect to Alpaca: {e}")
        return False
    
    try:
        # Get all positions
        positions = client.get_all_positions()
        
        if not positions:
            print("✅ No positions found")
            return True
            
        # Find short positions - FIXED attribute access
        short_positions = []
        for pos in positions:
            try:
                qty = float(pos.qty)
                if qty < 0:  # Short position
                    short_positions.append(pos)
            except (ValueError, AttributeError) as e:
                print(f"⚠️  Skipping position due to attribute error: {e}")
                continue
        
        if not short_positions:
            print("✅ No short positions to close")
            return True
            
        print(f"🚨 Found {len(short_positions)} short positions to close:")
        
        # Display position info with better error handling
        for pos in short_positions:
            try:
                symbol = pos.symbol
                qty = abs(float(pos.qty))
                
                # Try to get market value and calculate price
                try:
                    market_value = float(pos.market_value)
                    current_price = abs(market_value / float(pos.qty))
                except (AttributeError, ZeroDivisionError, TypeError):
                    current_price = "N/A"
                
                # Try to get unrealized P&L
                try:
                    if hasattr(pos, 'unrealized_pnl'):
                        unrealized_pnl = float(pos.unrealized_pnl)
                    elif hasattr(pos, 'unrealized_pl'):
                        unrealized_pnl = float(pos.unrealized_pl)
                    else:
                        unrealized_pnl = "N/A"
                except (AttributeError, TypeError, ValueError):
                    unrealized_pnl = "N/A"
                
                print(f"   📉 {symbol}: {qty} shares @ ${current_price} (P&L: ${unrealized_pnl})")
                
            except Exception as e:
                print(f"   📉 {pos.symbol}: Error displaying details - {e}")
        
        # Confirm before closing
        response = input(f"\n❓ Close all {len(short_positions)} short positions? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return False
            
        # Close each short position
        closed_count = 0
        for pos in short_positions:
            try:
                symbol = pos.symbol
                qty = abs(float(pos.qty))
                
                print(f"🔄 Closing {symbol}: Buying {qty} shares to cover short...")
                
                # Create buy order to close short
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY,  # Buy to cover short
                    time_in_force=TimeInForce.DAY
                )
                
                submitted_order = client.submit_order(order)
                print(f"✅ Submitted BUY order for {symbol}: {qty} shares (Order ID: {submitted_order.id})")
                closed_count += 1
                
            except Exception as e:
                print(f"❌ Failed to close {symbol}: {e}")
                
        print(f"\n🎯 Successfully submitted {closed_count}/{len(short_positions)} close orders")
        
        if closed_count > 0:
            print("⏳ Orders are being processed. Check your account to confirm fills.")
            print("💡 Tip: Check your Alpaca dashboard to see order status")
            
        return closed_count == len(short_positions)
        
    except Exception as e:
        print(f"❌ Error getting positions: {e}")
        print("💡 Try checking your Alpaca dashboard manually")
        return False

def main():
    print("🚨 EMERGENCY SHORT POSITION CLOSURE (FIXED VERSION)")
    print("=" * 50)
    print("This script will close ALL short positions in your account")
    print("Run this BEFORE restarting your bot with the fixes")
    print()
    
    # Check API keys
    if not os.getenv('APCA_API_KEY_ID') or not os.getenv('APCA_API_SECRET_KEY'):
        print("❌ Missing Alpaca API keys in environment")
        print("Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in your .env file")
        return
    
    # Execute closure
    success = close_all_short_positions()
    
    if success:
        print("\n✅ SHORT CLOSURE COMPLETE")
        print()
        print("🔧 NEXT STEPS:")
        print("1. Apply the code fixes to algo_trading_bot_v5.py")
        print("2. Create .env file with emergency settings:")
        print("   STRATEGY=trend")
        print("   RISK_PCT=0.01") 
        print("   MAX_POSITIONS=1")
        print("   USE_ML_SIGNALS=False")
        print("3. Restart bot: python enhanced_startup_script.py")
        print("4. Monitor for 24 hours before considering live trading")
    else:
        print("\n❌ SHORT CLOSURE INCOMPLETE")
        print()
        print("🔧 MANUAL ALTERNATIVES:")
        print("1. Log into your Alpaca dashboard")
        print("2. Go to Positions tab")
        print("3. Manually close all short positions (negative quantities)")
        print("4. Or try this script again after a few minutes")

if __name__ == "__main__":
    main()