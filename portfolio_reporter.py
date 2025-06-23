#!/usr/bin/env python3
"""
Comprehensive Portfolio Reporter for Industry-Grade Trading Bot
Generates detailed performance reports, visualizations, and shareable summaries
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import os
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import base64
from io import BytesIO

# Set style for professional-looking charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    total_return: float
    daily_pnl: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    avg_trade_duration: float
    best_trade: float
    worst_trade: float
    consecutive_wins: int
    consecutive_losses: int
    profit_factor: float
    
class PortfolioReporter:
    """
    Comprehensive portfolio reporting system
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger('AlgoTradingBot.reporter')
        
        # Ensure output directories exist
        self.reports_dir = Path('reports')
        self.reports_dir.mkdir(exist_ok=True)
        (self.reports_dir / 'charts').mkdir(exist_ok=True)
        
        # Load data sources
        self.bot_state = self._load_bot_state()
        self.trade_history = self._load_trade_history()
        self.dashboard_data = self._load_dashboard_data()
        self.daily_digests = self._load_daily_digests()
        
    def _load_bot_state(self) -> Dict:
        """Load bot state data"""
        try:
            if Path('bot_state.json').exists():
                with open('bot_state.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load bot state: {e}")
        return {}
    
    def _load_dashboard_data(self) -> Dict:
        """Load current dashboard data"""
        try:
            if Path('dashboard.json').exists():
                with open('dashboard.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load dashboard data: {e}")
        return {}
    
    def _load_trade_history(self) -> List[Dict]:
        """Load trade history from logs and bot data"""
        trades = []
        
        # Load from bot instance if available
        if self.bot and hasattr(self.bot, 'metrics') and hasattr(self.bot.metrics, 'trades'):
            for trade in self.bot.metrics.trades:
                trades.append({
                    'symbol': getattr(trade, 'symbol', 'Unknown'),
                    'entry_time': getattr(trade, 'entry_time', datetime.now()),
                    'exit_time': getattr(trade, 'exit_time', datetime.now()),
                    'entry_price': getattr(trade, 'entry_price', 0),
                    'exit_price': getattr(trade, 'exit_price', 0),
                    'quantity': getattr(trade, 'quantity', 0),
                    'pnl': getattr(trade, 'pnl', 0),
                    'strategy': getattr(trade, 'strategy', 'unknown'),
                    'duration_hours': (getattr(trade, 'exit_time', datetime.now()) - 
                                     getattr(trade, 'entry_time', datetime.now())).total_seconds() / 3600
                })
        
        # Load from trade logs if available
        try:
            if Path('logs/trades.log').exists():
                with open('logs/trades.log', 'r') as f:
                    for line in f:
                        if 'TRADE_CLOSED' in line:
                            # Parse trade log format: TRADE_CLOSED,SYMBOL,EXIT_PRICE,PNL,REASON
                            parts = line.strip().split(',')
                            if len(parts) >= 4:
                                trades.append({
                                    'symbol': parts[1],
                                    'exit_price': float(parts[2]) if parts[2] != 'N/A' else 0,
                                    'pnl': float(parts[3]) if parts[3] != 'N/A' else 0,
                                    'exit_reason': parts[4] if len(parts) > 4 else 'Unknown',
                                    'timestamp': datetime.now()
                                })
        except Exception as e:
            self.logger.debug(f"Failed to parse trade logs: {e}")
        
        return trades
    
    def _load_daily_digests(self) -> List[Dict]:
        """Load historical daily digest files"""
        digests = []
        
        try:
            # Find all daily digest files
            digest_files = list(Path('.').glob('daily_digest_*.json'))
            
            for digest_file in sorted(digest_files):
                try:
                    with open(digest_file, 'r') as f:
                        digest = json.load(f)
                        digest['file_date'] = digest_file.stem.split('_')[-1]
                        digests.append(digest)
                except Exception as e:
                    self.logger.debug(f"Failed to load digest {digest_file}: {e}")
        
        except Exception as e:
            self.logger.warning(f"Failed to load daily digests: {e}")
        
        return digests
    
    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        try:
            trades_df = pd.DataFrame(self.trade_history)
            
            if trades_df.empty:
                return PerformanceMetrics(
                    total_return=0, daily_pnl=0, win_rate=0, sharpe_ratio=0,
                    max_drawdown=0, total_trades=0, avg_trade_duration=0,
                    best_trade=0, worst_trade=0, consecutive_wins=0,
                    consecutive_losses=0, profit_factor=0
                )
            
            # Basic metrics
            total_pnl = trades_df['pnl'].sum() if 'pnl' in trades_df.columns else 0
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
            win_rate = (winning_trades / max(1, total_trades)) * 100
            
            # Advanced metrics
            if 'pnl' in trades_df.columns:
                best_trade = trades_df['pnl'].max()
                worst_trade = trades_df['pnl'].min()
                
                # Profit factor
                gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
                gross_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
                profit_factor = gross_profit / max(1, gross_loss)
                
                # Sharpe ratio approximation (assuming daily returns)
                daily_returns = trades_df['pnl'] / 1000  # Normalize by typical account size
                sharpe_ratio = daily_returns.mean() / max(daily_returns.std(), 0.001) * np.sqrt(252)
                
                # Max drawdown
                cumulative_pnl = trades_df['pnl'].cumsum()
                running_max = cumulative_pnl.expanding().max()
                drawdown = (cumulative_pnl - running_max)
                max_drawdown = abs(drawdown.min())
            else:
                best_trade = worst_trade = profit_factor = sharpe_ratio = max_drawdown = 0
            
            # Trade duration
            if 'duration_hours' in trades_df.columns:
                avg_trade_duration = trades_df['duration_hours'].mean()
            else:
                avg_trade_duration = 0
            
            # Consecutive wins/losses
            consecutive_wins = consecutive_losses = 0
            if 'pnl' in trades_df.columns:
                current_win_streak = current_loss_streak = 0
                for pnl in trades_df['pnl']:
                    if pnl > 0:
                        current_win_streak += 1
                        consecutive_wins = max(consecutive_wins, current_win_streak)
                        current_loss_streak = 0
                    else:
                        current_loss_streak += 1
                        consecutive_losses = max(consecutive_losses, current_loss_streak)
                        current_win_streak = 0
            
            # Total return calculation
            initial_capital = self.bot_state.get('initial_capital', 50000)
            total_return = (total_pnl / initial_capital) * 100 if initial_capital > 0 else 0
            
            # Daily P&L from dashboard
            daily_pnl = self.dashboard_data.get('daily_pnl', 0)
            
            return PerformanceMetrics(
                total_return=total_return,
                daily_pnl=daily_pnl,
                win_rate=win_rate,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                total_trades=total_trades,
                avg_trade_duration=avg_trade_duration,
                best_trade=best_trade,
                worst_trade=worst_trade,
                consecutive_wins=consecutive_wins,
                consecutive_losses=consecutive_losses,
                profit_factor=profit_factor
            )
            
        except Exception as e:
            self.logger.error(f"Performance calculation failed: {e}")
            return PerformanceMetrics(
                total_return=0, daily_pnl=0, win_rate=0, sharpe_ratio=0,
                max_drawdown=0, total_trades=0, avg_trade_duration=0,
                best_trade=0, worst_trade=0, consecutive_wins=0,
                consecutive_losses=0, profit_factor=0
            )
    
    def generate_performance_charts(self) -> Dict[str, str]:
        """Generate performance visualization charts"""
        chart_paths = {}
        
        try:
            # Prepare data
            trades_df = pd.DataFrame(self.trade_history)
            
            if trades_df.empty:
                self.logger.warning("No trade data available for charts")
                return chart_paths
            
            # 1. Cumulative P&L Chart
            if 'pnl' in trades_df.columns:
                plt.figure(figsize=(12, 6))
                cumulative_pnl = trades_df['pnl'].cumsum()
                plt.plot(cumulative_pnl, linewidth=2, color='#2E86AB')
                plt.title('Cumulative P&L Over Time', fontsize=16, fontweight='bold')
                plt.xlabel('Trade Number')
                plt.ylabel('Cumulative P&L ($)')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                pnl_chart_path = self.reports_dir / 'charts' / 'cumulative_pnl.png'
                plt.savefig(pnl_chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths['cumulative_pnl'] = str(pnl_chart_path)
            
            # 2. Trade Distribution Chart
            if 'pnl' in trades_df.columns:
                plt.figure(figsize=(10, 6))
                plt.hist(trades_df['pnl'], bins=30, alpha=0.7, color='#A23B72', edgecolor='black')
                plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Break-even')
                plt.title('Trade P&L Distribution', fontsize=16, fontweight='bold')
                plt.xlabel('P&L per Trade ($)')
                plt.ylabel('Frequency')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                dist_chart_path = self.reports_dir / 'charts' / 'trade_distribution.png'
                plt.savefig(dist_chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths['trade_distribution'] = str(dist_chart_path)
            
            # 3. Symbol Performance Chart
            if 'symbol' in trades_df.columns and 'pnl' in trades_df.columns:
                symbol_performance = trades_df.groupby('symbol')['pnl'].agg(['sum', 'count']).reset_index()
                symbol_performance = symbol_performance.sort_values('sum', ascending=True)
                
                if not symbol_performance.empty:
                    plt.figure(figsize=(12, 8))
                    colors = ['red' if x < 0 else 'green' for x in symbol_performance['sum']]
                    bars = plt.barh(symbol_performance['symbol'], symbol_performance['sum'], color=colors, alpha=0.7)
                    plt.title('Performance by Symbol', fontsize=16, fontweight='bold')
                    plt.xlabel('Total P&L ($)')
                    plt.ylabel('Symbol')
                    
                    # Add value labels on bars
                    for bar in bars:
                        width = bar.get_width()
                        plt.text(width, bar.get_y() + bar.get_height()/2, 
                                f'${width:.0f}', ha='left' if width >= 0 else 'right', 
                                va='center', fontweight='bold')
                    
                    plt.grid(True, alpha=0.3, axis='x')
                    plt.tight_layout()
                    
                    symbol_chart_path = self.reports_dir / 'charts' / 'symbol_performance.png'
                    plt.savefig(symbol_chart_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    chart_paths['symbol_performance'] = str(symbol_chart_path)
            
            # 4. Daily Performance Heatmap
            if self.daily_digests:
                daily_data = []
                for digest in self.daily_digests:
                    if 'performance' in digest:
                        daily_data.append({
                            'date': digest.get('file_date', ''),
                            'daily_pnl': digest['performance'].get('daily_pnl', 0)
                        })
                
                if daily_data:
                    daily_df = pd.DataFrame(daily_data)
                    daily_df['date'] = pd.to_datetime(daily_df['date'], format='%Y%m%d', errors='coerce')
                    daily_df = daily_df.dropna()
                    
                    if not daily_df.empty:
                        # Create calendar heatmap
                        daily_df['year'] = daily_df['date'].dt.year
                        daily_df['month'] = daily_df['date'].dt.month
                        daily_df['day'] = daily_df['date'].dt.day
                        
                        pivot_data = daily_df.pivot_table(values='daily_pnl', 
                                                         index=['year', 'month'], 
                                                         columns='day', 
                                                         fill_value=0)
                        
                        plt.figure(figsize=(15, 8))
                        sns.heatmap(pivot_data, cmap='RdYlGn', center=0, 
                                   annot=True, fmt='.0f', cbar_kws={'label': 'Daily P&L ($)'})
                        plt.title('Daily Performance Calendar', fontsize=16, fontweight='bold')
                        plt.tight_layout()
                        
                        heatmap_path = self.reports_dir / 'charts' / 'daily_heatmap.png'
                        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
                        plt.close()
                        chart_paths['daily_heatmap'] = str(heatmap_path)
            
        except Exception as e:
            self.logger.error(f"Chart generation failed: {e}")
        
        return chart_paths
    
    def generate_shareable_summary(self) -> str:
        """Generate a concise, shareable text summary"""
        try:
            metrics = self.calculate_performance_metrics()
            
            # Current status
            current_equity = self.dashboard_data.get('equity', 0)
            active_positions = self.dashboard_data.get('positions', 0)
            bot_status = self.dashboard_data.get('status', 'unknown')
            
            # Recent performance
            recent_days = 7
            recent_digests = self.daily_digests[-recent_days:] if len(self.daily_digests) >= recent_days else self.daily_digests
            recent_pnl = sum(d.get('performance', {}).get('daily_pnl', 0) for d in recent_digests)
            
            summary = f"""
🤖 **AUTONOMOUS TRADING BOT PERFORMANCE REPORT**
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 **ACCOUNT OVERVIEW**
Current Equity: ${current_equity:,.2f}
Daily P&L: ${metrics.daily_pnl:,.2f}
Total Return: {metrics.total_return:.2f}%
Bot Status: {bot_status.upper()}

📊 **TRADING PERFORMANCE**
Total Trades: {metrics.total_trades}
Win Rate: {metrics.win_rate:.1f}%
Profit Factor: {metrics.profit_factor:.2f}
Sharpe Ratio: {metrics.sharpe_ratio:.2f}

🎯 **BEST & WORST**
Best Trade: ${metrics.best_trade:,.2f}
Worst Trade: ${metrics.worst_trade:,.2f}
Max Drawdown: ${metrics.max_drawdown:,.2f}

📈 **RECENT PERFORMANCE ({recent_days} days)**
Recent P&L: ${recent_pnl:,.2f}
Active Positions: {active_positions}
Avg Trade Duration: {metrics.avg_trade_duration:.1f} hours

🔥 **STREAKS**
Best Win Streak: {metrics.consecutive_wins} trades
Worst Loss Streak: {metrics.consecutive_losses} trades

⚙️ **SYSTEM STATUS**
Uptime: {self.bot_state.get('uptime_hours', 0):.1f} hours
Total Trades Executed: {self.bot_state.get('total_trades', 0)}
Last Update: {self.dashboard_data.get('timestamp', 'Unknown')}
"""
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return f"Error generating summary: {e}"
    
    def generate_detailed_report(self) -> Dict:
        """Generate comprehensive detailed report"""
        try:
            metrics = self.calculate_performance_metrics()
            charts = self.generate_performance_charts()
            
            # Analyze trading patterns
            trades_df = pd.DataFrame(self.trade_history)
            trading_analysis = {}
            
            if not trades_df.empty:
                # Symbol analysis
                if 'symbol' in trades_df.columns:
                    symbol_stats = trades_df.groupby('symbol').agg({
                        'pnl': ['sum', 'mean', 'count'],
                        'duration_hours': 'mean'
                    }).round(2)
                    trading_analysis['symbol_performance'] = symbol_stats.to_dict() if not symbol_stats.empty else {}
                
                # Strategy analysis
                if 'strategy' in trades_df.columns:
                    strategy_stats = trades_df.groupby('strategy').agg({
                        'pnl': ['sum', 'mean', 'count']
                    }).round(2)
                    trading_analysis['strategy_performance'] = strategy_stats.to_dict() if not strategy_stats.empty else {}
                
                # Time analysis
                if 'entry_time' in trades_df.columns:
                    trades_df['hour'] = pd.to_datetime(trades_df['entry_time']).dt.hour
                    hourly_stats = trades_df.groupby('hour')['pnl'].agg(['sum', 'mean', 'count']).round(2)
                    trading_analysis['hourly_performance'] = hourly_stats.to_dict() if not hourly_stats.empty else {}
            
            # Risk analysis
            risk_metrics = {
                'value_at_risk_95': np.percentile(trades_df['pnl'], 5) if 'pnl' in trades_df.columns else 0,
                'expected_shortfall': trades_df[trades_df['pnl'] < np.percentile(trades_df['pnl'], 5)]['pnl'].mean() if 'pnl' in trades_df.columns else 0,
                'volatility': trades_df['pnl'].std() if 'pnl' in trades_df.columns else 0,
                'skewness': trades_df['pnl'].skew() if 'pnl' in trades_df.columns else 0,
                'kurtosis': trades_df['pnl'].kurtosis() if 'pnl' in trades_df.columns else 0
            }
            
            report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'report_period': {
                        'start_date': min(trades_df['entry_time']).isoformat() if 'entry_time' in trades_df.columns and not trades_df.empty else None,
                        'end_date': max(trades_df['exit_time']).isoformat() if 'exit_time' in trades_df.columns and not trades_df.empty else None,
                        'total_days': (datetime.now() - datetime.fromisoformat(self.bot_state.get('last_run', datetime.now().isoformat()))).days if self.bot_state.get('last_run') else 0
                    },
                    'data_sources': {
                        'bot_state': bool(self.bot_state),
                        'trade_history': len(self.trade_history),
                        'daily_digests': len(self.daily_digests),
                        'dashboard_data': bool(self.dashboard_data)
                    }
                },
                'performance_metrics': {
                    'total_return_pct': metrics.total_return,
                    'daily_pnl': metrics.daily_pnl,
                    'win_rate_pct': metrics.win_rate,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'total_trades': metrics.total_trades,
                    'avg_trade_duration_hours': metrics.avg_trade_duration,
                    'best_trade': metrics.best_trade,
                    'worst_trade': metrics.worst_trade,
                    'consecutive_wins': metrics.consecutive_wins,
                    'consecutive_losses': metrics.consecutive_losses,
                    'profit_factor': metrics.profit_factor
                },
                'account_status': {
                    'current_equity': self.dashboard_data.get('equity', 0),
                    'active_positions': self.dashboard_data.get('positions', 0),
                    'bot_status': self.dashboard_data.get('status', 'unknown'),
                    'last_update': self.dashboard_data.get('timestamp', 'unknown')
                },
                'risk_analysis': risk_metrics,
                'trading_analysis': trading_analysis,
                'chart_files': charts,
                'recommendations': self._generate_recommendations(metrics, trading_analysis)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Detailed report generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, metrics: PerformanceMetrics, analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on performance"""
        recommendations = []
        
        try:
            # Win rate recommendations
            if metrics.win_rate < 40:
                recommendations.append("⚠️ Win rate below 40% - Consider reviewing entry criteria and strategy parameters")
            elif metrics.win_rate > 70:
                recommendations.append("✅ Excellent win rate - Consider increasing position sizes if risk allows")
            
            # Sharpe ratio recommendations
            if metrics.sharpe_ratio < 1.0:
                recommendations.append("📊 Low Sharpe ratio - Focus on reducing trade frequency and improving risk-adjusted returns")
            elif metrics.sharpe_ratio > 2.0:
                recommendations.append("🎯 Outstanding Sharpe ratio - Current strategy is well-optimized")
            
            # Drawdown recommendations
            if metrics.max_drawdown > 1000:  # $1000 drawdown
                recommendations.append("🛑 High drawdown detected - Implement tighter risk management and position sizing")
            
            # Trade frequency recommendations
            if metrics.total_trades > 100:
                recommendations.append("📈 High trade frequency - Monitor transaction costs and consider selective filtering")
            elif metrics.total_trades < 10:
                recommendations.append("⏰ Low trade frequency - Consider expanding symbol universe or relaxing entry criteria")
            
            # Duration recommendations
            if metrics.avg_trade_duration > 48:  # 48 hours
                recommendations.append("⌛ Long average holding periods - Consider implementing time-based exits")
            elif metrics.avg_trade_duration < 2:  # 2 hours
                recommendations.append("⚡ Very short holding periods - Ensure sufficient time for trades to develop")
            
            # Profit factor recommendations
            if metrics.profit_factor < 1.2:
                recommendations.append("💰 Low profit factor - Focus on cutting losses quickly and letting winners run")
            elif metrics.profit_factor > 2.0:
                recommendations.append("🚀 Excellent profit factor - Strategy shows strong edge")
            
            # Consecutive loss recommendations
            if metrics.consecutive_losses > 5:
                recommendations.append("🔄 High consecutive losses detected - Implement cooling-off periods after loss streaks")
            
            # Add general recommendations
            recommendations.append("📝 Regularly review and backtest strategy modifications")
            recommendations.append("🔍 Monitor market regime changes and adapt accordingly")
            recommendations.append("💾 Keep detailed records for continuous improvement")
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            recommendations.append("❓ Unable to generate specific recommendations due to data limitations")
        
        return recommendations
    
    def save_report(self, report_type: str = 'both') -> Dict[str, str]:
        """Save reports to files and return file paths"""
        saved_files = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            if report_type in ['summary', 'both']:
                # Save shareable summary
                summary = self.generate_shareable_summary()
                summary_path = self.reports_dir / f'portfolio_summary_{timestamp}.txt'
                
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                saved_files['summary'] = str(summary_path)
                
                # Also save as markdown for better formatting
                md_path = self.reports_dir / f'portfolio_summary_{timestamp}.md'
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(summary.replace('**', '**').replace('🤖', '## '))
                saved_files['summary_md'] = str(md_path)
            
            if report_type in ['detailed', 'both']:
                # Save detailed report
                detailed_report = self.generate_detailed_report()
                detailed_path = self.reports_dir / f'detailed_report_{timestamp}.json'
                
                with open(detailed_path, 'w', encoding='utf-8') as f:
                    json.dump(detailed_report, f, indent=2, default=str)
                saved_files['detailed'] = str(detailed_path)
                
                # Save as HTML for better readability
                html_path = self.reports_dir / f'portfolio_report_{timestamp}.html'
                html_content = self._generate_html_report(detailed_report)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                saved_files['html'] = str(html_path)
            
            self.logger.info(f"Reports saved: {list(saved_files.keys())}")
            return saved_files
            
        except Exception as e:
            self.logger.error(f"Report saving failed: {e}")
            return {'error': str(e)}
    
    def _generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML version of the detailed report"""
        try:
            metrics = report_data.get('performance_metrics', {})
            account = report_data.get('account_status', {})
            recommendations = report_data.get('recommendations', [])
            charts = report_data.get('chart_files', {})
            
            # Determine performance colors
            daily_pnl_class = 'positive' if metrics.get('daily_pnl', 0) >= 0 else 'negative'
            total_return_class = 'positive' if metrics.get('total_return_pct', 0) >= 0 else 'negative'
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #007bff; padding-bottom: 20px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; margin-top: 5px; font-size: 14px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .recommendations h3 {{ color: #495057; margin-top: 0; }}
        .rec-item {{ margin: 10px 0; padding: 8px; background: white; border-radius: 4px; }}
        .chart-container {{ text-align: center; margin: 30px 0; }}
        .chart-container h3 {{ color: #495057; }}
        .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 10px; }}
        .status-indicator {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .status-running {{ background: #28a745; }}
        .status-warning {{ background: #ffc107; }}
        .status-error {{ background: #dc3545; }}
        .timestamp {{ color: #6c757d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Autonomous Trading Bot Portfolio Report</h1>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>
                <span class="status-indicator {'status-running' if account.get('bot_status') == 'running' else 'status-warning'}"></span>
                Bot Status: {account.get('bot_status', 'Unknown').upper()}
            </p>
        </div>
        
        <h2>📊 Performance Overview</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value {total_return_class}">{metrics.get('total_return_pct', 0):.2f}%</div>
                <div class="metric-label">Total Return</div>
            </div>
            <div class="metric-card">
                <div class="metric-value {daily_pnl_class}">${metrics.get('daily_pnl', 0):,.2f}</div>
                <div class="metric-label">Today's P&L</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${account.get('current_equity', 0):,.2f}</div>
                <div class="metric-label">Current Equity</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.get('win_rate_pct', 0):.1f}%</div>
                <div class="metric-label">Win Rate</div>
            </div>
        </div>
        
        <h2>📈 Advanced Metrics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{metrics.get('sharpe_ratio', 0):.2f}</div>
                <div class="metric-label">Sharpe Ratio</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.get('profit_factor', 0):.2f}</div>
                <div class="metric-label">Profit Factor</div>
            </div>
            <div class="metric-card">
                <div class="metric-value negative">${metrics.get('max_drawdown', 0):,.2f}</div>
                <div class="metric-label">Max Drawdown</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.get('total_trades', 0)}</div>
                <div class="metric-label">Total Trades</div>
            </div>
        </div>
        
        <h2>🎯 Trade Performance</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value positive">${metrics.get('best_trade', 0):,.2f}</div>
                <div class="metric-label">Best Trade</div>
            </div>
            <div class="metric-card">
                <div class="metric-value negative">${metrics.get('worst_trade', 0):,.2f}</div>
                <div class="metric-label">Worst Trade</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.get('avg_trade_duration_hours', 0):.1f}h</div>
                <div class="metric-label">Avg Trade Duration</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{account.get('active_positions', 0)}</div>
                <div class="metric-label">Active Positions</div>
            </div>
        </div>
        
        <h2>🔥 Streaks & Consistency</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value positive">{metrics.get('consecutive_wins', 0)}</div>
                <div class="metric-label">Best Win Streak</div>
            </div>
            <div class="metric-card">
                <div class="metric-value negative">{metrics.get('consecutive_losses', 0)}</div>
                <div class="metric-label">Worst Loss Streak</div>
            </div>
        </div>"""
            
            # Add charts if available
            if charts:
                html += "\n        <h2>📊 Performance Charts</h2>"
                
                for chart_name, chart_path in charts.items():
                    if os.path.exists(chart_path):
                        # Convert chart to base64 for embedding
                        try:
                            with open(chart_path, 'rb') as f:
                                chart_data = base64.b64encode(f.read()).decode()
                            chart_title = chart_name.replace('_', ' ').title()
                            html += f"""
        <div class="chart-container">
            <h3>{chart_title}</h3>
            <img src="data:image/png;base64,{chart_data}" alt="{chart_title}">
        </div>"""
                        except Exception as e:
                            html += f"""
        <div class="chart-container">
            <h3>{chart_name.replace('_', ' ').title()}</h3>
            <p>Chart not available: {str(e)}</p>
        </div>"""
            
            # Add recommendations
            if recommendations:
                html += """
        <div class="recommendations">
            <h3>💡 AI-Generated Recommendations</h3>"""
                
                for rec in recommendations:
                    html += f'            <div class="rec-item">{rec}</div>\n'
                
                html += "        </div>"
            
            html += """
        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6;">
            <p class="timestamp">Report generated by Autonomous Trading Bot v4.0</p>
            <p class="timestamp">⚠️ Past performance does not guarantee future results</p>
        </div>
    </div>
</body>
</html>"""
            
            return html
            
        except Exception as e:
            self.logger.error(f"HTML report generation failed: {e}")
            return f"<html><body><h1>Error generating report: {e}</h1></body></html>"

# Convenience functions for easy usage
def generate_quick_summary(bot_instance=None) -> str:
    """Generate a quick shareable summary"""
    reporter = PortfolioReporter(bot_instance)
    return reporter.generate_shareable_summary()

def generate_full_report(bot_instance=None, save_files=True) -> Dict:
    """Generate full report with optional file saving"""
    reporter = PortfolioReporter(bot_instance)
    report = reporter.generate_detailed_report()
    
    if save_files:
        saved_files = reporter.save_report('both')
        report['saved_files'] = saved_files
    
    return report

def create_portfolio_snapshot(bot_instance=None) -> str:
    """Create a quick portfolio snapshot for sharing"""
    try:
        reporter = PortfolioReporter(bot_instance)
        
        # Get current status
        current_equity = reporter.dashboard_data.get('equity', 0)
        daily_pnl = reporter.dashboard_data.get('daily_pnl', 0)
        active_positions = reporter.dashboard_data.get('positions', 0)
        
        # Calculate quick metrics
        trades_df = pd.DataFrame(reporter.trade_history)
        total_trades = len(trades_df)
        win_rate = 0
        
        if not trades_df.empty and 'pnl' in trades_df.columns:
            winning_trades = len(trades_df[trades_df['pnl'] > 0])
            win_rate = (winning_trades / max(1, total_trades)) * 100
        
        snapshot = f"""
🤖 TRADING BOT SNAPSHOT
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

💰 Equity: ${current_equity:,.2f}
📊 Today: ${daily_pnl:,.2f}
🎯 Positions: {active_positions}
📈 Trades: {total_trades} ({win_rate:.1f}% wins)

Status: ACTIVE ✅
"""
        return snapshot.strip()
        
    except Exception as e:
        return f"Error creating snapshot: {e}"

# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate portfolio performance reports')
    parser.add_argument('--type', choices=['summary', 'detailed', 'both', 'snapshot'], 
                       default='summary', help='Type of report to generate')
    parser.add_argument('--save', action='store_true', help='Save reports to files')
    parser.add_argument('--output', help='Output directory (default: reports/)')
    
    args = parser.parse_args()
    
    # Create reporter
    reporter = PortfolioReporter()
    
    if args.output:
        reporter.reports_dir = Path(args.output)
        reporter.reports_dir.mkdir(exist_ok=True)
    
    # Generate requested report
    if args.type == 'snapshot':
        print(create_portfolio_snapshot())
    elif args.type == 'summary':
        summary = reporter.generate_shareable_summary()
        print(summary)
        if args.save:
            files = reporter.save_report('summary')
            print(f"\n📁 Saved to: {files}")
    elif args.type == 'detailed':
        report = reporter.generate_detailed_report()
        print(f"Generated detailed report with {len(report)} sections")
        if args.save:
            files = reporter.save_report('detailed')
            print(f"📁 Saved to: {files}")
    elif args.type == 'both':
        print("=== QUICK SUMMARY ===")
        print(reporter.generate_shareable_summary())
        print("\n=== GENERATING DETAILED REPORT ===")
        report = reporter.generate_detailed_report()
        print(f"Detailed report generated with {len(report)} sections")
        if args.save:
            files = reporter.save_report('both')
            print(f"📁 All reports saved to: {files}")
    
    print(f"\n✅ Report generation complete!")