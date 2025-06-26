#!/usr/bin/env python3
"""
Enhanced Startup Script for Industry-Grade Autonomous Trading Bot
Integrates all improvements and handles the issues from your logs
"""

import os
import sys
import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from report_integration import integrate_portfolio_reporting

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """Setup environment and validate configuration"""
    print("🔧 Setting up environment...")
    
    # Create necessary directories
    directories = ['logs', 'data', 'data/historical', 'data/fundamental', 
                  'data/economic', 'data/news', 'data/events', 'backups']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    print("✅ Environment setup complete")

def validate_api_keys():
    """Validate API keys and provide guidance"""
    print("🔑 Validating API keys...")
    
    # Required keys
    required_keys = {
        'APCA_API_KEY_ID': 'Alpaca API Key ID',
        'APCA_API_SECRET_KEY': 'Alpaca Secret Key'
    }
    
    # Optional keys
    optional_keys = {
        'ALPHA_VANTAGE_KEY': 'Alpha Vantage (fundamental data)',
        'FRED_API_KEY': 'FRED (economic data)', 
        'NEWS_API_KEY': 'NewsAPI (sentiment analysis)',
        'EMAIL_SENDER': 'Email alerts',
        'EMAIL_PASSWORD': 'Email alerts',
        'TWILIO_SID': 'SMS alerts (optional)',
        'TWILIO_TOKEN': 'SMS alerts (optional)'
    }
    
    # Check required keys
    missing_required = []
    for key, description in required_keys.items():
        if not os.getenv(key):
            missing_required.append(f"{key} ({description})")
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for key in missing_required:
            print(f"   - {key}")
        print("\nPlease set these in your environment or .env file")
        sys.exit(1)
    
    # Check optional keys
    available_optional = []
    missing_optional = []
    for key, description in optional_keys.items():
        if os.getenv(key):
            available_optional.append(f"{key} ({description})")
        else:
            missing_optional.append(f"{key} ({description})")
    
    print("✅ Required API keys found")
    
    if available_optional:
        print("✅ Available optional features:")
        for key in available_optional:
            print(f"   - {key}")
    
    if missing_optional:
        print("⚠️  Missing optional features:")
        for key in missing_optional:
            print(f"   - {key}")
        print("   Bot will use fallback methods for missing APIs")

