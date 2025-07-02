"""
Dashboard infrastructure module.

Provides web-based monitoring and ngrok tunnel management for the trading bot.
"""

from .dashboard_server import DashboardServer, NgrokTunnel

__all__ = ['DashboardServer', 'NgrokTunnel']