#!/usr/bin/env python3
"""
Easy integration script for portfolio reporting
Add this to your trading bot for instant portfolio reports
"""

import sys
from pathlib import Path

# Add the portfolio reporter to your bot
def integrate_portfolio_reporting(bot_instance):
    """
    Integrate portfolio reporting into your existing bot
    """
    try:
        from portfolio_reporter import PortfolioReporter, generate_quick_summary, generate_full_report
        
        # Add reporting methods to your bot
        import types
        
        def generate_portfolio_report(self, report_type='summary', save_to_file=True):
            """Generate portfolio performance report"""
            try:
                reporter = PortfolioReporter(self)
                
                if report_type == 'summary':
                    summary = reporter.generate_shareable_summary()
                    print("\n" + "="*60)
                    print("🤖 PORTFOLIO PERFORMANCE SUMMARY")
                    print("="*60)
                    print(summary)
                    print("="*60)
                    
                    if save_to_file:
                        files = reporter.save_report('summary')
                        print(f"\n📁 Summary saved to: {files.get('summary', 'N/A')}")
                    
                    return summary
                
                elif report_type == 'detailed':
                    report = reporter.generate_detailed_report()
                    print(f"\n📊 Generated detailed report with {len(report)} sections")
                    
                    if save_to_file:
                        files = reporter.save_report('detailed')
                        print(f"📁 Detailed report saved to: {files.get('html', 'N/A')}")
                    
                    return report
                
                elif report_type == 'both':
                    summary = reporter.generate_shareable_summary()
                    report = reporter.generate_detailed_report()
                    
                    print("\n" + "="*60)
                    print("🤖 PORTFOLIO PERFORMANCE SUMMARY")
                    print("="*60)
                    print(summary)
                    print("="*60)
                    
                    if save_to_file:
                        files = reporter.save_report('both')
                        print(f"\n📁 Reports saved:")
                        for report_name, file_path in files.items():
                            print(f"   - {report_name}: {file_path}")
                    
                    return {'summary': summary, 'detailed': report}
                
            except Exception as e:
                self.logger.error(f"Portfolio report generation failed: {e}")
                print(f"❌ Report generation failed: {e}")
                return None
        
        def get_quick_stats(self):
            """Get quick portfolio statistics"""
            try:
                from portfolio_reporter import create_portfolio_snapshot
                return create_portfolio_snapshot(self)
            except Exception as e:
                return f"Error getting stats: {e}"
        
        def send_performance_update(self, channel='console'):
            """Send performance update to specified channel"""
            try:
                summary = self.generate_portfolio_report('summary', save_to_file=False)
                
                if channel == 'email' and hasattr(self, 'alert_system'):
                    # Send via email if alert system is available
                    import asyncio
                    asyncio.create_task(self.alert_system.evaluate_alerts({
                        'custom_alert': True,
                        'alert_message': f"Daily Performance Update:\n{summary}",
                        'events': ['daily_performance_update']
                    }))
                    print("📧 Performance update sent via email")
                
                elif channel == 'console':
                    print(summary)
                
                return summary
                
            except Exception as e:
                self.logger.error(f"Performance update failed: {e}")
                return None
        
        # Add methods to bot instance
        bot_instance.generate_portfolio_report = types.MethodType(generate_portfolio_report, bot_instance)
        bot_instance.get_quick_stats = types.MethodType(get_quick_stats, bot_instance)
        bot_instance.send_performance_update = types.MethodType(send_performance_update, bot_instance)
        
        print("✅ Portfolio reporting integrated successfully!")
        print("\nNew methods available:")
        print("  - bot.generate_portfolio_report('summary')")
        print("  - bot.generate_portfolio_report('detailed')")
        print("  - bot.generate_portfolio_report('both')")
        print("  - bot.get_quick_stats()")
        print("  - bot.send_performance_update()")
        
        return True
        
    except ImportError:
        print("❌ Portfolio reporter not found. Make sure portfolio_reporter.py is in the same directory.")
        return False
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return False

# Standalone reporting functions
def generate_report_from_files(report_type='summary'):
    """Generate report directly from saved files (no bot instance needed)"""
    try:
        from portfolio_reporter import PortfolioReporter
        
        print("📊 Generating report from saved data...")
        reporter = PortfolioReporter(bot_instance=None)
        
        if report_type == 'summary':
            summary = reporter.generate_shareable_summary()
            print("\n" + "="*60)
            print("🤖 PORTFOLIO PERFORMANCE SUMMARY")
            print("="*60)
            print(summary)
            print("="*60)
            
            # Save to file
            files = reporter.save_report('summary')
            print(f"\n📁 Summary saved to: {files.get('summary', 'N/A')}")
            return summary
            
        elif report_type == 'detailed':
            report = reporter.generate_detailed_report()
            files = reporter.save_report('detailed')
            print(f"📊 Detailed report generated and saved to: {files.get('html', 'N/A')}")
            return report
            
        elif report_type == 'both':
            summary = reporter.generate_shareable_summary()
            report = reporter.generate_detailed_report()
            files = reporter.save_report('both')
            
            print("\n" + "="*60)
            print("🤖 PORTFOLIO PERFORMANCE SUMMARY")
            print("="*60)
            print(summary)
            print("="*60)
            
            print(f"\n📁 All reports saved:")
            for report_name, file_path in files.items():
                print(f"   - {report_name}: {file_path}")
            
            return {'summary': summary, 'detailed': report}
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return None

