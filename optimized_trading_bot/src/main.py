"""
Main application entry point for the optimized trading bot.

This module handles application startup, dependency injection,
and orchestration of the entire trading system.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional
import argparse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.manager import ConfigurationManager, DefaultConfigurationValidator
from config.providers import FileConfigProvider, EnvironmentConfigProvider, DefaultConfigProvider
from config.models import BotConfiguration, EnvironmentType
from application.enhanced_trading_bot import EnhancedTradingBot
from infrastructure.dashboard import DashboardServer, NgrokTunnel
from dotenv import load_dotenv


class TradingBotApplication:
    """
    Main application class for the optimized trading bot.
    
    Handles startup, shutdown, and lifecycle management of all components.
    """
    
    def __init__(self):
        self.config: Optional[BotConfiguration] = None
        self.config_manager: Optional[ConfigurationManager] = None
        self.trading_bot: Optional[EnhancedTradingBot] = None
        self.dashboard_server: Optional[DashboardServer] = None
        self.ngrok_tunnel: Optional[NgrokTunnel] = None
        self.logger: Optional[logging.Logger] = None
        self._shutdown_event = asyncio.Event()
        self._tasks = []
    
    async def initialize(self, config_path: Optional[str] = None, validate_only: bool = False) -> None:
        """Initialize the application with configuration and dependencies."""
        try:
            # Load environment variables from .env file
            load_dotenv()
            
            # Setup configuration providers
            providers = [DefaultConfigProvider()]
            
            # Add environment provider
            providers.append(EnvironmentConfigProvider())
            
            # Add file provider if specified
            if config_path:
                providers.append(FileConfigProvider(config_path))
            else:
                # Try default config locations
                default_configs = [
                    "config/production.yaml",
                    "config/development.yaml", 
                    "config.yaml",
                    "trading_bot_config.yaml"
                ]
                for config_file in default_configs:
                    if Path(config_file).exists():
                        providers.append(FileConfigProvider(config_file))
                        break
            
            # Initialize configuration manager
            validators = [DefaultConfigurationValidator()]
            self.config_manager = ConfigurationManager(providers, validators)
            self.config = await self.config_manager.load_configuration()
            
            # Override API credentials from environment variables if available
            import os
            if os.getenv('APCA_API_KEY_ID') or os.getenv('ALPACA_API_KEY'):
                api_key = os.getenv('APCA_API_KEY_ID') or os.getenv('ALPACA_API_KEY')
                secret_key = os.getenv('APCA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
                paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
                
                if api_key and secret_key:
                    self.config.api_credentials.key_id = api_key
                    self.config.api_credentials.secret_key = secret_key
                    self.config.api_credentials.paper_trading = paper_trading
            
            # Setup basic logging
            self._setup_logging()
            self.logger = logging.getLogger(__name__)
            
            self.logger.info(f"🚀 Starting {self.config.bot_name} v{self.config.version}")
            self.logger.info(f"📊 Environment: {self.config.environment.value}")
            self.logger.info(f"📈 Paper Trading: {self.config.is_paper_trading()}")
            
            # Only initialize trading components if not just validating config
            if not validate_only:
                # Initialize enhanced trading bot directly
                from infrastructure.brokers.alpaca_client import AlpacaClient
                from infrastructure.data_sources.multi_source_provider import MultiSourceDataProvider
                from core.trading.services import TradingService, PositionManager, PortfolioManager
                from events.event_bus import EventBus
                
                # Initialize components
                event_bus = EventBus()
                alpaca_client = AlpacaClient(self.config.api_credentials, self.logger)
                data_provider = MultiSourceDataProvider(self.config.data, self.logger)
                quote_provider = data_provider  # MultiSourceDataProvider implements both interfaces
                
                trading_service = TradingService(alpaca_client, self.logger)
                position_manager = PositionManager(trading_service, self.logger)
                portfolio_manager = PortfolioManager(position_manager, alpaca_client, self.logger)
                
                # Initialize enhanced trading bot
                self.trading_bot = EnhancedTradingBot(
                    config=self.config,
                    trading_service=trading_service,
                    position_manager=position_manager,
                    portfolio_manager=portfolio_manager,
                    data_provider=data_provider,
                    quote_provider=quote_provider,
                    event_bus=event_bus,
                    logger=self.logger
                )
                
                # Initialize dashboard server
                self.dashboard_server = DashboardServer(
                    port=8080,
                    logger=self.logger
                )
                
                # Initialize ngrok tunnel
                self.ngrok_tunnel = NgrokTunnel(
                    port=8080,
                    logger=self.logger
                )
            
            self.logger.info("✅ Application initialized successfully")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to initialize application: {e}")
            else:
                print(f"❌ Failed to initialize application: {e}")
            raise
    
    async def start(self) -> None:
        """Start the trading bot and all background services."""
        try:
            self.logger.info("🚀 Starting trading bot application...")
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start dashboard server
            if self.dashboard_server:
                self.dashboard_server.start()
                self.logger.info("🌐 Dashboard server started at http://localhost:8080")
                
                # Start ngrok tunnel
                if self.ngrok_tunnel:
                    tunnel_url = self.ngrok_tunnel.start_tunnel()
                    if tunnel_url:
                        self.logger.info(f"🌍 Remote dashboard available at: {tunnel_url}")
                    else:
                        self.logger.info("ℹ️ Remote dashboard not available (ngrok not installed or failed)")
            
            # Start trading bot
            trading_task = asyncio.create_task(self.trading_bot.start())
            self._tasks.append(trading_task)
            
            self.logger.info("✅ All services started successfully")
            self.logger.info("📈 Enhanced Trading Bot is now running...")
            self.logger.info("🌐 Dashboard: http://localhost:8080")
            self.logger.info("🛑 Press Ctrl+C to stop the bot")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"❌ Error during application startup: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        try:
            self.logger.info("🛑 Initiating graceful shutdown...")
            
            # Signal shutdown to all components
            self._shutdown_event.set()
            
            # Stop trading bot first
            if self.trading_bot:
                await self.trading_bot.stop()
            
            # Stop dashboard server
            if self.dashboard_server:
                self.dashboard_server.stop()
            
            # Stop ngrok tunnel
            if self.ngrok_tunnel:
                self.ngrok_tunnel.stop_tunnel()
            
            # Cancel all background tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.logger.info("✅ Application shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.monitoring.log_level.value, logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_file_path = Path(self.config.monitoring.log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format=self.config.monitoring.log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file_path) if self.config.monitoring.log_to_file else logging.NullHandler()
            ]
        )
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"🔔 Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Optimized Trading Bot')
    parser.add_argument('--config', '-c', type=str, help='Configuration file path')
    parser.add_argument('--log-level', '-l', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Log level')
    parser.add_argument('--paper-trading', action='store_true', 
                       help='Force paper trading mode')
    parser.add_argument('--validate-config', action='store_true',
                       help='Validate configuration and exit')
    
    args = parser.parse_args()
    
    app = TradingBotApplication()
    
    try:
        # Initialize application 
        validate_only = args.validate_config
        await app.initialize(args.config, validate_only=validate_only)
        
        # Override paper trading if specified
        if args.paper_trading:
            app.config.api_credentials.paper_trading = True
        
        # Validate configuration if requested
        if args.validate_config:
            print("✅ Configuration validation completed successfully")
            return
        
        # Check for production safeguards
        if (app.config.environment == EnvironmentType.PRODUCTION and 
            app.config.is_paper_trading()):
            print("⚠️  WARNING: Production environment with paper trading enabled")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                return
        
        # Start the application
        await app.start()
        
    except KeyboardInterrupt:
        print("\\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Application failed: {e}")
        return 1
    finally:
        try:
            await app.shutdown()
        except:
            pass
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n🛑 Shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)