def install_dependencies():
    """Check and install required dependencies"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'alpaca-py',
        'pandas',
        'numpy', 
        'yfinance',
        'requests',
        'python-dotenv',
        'fredapi',
        'textblob',
        'nltk'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        
        # Try to install automatically
        try:
            import subprocess
            print("🔄 Attempting to install missing packages...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ Packages installed successfully")
        except Exception as e:
            print(f"❌ Failed to install packages: {e}")
            sys.exit(1)
    else:
        print("✅ All dependencies satisfied")

def create_enhanced_config():
    """Create enhanced configuration - CONSOLIDATED VERSION"""
    print("⚙️  Creating enhanced configuration...")
    
    config = {
        # API Configuration
        'API_KEY': os.getenv('APCA_API_KEY_ID'),
        'SECRET_KEY': os.getenv('APCA_API_SECRET_KEY'),
        'BASE_URL': os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets'),
        'PAPER_TRADING': os.getenv('PAPER_TRADING', 'True').lower() == 'true',
        
        # Capital Management - UPDATED TO MATCH YOUR NEEDS
        'TOTAL_CAPITAL': int(os.getenv('TOTAL_CAPITAL', '100000')),    # Increased from 50k
        'TRADING_CAPITAL': int(os.getenv('TRADING_CAPITAL', '20000')), # Increased from 10k
        'RISK_PCT': float(os.getenv('RISK_PCT', '0.015')),            # 1.5% (between startup 1% and main 2%)
        'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', '3')),        # Updated from 1 to 3
        'MAX_DAILY_LOSS': float(os.getenv('MAX_DAILY_LOSS', '0.025')), # 2.5% (slightly higher)
        
        # Strategy Configuration - CONSOLIDATED
        'STRATEGY': os.getenv('STRATEGY', 'combined'),  # CHANGED: Use 'combined' as default
        'USE_ML_SIGNALS': os.getenv('USE_ML_SIGNALS', 'True').lower() == 'true',  # ENABLED by default
        'USE_ADAPTIVE_STOPS': True,
        'ML_CONFIDENCE_THRESHOLD': float(os.getenv('ML_CONFIDENCE_THRESHOLD', '0.7')),
        
        # Timing Configuration - FROM MAIN BOT
        'LOOP_SLEEP': int(os.getenv('LOOP_SLEEP', '120')),  # 2 minutes (was 60s in main bot)
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        
        # Enhanced Features - BEST OF BOTH
        'EXTENDED_HOURS_ENABLED': os.getenv('EXTENDED_HOURS_ENABLED', 'True').lower() == 'true',
        'PRE_MARKET_RISK_REDUCTION': float(os.getenv('PRE_MARKET_RISK_REDUCTION', '0.5')),
        'AUTO_RECOVERY_ENABLED': True,
        'SMART_ALERTS_ENABLED': True,
        'CLOSE_ON_SHUTDOWN': os.getenv('CLOSE_ON_SHUTDOWN', 'False').lower() == 'true',
        
        # Advanced Features - FROM MAIN BOT
        'PORTFOLIO_OPTIMIZATION': os.getenv('PORTFOLIO_OPTIMIZATION', 'True').lower() == 'true',
        'ADAPTIVE_RISK_MANAGEMENT': True,
        'MARKET_MICROSTRUCTURE_ANALYSIS': True,
        'USE_KELLY_CRITERION': True,
        'MAX_PORTFOLIO_HEAT': float(os.getenv('MAX_PORTFOLIO_HEAT', '0.6')),
        'MIN_LIQUIDITY_SCORE': float(os.getenv('MIN_LIQUIDITY_SCORE', '0.5')),
        
        # Execution Parameters - FROM MAIN BOT
        'SMART_ORDER_ROUTING': True,
        'MAX_SPREAD_PCT': float(os.getenv('MAX_SPREAD_PCT', '0.01')),  # 1% max spread
        'USE_ADAPTIVE_STOPS': True,
        
        # Performance Optimizations
        'MAX_CONSECUTIVE_ERRORS': int(os.getenv('MAX_CONSECUTIVE_ERRORS', '10')),
        'HEALTH_CHECK_INTERVAL': int(os.getenv('HEALTH_CHECK_INTERVAL', '300')),
        'STATE_SAVE_INTERVAL': int(os.getenv('STATE_SAVE_INTERVAL', '60')),
        'SYMBOL_CACHE_DURATION': int(os.getenv('SYMBOL_CACHE_DURATION', '300')),
        'MAX_DAILY_API_CALLS': int(os.getenv('MAX_DAILY_API_CALLS', '1000')),
        'FALLBACK_MODE_ENABLED': True,
        
        # Monitoring - ENHANCED
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
        
        # Data Sources - OPTIONAL
        'ALPHA_VANTAGE_KEY': os.getenv('ALPHA_VANTAGE_KEY', ''),
        'FRED_API_KEY': os.getenv('FRED_API_KEY', ''),
        'NEWS_API_KEY': os.getenv('NEWS_API_KEY', ''),
    }
    
    print("✅ Enhanced consolidated configuration created")
    return config

def create_startup_bot():
    """Create and configure the enhanced bot"""
    print("🤖 Initializing Enhanced Autonomous Trading Bot...")
    
    try:
        # Import with fallback handling
        try:
            from enhanced_autonomous_bot import IndustryGradeAutonomousBot
            print("✅ Using IndustryGradeAutonomousBot")
            bot_class = IndustryGradeAutonomousBot
        except ImportError:
            print("⚠️  IndustryGradeAutonomousBot not found, using base bot with enhancements")
            from algo_trading_bot_v5 import AlgoTradingBot
            bot_class = AlgoTradingBot
        
        # Create configuration
        config = create_enhanced_config()
        
        # Create bot instance
        bot = bot_class(config)
        
        # Apply enhancements if using base bot
        if bot_class.__name__ == 'AlgoTradingBot':
            print("🔧 Applying enhancements to base bot...")
            
            # Apply enhanced fixes
            try:
                from enhanced_algo_bot_fixes import apply_enhanced_fixes
                apply_enhanced_fixes(bot)
                print("✅ Enhanced fixes applied")
            except ImportError:
                print("⚠️  Enhanced fixes module not found")
            
            # Integrate robust data provider
            try:
                from api_fallback_system import integrate_robust_data_provider
                integrate_robust_data_provider(bot)
                print("✅ Robust data provider integrated")
            except ImportError:
                print("⚠️  Robust data provider not found")
        
        print("✅ Bot initialization complete")
        return bot
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        traceback.print_exc()
        sys.exit(1)

def run_pre_flight_checks(bot):
    """Run comprehensive pre-flight checks"""
    print("🔍 Running pre-flight checks...")
    
    checks_passed = 0
    total_checks = 6
    
    # Check 1: Market connectivity
    try:
        if bot.is_market_open() is not None:
            print("✅ Market connectivity check passed")
            checks_passed += 1
        else:
            print("❌ Market connectivity check failed")
    except Exception as e:
        print(f"❌ Market connectivity error: {e}")
    
    # Check 2: Account access
    try:
        account_info = bot.get_account_info()
        if account_info and 'equity' in account_info:
            print(f"✅ Account access: ${account_info['equity']:,.2f} equity")
            checks_passed += 1
        else:
            print("❌ Account access check failed")
    except Exception as e:
        print(f"❌ Account access error: {e}")
    
    # Check 3: Data provider
    try:
        test_data = bot.get_real_time_data('AAPL')
        if not test_data.empty:
            print("✅ Data provider check passed")
            checks_passed += 1
        else:
            print("❌ Data provider check failed")
    except Exception as e:
        print(f"❌ Data provider error: {e}")
    
    # Check 4: Symbol selection
    try:
        symbols = bot._select_symbols()
        if symbols and len(symbols) > 0:
            print(f"✅ Symbol selection: {len(symbols)} symbols available")
            checks_passed += 1
        else:
            print("❌ Symbol selection check failed")
    except Exception as e:
        print(f"❌ Symbol selection error: {e}")
    
    # Check 5: Risk management
    try:
        if hasattr(bot, '_pre_trade_risk_check'):
            risk_check = bot._pre_trade_risk_check('AAPL', 'buy')
            print(f"✅ Risk management: {'Enabled' if risk_check is not None else 'Disabled'}")
            checks_passed += 1
        else:
            print("❌ Risk management methods missing")
    except Exception as e:
        print(f"❌ Risk management error: {e}")
    
    # Check 6: Monitoring systems
    try:
        if hasattr(bot, 'alert_system') or hasattr(bot, '_update_dashboard'):
            print("✅ Monitoring systems available")
            checks_passed += 1
        else:
            print("❌ Monitoring systems not found")
    except Exception as e:
        print(f"❌ Monitoring systems error: {e}")
    
    # Summary
    success_rate = (checks_passed / total_checks) * 100
    print(f"\n📊 Pre-flight results: {checks_passed}/{total_checks} checks passed ({success_rate:.1f}%)")
    
    if checks_passed >= 4:  # Minimum viable
        print("✅ Pre-flight checks passed - bot ready for operation")
        return True
    else:
        print("❌ Pre-flight checks failed - please resolve issues before trading")
        return False

def start_monitoring_services(bot):
    """Start monitoring services"""
    print("📊 Starting monitoring services...")
    
    try:
        # Start metrics exporter if available
        try:
            from metrics_exporter import TradingBotMetricsExporter, start_metrics_server
            
            exporter = TradingBotMetricsExporter()
            exporter.start_collection()
            
            server = start_metrics_server(port=8000)
            if server:
                print("✅ Metrics server started on http://localhost:8000/metrics")
            
        except ImportError:
            print("⚠️  Metrics exporter not available")
        except Exception as e:
            print(f"⚠️  Metrics server failed: {e}")
        
        # Update dashboard
        try:
            bot._update_monitoring_dashboard()
            print("✅ Dashboard initialized")
        except Exception as e:
            print(f"⚠️  Dashboard initialization failed: {e}")
        
        print("✅ Monitoring services started")
        
    except Exception as e:
        print(f"⚠️  Monitoring services partially failed: {e}")

def main():
    """Main startup sequence"""
    print("🚀 Enhanced Autonomous Trading Bot Startup")
    print("=" * 50)
    
    try:
        # Environment setup
        setup_environment()
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Environment variables loaded")
        except ImportError:
            print("⚠️  python-dotenv not available, using system environment")
        
        # Validate dependencies and API keys
        install_dependencies()
        validate_api_keys()
        
        # Create and configure bot
        bot = create_startup_bot()
        
        # Run pre-flight checks
        if not run_pre_flight_checks(bot):
            response = input("\n⚠️  Some checks failed. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("❌ Startup cancelled by user")
                sys.exit(1)
        
        # Start monitoring services
        start_monitoring_services(bot)
        
        # Display startup summary
        print("\n" + "=" * 50)
        print("🎯 Bot Configuration Summary:")
        print(f"   Paper Trading: {'Yes' if bot.config.get('PAPER_TRADING') else 'No'}")
        print(f"   Trading Capital: ${bot.config.get('TRADING_CAPITAL', 0):,}")
        print(f"   Risk Per Trade: {bot.config.get('RISK_PCT', 0)*100:.1f}%")
        print(f"   Max Positions: {bot.config.get('MAX_POSITIONS', 0)}")
        print(f"   Strategy: {bot.config.get('STRATEGY', 'unknown')}")
        print(f"   Extended Hours: {'Yes' if bot.config.get('EXTENDED_HOURS_ENABLED') else 'No'}")
        print(f"   Fallback Mode: {'Available' if hasattr(bot, 'fallback_mode') else 'Not available'}")
        
        # Show data provider status if available
        if hasattr(bot, 'get_data_provider_status'):
            try:
                status = bot.get_data_provider_status()
                enabled_sources = [name for name, info in status.items() if info['enabled']]
                print(f"   Data Sources: {', '.join(enabled_sources)}")
            except:
                pass
        
        print("=" * 50)
        
        # Final confirmation
        print("\n🚀 Ready to start autonomous trading!")
        print("📊 Monitor progress at:")
        print("   - Dashboard: dashboard.html (auto-updated)")
        print("   - Logs: logs/algo_trading.log")
        print("   - State: bot_state.json")
        print("   - Metrics: http://localhost:8000/metrics (if available)")
        
        response = input("\nStart trading? (Y/n): ")
        if response.lower() == 'n':
            print("❌ Trading cancelled by user")
            sys.exit(0)
        
        # Start the bot
        print("\n🏁 Starting autonomous trading...")
        print("   Press Ctrl+C to stop gracefully")
        print("   Bot will handle errors and API failures automatically")
        print("\n" + "=" * 50)
        
        # Run the bot
        if hasattr(bot, 'run_autonomous'):
            # Enhanced autonomous bot
            asyncio.run(bot.run_autonomous())
        else:
            # Base bot with enhancements
            try:
                bot.run()
            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested by user")
            except Exception as e:
                print(f"💥 Critical error: {e}")
                traceback.print_exc()
        
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted by user")
    except Exception as e:
        print(f"💥 Startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)

def quick_start():
    """Quick start for testing"""
    print("⚡ Quick Start Mode")
    
    # Minimal checks
    if not os.getenv('APCA_API_KEY_ID') or not os.getenv('APCA_API_SECRET_KEY'):
        print("❌ Missing Alpaca API keys")
        sys.exit(1)
    
    # Create simple config
    config = {
        'API_KEY': os.getenv('APCA_API_KEY_ID'),
        'SECRET_KEY': os.getenv('APCA_API_SECRET_KEY'),
        'PAPER_TRADING': True,
        'RISK_PCT': 0.01,
        'MAX_POSITIONS': 1,
        'MAX_DAILY_LOSS': 0.01,
        'STRATEGY': 'trend'
    }
    
    # Try to create basic bot
    try:
        from algo_trading_bot_v5 import AlgoTradingBot
        bot = AlgoTradingBot(config)
        
        # Apply critical fixes
        try:
            from enhanced_algo_bot_fixes import apply_enhanced_fixes
            apply_enhanced_fixes(bot)
        except:
            pass
        
        # Quick test
        print("🧪 Quick test...")
        symbols = bot._select_symbols()
        print(f"✅ Found {len(symbols)} symbols")
        
        quote = bot.get_real_time_data('AAPL')
        if not quote.empty:
            print(f"✅ Data access working: AAPL at ${quote['ask'].iloc[0]:.2f}")
        else:
            print("⚠️  Data access limited")
        
        print("✅ Quick start successful - run main() for full startup")
        return bot
        
    except Exception as e:
        print(f"❌ Quick start failed: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        quick_start()
    else:
        main()