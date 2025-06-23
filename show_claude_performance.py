#!/usr/bin/env python3
"""
Instant Performance Reporter for Claude
Run this script to generate a comprehensive report of your trading bot's performance
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import glob

def load_bot_data():
    """Load all available bot data from files"""
    data = {
        'bot_state': {},
        'dashboard': {},
        'trades': [],
        'logs_summary': {},
        'daily_digests': []
    }
    
    # Load bot state
    try:
        if Path('bot_state.json').exists():
            with open('bot_state.json', 'r') as f:
                data['bot_state'] = json.load(f)
    except Exception as e:
        print(f"Note: Could not load bot_state.json: {e}")
    
    # Load dashboard
    try:
        if Path('dashboard.json').exists():
            with open('dashboard.json', 'r') as f:
                data['dashboard'] = json.load(f)
    except Exception as e:
        print(f"Note: Could not load dashboard.json: {e}")
    
    # Load daily digests
    try:
        digest_files = glob.glob('daily_digest_*.json')
        for digest_file in sorted(digest_files):
            with open(digest_file, 'r') as f:
                digest = json.load(f)
                digest['file_date'] = digest_file.split('_')[-1].replace('.json', '')
                data['daily_digests'].append(digest)
    except Exception as e:
        print(f"Note: Could not load daily digests: {e}")
    
    # Parse trade logs if available
    try:
        if Path('logs/trades.log').exists():
            with open('logs/trades.log', 'r') as f:
                for line in f:
                    if 'TRADE_CLOSED' in line or 'ENHANCED_TRADE' in line:
                        parts = line.strip().split(',')
                        if len(parts) >= 4:
                            trade_data = {
                                'timestamp': parts[0] if parts[0] else datetime.now().isoformat(),
                                'type': parts[1] if len(parts) > 1 else 'TRADE',
                                'symbol': parts[2] if len(parts) > 2 else 'UNKNOWN',
                                'action': parts[3] if len(parts) > 3 else 'UNKNOWN',
                                'details': parts[4:] if len(parts) > 4 else []
                            }
                            data['trades'].append(trade_data)
    except Exception as e:
        print(f"Note: Could not parse trade logs: {e}")
    
    # Analyze log files
    try:
        if Path('logs/algo_trading.log').exists():
            with open('logs/algo_trading.log', 'r') as f:
                lines = f.readlines()
                data['logs_summary'] = {
                    'total_lines': len(lines),
                    'recent_activity': lines[-10:] if lines else [],
                    'error_count': sum(1 for line in lines if 'ERROR' in line),
                    'warning_count': sum(1 for line in lines if 'WARNING' in line),
                    'trade_count': sum(1 for line in lines if 'TRADE' in line),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime('logs/algo_trading.log')).isoformat()
                }
    except Exception as e:
        print(f"Note: Could not analyze logs: {e}")
    
    return data

def calculate_performance_metrics(data: Dict) -> Dict:
    """Calculate performance metrics from available data"""
    metrics = {
        'account_summary': {},
        'trading_performance': {},
        'system_health': {},
        'recent_activity': {}
    }
    
    # Account summary from dashboard
    dashboard = data.get('dashboard', {})
    metrics['account_summary'] = {
        'current_equity': dashboard.get('equity', 0),
        'daily_pnl': dashboard.get('daily_pnl', 0),
        'active_positions': dashboard.get('positions', 0),
        'bot_status': dashboard.get('status', 'unknown'),
        'last_update': dashboard.get('timestamp', 'unknown')
    }
    
    # Trading performance from various sources
    bot_state = data.get('bot_state', {})
    metrics['trading_performance'] = {
        'total_trades': bot_state.get('total_trades', 0),
        'total_pnl': bot_state.get('total_pnl', 0),
        'uptime_hours': bot_state.get('uptime_hours', 0),
        'win_rate': dashboard.get('win_rate', 0),
        'performance_stats': bot_state.get('performance_stats', {})
    }
    
    # System health from logs
    logs = data.get('logs_summary', {})
    metrics['system_health'] = {
        'error_count': logs.get('error_count', 0),
        'warning_count': logs.get('warning_count', 0),
        'last_activity': logs.get('last_modified', 'unknown'),
        'log_entries': logs.get('total_lines', 0)
    }
    
    # Recent activity from daily digests
    digests = data.get('daily_digests', [])
    if digests:
        recent_digest = digests[-1]
        metrics['recent_activity'] = {
            'last_digest_date': recent_digest.get('file_date', 'unknown'),
            'recent_performance': recent_digest.get('performance', {}),
            'recent_trades': recent_digest.get('trades', []),
            'recommendations': recent_digest.get('recommendations', [])
        }
    
    return metrics

def generate_claude_report(data: Dict, metrics: Dict) -> str:
    """Generate comprehensive report for Claude"""
    
    account = metrics['account_summary']
    trading = metrics['trading_performance']
    health = metrics['system_health']
    recent = metrics['recent_activity']
    
    # Determine status indicators
    status_emoji = "🟢" if account['bot_status'] == 'running' else "🟡"
    pnl_emoji = "📈" if account['daily_pnl'] >= 0 else "📉"
    health_emoji = "🟢" if health['error_count'] < 5 else "🟡" if health['error_count'] < 20 else "🔴"
    
    report = f"""