def quick_performance_check():
    """Quick performance check - minimal output"""
    try:
        from portfolio_reporter import create_portfolio_snapshot
        snapshot = create_portfolio_snapshot()
        print(snapshot)
        return snapshot
    except Exception as e:
        print(f"❌ Quick check failed: {e}")
        return None

# Command to show Claude your performance
def show_claude_performance():
    """Generate a comprehensive report formatted for sharing with Claude"""
    try:
        from portfolio_reporter import PortfolioReporter
        
        print("📊 Generating comprehensive report for Claude...")
        reporter = PortfolioReporter(bot_instance=None)
        
        # Generate summary
        summary = reporter.generate_shareable_summary()
        
        # Generate key metrics
        metrics = reporter.calculate_performance_metrics()
        
        # Create Claude-optimized report
        claude_report = f"""
{summary}

🔍 **DETAILED ANALYSIS FOR REVIEW**

**Risk Metrics:**
- Sharpe Ratio: {metrics.sharpe_ratio:.2f}
- Max Drawdown: ${metrics.max_drawdown:,.2f}
- Profit Factor: {metrics.profit_factor:.2f}
- Average Trade Duration: {metrics.avg_trade_duration:.1f} hours

**Trading Patterns:**
- Total Trades Executed: {metrics.total_trades}
- Best Single Trade: ${metrics.best_trade:,.2f}
- Worst Single Trade: ${metrics.worst_trade:,.2f}
- Longest Win Streak: {metrics.consecutive_wins} trades
- Longest Loss Streak: {metrics.consecutive_losses} trades

**Current Status:**
- Bot is {'ACTIVE' if reporter.dashboard_data.get('status') == 'running' else 'INACTIVE'}
- Active Positions: {reporter.dashboard_data.get('positions', 0)}
- Last Update: {reporter.dashboard_data.get('timestamp', 'Unknown')}

**Files Generated:**
- Detailed reports saved in 'reports/' directory
- Charts and visualizations available
- Raw data in JSON format for analysis

This trading bot has been running autonomously and executing trades based on technical analysis, fundamental data, economic events, and news sentiment. The system includes comprehensive risk management, fallback modes, and real-time monitoring.
"""
        
        print(claude_report)
        
        # Save comprehensive report
        timestamp = Path('reports').mkdir(exist_ok=True)
        claude_file = Path('reports') / f'claude_report_{Path().cwd().name}_{reporter.dashboard_data.get("timestamp", "").replace(":", "").replace("-", "").replace(" ", "_")[:15]}.txt'
        
        with open(claude_file, 'w', encoding='utf-8') as f:
            f.write(claude_report)
        
        print(f"\n📁 Comprehensive report saved to: {claude_file}")
        print("\n💡 You can copy and paste this report to show Claude your bot's performance!")
        
        return claude_report
        
    except Exception as e:
        print(f"❌ Claude report generation failed: {e}")
        return None

# Easy command-line usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Portfolio Reporting Integration')
    parser.add_argument('command', choices=['summary', 'detailed', 'both', 'quick', 'claude'], 
                       help='Type of report to generate')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save to files')
    
    args = parser.parse_args()
    
    if args.command == 'quick':
        quick_performance_check()
    elif args.command == 'claude':
        show_claude_performance()
    else:
        save_files = not args.no_save
        if args.command in ['summary', 'detailed', 'both']:
            generate_report_from_files(args.command)
        else:
            print("❌ Invalid command")

# Integration example for your bot
"""
USAGE EXAMPLES:

1. Add to your main bot file (main.py or enhanced_startup_script.py):

    from report_integration import integrate_portfolio_reporting
    
    # After creating your bot instance:
    bot = IndustryGradeAutonomousBot(config)
    integrate_portfolio_reporting(bot)
    
    # Now you can use:
    bot.generate_portfolio_report('summary')
    bot.get_quick_stats()

2. Generate reports without bot instance:

    python report_integration.py summary
    python report_integration.py detailed
    python report_integration.py claude

3. Quick performance check:

    python report_integration.py quick

4. Show Claude your performance:

    python report_integration.py claude
    
    This generates a comprehensive report formatted for sharing with Claude,
    including all key metrics, trading patterns, and system status.
"""