🤖 **AUTONOMOUS TRADING BOT PERFORMANCE REPORT**
📅 **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{status_emoji} **SYSTEM STATUS**
Bot Status: {account['bot_status'].upper()}
Last Update: {account['last_update']}
System Health: {health_emoji} ({health['error_count']} errors, {health['warning_count']} warnings)
Uptime: {trading['uptime_hours']:.1f} hours

💰 **ACCOUNT PERFORMANCE**
Current Equity: ${account['current_equity']:,.2f}
Daily P&L: {pnl_emoji} ${account['daily_pnl']:,.2f}
Total P&L: ${trading['total_pnl']:,.2f}
Active Positions: {account['active_positions']}

📊 **TRADING STATISTICS**
Total Trades Executed: {trading['total_trades']}
Win Rate: {trading['win_rate']:.1f}%
System Logs: {health['log_entries']:,} entries
Recent Error Rate: {health['error_count']/max(1, health['log_entries'])*100:.2f}%

📈 **PERFORMANCE ANALYSIS**"""

    # Add performance stats if available
    perf_stats = trading.get('performance_stats', {})
    if perf_stats:
        report += f"""
Best Day: ${perf_stats.get('best_day', 0):,.2f}
Worst Day: ${perf_stats.get('worst_day', 0):,.2f}
Winning Streak: {perf_stats.get('consecutive_winning_days', 0)} days
Losing Streak: {perf_stats.get('consecutive_losing_days', 0)} days"""

    # Add recent activity
    if recent:
        report += f"""

🔄 **RECENT ACTIVITY**
Last Digest: {recent.get('last_digest_date', 'N/A')}"""
        
        recent_perf = recent.get('recent_performance', {})
        if recent_perf:
            report += f"""
Recent Daily P&L: ${recent_perf.get('daily_pnl', 0):,.2f}
Recent Trades: {recent_perf.get('trades_count', 0)}"""

    # Add daily digests summary
    digests = data.get('daily_digests', [])
    if digests:
        total_digest_pnl = sum(d.get('performance', {}).get('daily_pnl', 0) for d in digests)
        report += f"""

📚 **HISTORICAL SUMMARY**
Daily Digests Available: {len(digests)} days
Historical P&L Sum: ${total_digest_pnl:,.2f}
Data Coverage: {digests[0].get('file_date', 'unknown') if digests else 'N/A'} to {digests[-1].get('file_date', 'unknown') if digests else 'N/A'}"""

    # Add system capabilities
    report += f"""

⚙️ **SYSTEM CAPABILITIES**
- ✅ Autonomous trading with technical analysis
- ✅ Real-time market data processing
- ✅ Risk management and position sizing
- ✅ Extended hours trading support
- ✅ Event-driven trade filtering
- ✅ Comprehensive logging and monitoring
- ✅ Automated reporting and alerts
- ✅ Fallback modes for API failures

🎯 **TRADING STRATEGY**
- Multi-strategy approach (trend following + mean reversion)
- Fundamental data integration (earnings calendar)
- Economic event awareness (FOMC meetings)
- News sentiment analysis
- Adaptive stop losses and take profits
- ML-enhanced signal generation (when enabled)

📁 **DATA FILES ANALYSIS**"""

    # File analysis
    files_found = []
    if data['bot_state']:
        files_found.append("✅ bot_state.json - Bot configuration and state")
    if data['dashboard']:
        files_found.append("✅ dashboard.json - Real-time performance dashboard")
    if data['daily_digests']:
        files_found.append(f"✅ daily_digest_*.json - {len(data['daily_digests'])} daily reports")
    if data['logs_summary']:
        files_found.append(f"✅ algo_trading.log - {data['logs_summary']['total_lines']:,} log entries")
    if data['trades']:
        files_found.append(f"✅ trades.log - {len(data['trades'])} trade records")

    for file_info in files_found:
        report += f"\n{file_info}"

    if not files_found:
        report += "\n⚠️ No data files found - bot may be newly initialized"

    # Add recommendations based on data
    report += f"""

💡 **AI ANALYSIS & RECOMMENDATIONS**"""

    recommendations = []
    
    # Performance-based recommendations
    if account['daily_pnl'] < -500:
        recommendations.append("🔴 Significant daily loss detected - Review risk management settings")
    elif account['daily_pnl'] > 500:
        recommendations.append("🟢 Strong daily performance - Consider scaling successful strategies")
    
    if trading['win_rate'] < 40:
        recommendations.append("📊 Win rate below 40% - Analyze entry criteria and market conditions")
    elif trading['win_rate'] > 70:
        recommendations.append("🎯 Excellent win rate - Strategy is performing well")
    
    if health['error_count'] > 20:
        recommendations.append("⚠️ High error count - Check system stability and API connections")
    elif health['error_count'] == 0:
        recommendations.append("✅ No errors detected - System running smoothly")
    
    if account['active_positions'] == 0:
        recommendations.append("📈 No active positions - Check market conditions or entry criteria")
    elif account['active_positions'] > 5:
        recommendations.append("⚖️ High position count - Monitor risk exposure")
    
    # System recommendations
    if trading['uptime_hours'] > 168:  # 1 week
        recommendations.append("⏰ Extended uptime - Consider periodic restarts for optimal performance")
    
    if not data['daily_digests']:
        recommendations.append("📊 No daily digests found - Enable performance tracking")
    
    for rec in recommendations:
        report += f"\n{rec}"

    if not recommendations:
        report += "\n✅ System appears to be operating within normal parameters"

    report += f"""

🔗 **SYSTEM INTEGRATION STATUS**
- Data Collection: {'✅ Active' if any([data['bot_state'], data['dashboard'], data['logs_summary']]) else '❌ Limited'}
- Performance Tracking: {'✅ Active' if data['daily_digests'] else '⚠️ Partial'}
- Trade Logging: {'✅ Active' if data['trades'] else '⚠️ Limited'}
- Error Monitoring: {'✅ Active' if data['logs_summary'] else '❌ Inactive'}

📋 **NEXT STEPS**
1. Review any flagged recommendations above
2. Monitor system performance over the next 24-48 hours
3. Consider adjusting risk parameters if needed
4. Ensure all monitoring systems are functioning
5. Regular performance reviews recommended

---
**Report Notes:**
- This analysis is based on available data files from your trading bot
- Some metrics may be limited if the bot is newly started
- Real-time performance may vary from historical analysis
- Always verify trading decisions and monitor risk exposure

**Disclaimer:** This is an automated analysis. Past performance does not guarantee future results. Always review and validate trading decisions."""

    return report

def save_report_for_claude(report: str) -> str:
    """Save the report to a file and return the filename"""
    try:
        # Create reports directory
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = reports_dir / f'claude_performance_report_{timestamp}.txt'
        
        # Save report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(filename)
    except Exception as e:
        print(f"Warning: Could not save report to file: {e}")
        return "report_not_saved.txt"

def main():
    """Main function to generate and display the report"""
    print("🚀 Generating comprehensive performance report for Claude...")
    print("📊 Analyzing available data files...")
    
    # Load all available data
    data = load_bot_data()
    
    # Calculate metrics
    metrics = calculate_performance_metrics(data)
    
    # Generate Claude report
    report = generate_claude_report(data, metrics)
    
    # Display report
    print("\n" + "="*80)
    print("📈 TRADING BOT PERFORMANCE REPORT FOR CLAUDE")
    print("="*80)
    print(report)
    print("="*80)
    
    # Save report
    filename = save_report_for_claude(report)
    print(f"\n📁 Report saved to: {filename}")
    
    # Instructions
    print(f"""
💡 **INSTRUCTIONS FOR SHARING WITH CLAUDE:**

1. Copy the entire report above (from the header to the disclaimer)
2. Paste it in your conversation with Claude
3. Ask Claude to analyze your bot's performance and provide insights

📋 **SAMPLE CLAUDE PROMPT:**
"Here's my autonomous trading bot's performance report. Please analyze the results and provide insights on the performance, risk management, and any recommendations for optimization:"

🔄 **TO REGENERATE THIS REPORT:**
Run this script again: python show_claude_performance.py

✅ Report generation complete!
""")

if __name__ == "__main__":
    main()