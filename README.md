# 🤖 Autonomous Trading Bot v3.0

A sophisticated, fully autonomous algorithmic trading bot built in Python that operates with minimal supervision, featuring advanced risk management, ML-enhanced signals, extended hours trading, and comprehensive monitoring capabilities.

## 🌟 Key Highlights

- **💰 Budget-Optimized**: Operates on <$10/day infrastructure costs
- **🎯 Capital Efficient**: Manages $50k accounts with $10k active trading capital  
- **🤖 Fully Autonomous**: Minimal human intervention required
- **🛡️ Production-Ready**: Built-in error recovery and health monitoring
- **📊 ML-Enhanced**: Optional machine learning signal integration
- **⏰ 24/7 Operation**: Extended hours trading with session-aware logic

---

## 🚀 Features

### **Core Trading Engine**
- **Multi-Strategy Support**: Trend following, mean reversion, and combined strategies
- **Advanced Risk Management**: Adaptive stop losses, Kelly Criterion position sizing, and daily loss limits
- **Real-Time Execution**: Sub-second trade execution with market microstructure analysis
- **Extended Hours Trading**: Pre-market (4:00-9:30 AM) and after-hours (4:00-8:00 PM) capabilities
- **Smart Order Routing**: Market vs limit order optimization based on liquidity

### **Advanced Intelligence**
- **ML Signal Enhancement**: Ensemble machine learning models for signal generation
- **Volatility-Based Exits**: Dynamic position management based on market volatility
- **Smart Symbol Filtering**: AI-powered stock selection from 80+ liquid symbols
- **Adaptive Risk Management**: Dynamic position sizing based on portfolio heat and market regime
- **Gap Analysis**: Pre-market gap detection and fade strategies

### **Autonomous Operations**
- **Self-Recovery**: Circuit breaker pattern with automatic error handling
- **Health Monitoring**: Continuous system health checks and diagnostics
- **State Persistence**: Automatic state saving and recovery across restarts
- **Maintenance Automation**: Scheduled cleanup, optimization, and model updates
- **Emergency Procedures**: Automatic position closure during critical failures

### **Monitoring & Alerts**
- **Real-Time Dashboard**: JSON-based performance monitoring with web interface
- **Smart Alert System**: Multi-channel notifications (Email, SMS, Telegram, Discord)
- **Daily Reporting**: Automated daily digest with performance analytics
- **Performance Metrics**: Win rate, Sharpe ratio, maximum drawdown tracking

---

## 📁 Project Structure

```
trading_bot/
├── main.py                      # Main autonomous trading bot entry point
├── algo_trading_bot_v5.py       # Core trading engine with enhanced features
├── error_recovery.py            # Circuit breaker and error recovery system
├── extended_hours.py            # Pre-market and after-hours trading logic
├── infrastructure.py            # Cost-optimized infrastructure management
├── monitoring.py                # Smart alerts and performance monitoring
├── bot_state.json              # Persistent bot state (auto-generated)
├── dashboard.json              # Real-time dashboard data (auto-generated)
├── daily_digest_YYYYMMDD.json  # Daily performance reports (auto-generated)
├── logs/                       # Automated log management
│   ├── algo_trading.log        # Main trading logs
│   ├── errors.log              # Error logs
│   ├── trades.log              # Trade execution logs
│   └── performance/            # Performance metrics
├── data/
│   ├── historical/             # Cached historical data
│   ├── ml_models/              # ML model storage
│   └── backups/                # Critical data backups
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## ⚙️ Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed on your system
- **Alpaca Trading Account** with API access (free paper trading available)
- **2GB+ RAM** recommended for optimal performance
- **10GB+ disk space** for data storage and logs
- **Stable internet connection** for real-time data feeds
- **Basic understanding** of trading concepts and risk management

---

## 🛠️ Installation & Setup

### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/autonomous-trading-bot.git
cd autonomous-trading-bot
```

### **2. Install Dependencies**
```bash
# Create virtual environment (recommended)
python -m venv trading_env
source trading_env/bin/activate  # On Windows: trading_env\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### **3. Set Environment Variables**
```bash
# Required Alpaca API Keys
export APCA_API_KEY_ID="your_alpaca_api_key"
export APCA_API_SECRET_KEY="your_alpaca_secret_key"

# Optional: Notification settings
export EMAIL_SENDER="your_email@gmail.com"
export EMAIL_PASSWORD="your_app_password"
export EMAIL_RECIPIENT="alerts@yourdomain.com"

# Optional: SMS alerts (requires Twilio)
export TWILIO_SID="your_twilio_sid"
export TWILIO_TOKEN="your_twilio_token"
export TWILIO_FROM="+1234567890"
export PHONE_NUMBER="+1987654321"

# Make environment variables persistent
echo 'export APCA_API_KEY_ID="your_alpaca_api_key"' >> ~/.bashrc
echo 'export APCA_API_SECRET_KEY="your_alpaca_secret_key"' >> ~/.bashrc
source ~/.bashrc
```

### **4. Verify Setup**
```bash
# Test API connectivity
python -c "
import os
from alpaca.trading.client import TradingClient
client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)
print('API Connected Successfully:', client.get_account().account_number)
"
```

### **5. Run the Bot**
```bash
# Development mode (foreground)
python main.py

# Production mode (background with logging)
nohup python main.py > bot.log 2>&1 &

# Check if running
ps aux | grep "python main.py"
```

---

## ⚙️ Configuration

The bot uses an internal configuration system in `main.py`. Key parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TOTAL_CAPITAL` | $50,000 | Total account capital |
| `TRADING_CAPITAL` | $10,000 | Active trading capital |
| `RISK_PCT` | 2% | Risk per trade (Kelly Criterion enhanced) |
| `MAX_POSITIONS` | 3 | Maximum concurrent positions |
| `MAX_DAILY_LOSS` | 2% | Daily loss limit ($1,000) |
| `STRATEGY` | 'combined' | Trading strategy type |
| `USE_ML_SIGNALS` | True | Enable ML enhancements |
| `PAPER_TRADING` | True | Start in paper trading mode |
| `EXTENDED_HOURS_ENABLED` | True | Pre/post market trading |
| `AUTO_RECOVERY_ENABLED` | True | Automatic error recovery |

### **Customizing Configuration**
Edit the configuration dictionary in `main.py`:

```python
config = {
    # Capital Management
    'TOTAL_CAPITAL': 50000,
    'TRADING_CAPITAL': 10000,
    'RISK_PCT': 0.02,                    # 2% risk per trade
    'MAX_POSITIONS': 3,
    'MAX_DAILY_LOSS': 0.02,              # 2% max daily loss
    
    # Strategy Configuration
    'STRATEGY': 'combined',              # 'trend', 'mean_reversion', 'combined'
    'USE_ML_SIGNALS': True,
    'USE_ADAPTIVE_STOPS': True,
    'USE_KELLY_CRITERION': True,
    
    # Trading Sessions
    'EXTENDED_HOURS_ENABLED': True,
    'PRE_MARKET_RISK_REDUCTION': 0.5,   # 50% position size reduction
    
    # Safety & Recovery
    'PAPER_TRADING': True,               # SET TO FALSE FOR LIVE TRADING
    'AUTO_RECOVERY_ENABLED': True,
    'CLOSE_ON_SHUTDOWN': False,
}
```

---

## 🎯 Trading Strategies

### **1. Trend Following Strategy**
- **Dual Moving Average Crossover** with EMA (12/26) and SMA (50)
- **MACD Confirmation** with signal line crossover
- **Volume Confirmation** (120% above 20-day average)
- **Volatility Filter** (ATR-based risk adjustment)
- **Support/Resistance Levels** for entry/exit optimization

### **2. Mean Reversion Strategy**
- **RSI Oscillator** (oversold <30, overbought >70)
- **Bollinger Bands** (2 standard deviations)
- **Stochastic Oscillator** (K%/D% confirmation)
- **Statistical Mean Reversion** (20-period moving average)
- **Multi-timeframe Analysis** for signal validation

### **3. Combined Strategy** ⭐ (Recommended)
- **Consensus Requirement**: 2 out of 3 signals must agree
- **Risk-Adjusted Scoring**: Weighted signal strength
- **Market Regime Detection**: Bull/bear/sideways adaptation
- **Correlation Analysis**: Avoid redundant positions
- **Dynamic Thresholds**: Volatility-adjusted entry/exit points

### **4. ML-Enhanced Signals** 🧠
- **Feature Engineering**: 50+ technical indicators
- **Ensemble Methods**: Combined model predictions
- **Real-time Learning**: Continuous model updates
- **Signal Confidence**: Probabilistic trade scoring
- **Market Microstructure**: Order book analysis

---

## 📊 Usage & Monitoring

### **Starting the Bot**
```bash
# Basic usage (development)
python main.py

# Background execution (production)
nohup python main.py > logs/bot.log 2>&1 &

# With custom configuration
PYTHONPATH=. python main.py --strategy=trend --risk=0.015

# Monitor process
tail -f logs/algo_trading.log
```

### **Real-Time Monitoring Files**
The bot automatically generates several monitoring files:

- **`dashboard.json`**: Real-time performance metrics
- **`bot_state.json`**: Persistent bot state and positions
- **`daily_digest_YYYYMMDD.json`**: Daily performance reports
- **`logs/trades.log`**: Detailed trade execution logs
- **`logs/algo_trading.log`**: System operation logs
- **`logs/errors.log`**: Error and recovery logs

### **Dashboard Data Structure**
```json
{
  "timestamp": "2025-06-22T16:35:00",
  "status": "running",
  "market_open": true,
  "equity": 50250.50,
  "daily_pnl": 250.50,
  "daily_pnl_pct": 0.50,
  "positions": 2,
  "total_trades": 45,
  "win_rate": 67.5,
  "sharpe_ratio": 1.85,
  "max_drawdown": 3.2,
  "position_details": {
    "AAPL": {
      "entry_price": 185.50,
      "current_pnl": 125.00,
      "stop_loss": 181.17,
      "take_profit": 192.35
    }
  }
}
```

### **Viewing Performance**
```bash
# Current dashboard
cat dashboard.json | python -m json.tool

# Real-time monitoring
watch -n 5 'cat dashboard.json | python -m json.tool'

# Recent trades
tail -20 logs/trades.log

# Error monitoring
tail -f logs/errors.log
```

### **Emergency Controls**
```bash
# Graceful shutdown (allows position closure)
pkill -SIGTERM -f "python main.py"

# Force stop (immediate shutdown)
pkill -SIGKILL -f "python main.py"

# Check system status
ps aux | grep python | grep main.py
```

---

## 🛡️ Risk Management

### **Position-Level Risk**
- **Adaptive Stop Loss**: ATR-based with support/resistance levels
- **Take Profit Targets**: Risk-reward ratio optimization (2:1 minimum)
- **Position Sizing**: Kelly Criterion with portfolio heat adjustment
- **Hold Time Limits**: Maximum 24-hour position duration
- **Volatility Exits**: Dynamic exit on 3x normal volatility

### **Portfolio-Level Risk**
- **Daily Loss Limits**: Automatic halt at 2% daily loss ($1,000)
- **Position Limits**: Maximum 3 concurrent positions
- **Correlation Analysis**: Avoid over-concentration in correlated assets
- **Market Regime Detection**: Risk reduction in high-stress markets
- **Portfolio Heat**: Maximum 60% average correlation between positions

### **System-Level Risk**
- **Circuit Breaker Pattern**: API failure protection with exponential backoff
- **Health Monitoring**: Continuous system diagnostics
- **Emergency Shutdown**: Automatic position closure on critical failures
- **Data Validation**: Real-time data quality checks
- **Rate Limiting**: API call optimization to prevent violations

---

## 🔍 Troubleshooting

### **Common Issues**

#### **Bot Won't Start**
```bash
# Check environment variables
echo $APCA_API_KEY_ID
echo $APCA_API_SECRET_KEY

# Verify API connectivity
python -c "
from alpaca.trading.client import TradingClient
import os
client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)
print('Account Status:', client.get_account().status)
"

# Check dependencies
pip install -r requirements.txt
```

#### **Trading Not Executing**
- ✅ Verify market hours (9:30 AM - 4:00 PM ET for regular session)
- ✅ Check account buying power and day trading limits
- ✅ Review risk management settings (daily loss limit, position limits)
- ✅ Examine `logs/errors.log` for specific error messages
- ✅ Ensure symbols are in the approved trading universe

#### **High Error Rate**
- 🌐 Check internet connectivity and API latency
- 🔑 Verify API key permissions and account status
- 📊 Review rate limiting settings and API usage
- 💻 Check system resources (CPU >80%, Memory >2GB)
- 📈 Monitor market volatility (may cause data issues)

### **Log Analysis**
```bash
# Recent errors
tail -50 logs/errors.log

# Trading activity
grep "TRADE_EXECUTED\|POSITION_CLOSED" logs/trades.log | tail -10

# System health
grep "Health\|Performance" logs/algo_trading.log | tail -10

# API issues
grep "API\|Connection" logs/errors.log | tail -10
```

### **Performance Diagnostics**
```bash
# Check bot state
cat bot_state.json | python -m json.tool

# Monitor resource usage
top -p $(pgrep -f "python main.py")

# Disk space check
df -h

# Network connectivity
ping -c 4 paper-api.alpaca.markets
```

---

## 📈 Performance Analytics

### **Key Metrics Tracked**
- **Total Return**: Cumulative portfolio performance
- **Daily P&L**: Real-time profit/loss tracking
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted returns (target >1.5)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Average Trade Duration**: Position holding time analysis
- **Profit Factor**: Gross profit ÷ gross loss ratio

### **Strategy Performance**
```python
# Example performance metrics
{
    "strategy_performance": {
        "trend_following": {
            "win_rate": 0.65,
            "avg_profit": 127.50,
            "avg_loss": -89.25,
            "profit_factor": 1.85
        },
        "mean_reversion": {
            "win_rate": 0.72,
            "avg_profit": 95.75,
            "avg_loss": -76.50,
            "profit_factor": 2.14
        },
        "combined": {
            "win_rate": 0.68,
            "avg_profit": 112.85,
            "avg_loss": -82.15,
            "profit_factor": 1.96
        }
    }
}
```

### **Risk Metrics**
- **Value at Risk (VaR)**: 95% confidence daily loss estimate
- **Portfolio Heat**: Average correlation between positions
- **Beta to Market**: Systematic risk exposure (SPY correlation)
- **Maximum Leverage**: Peak portfolio exposure
- **Volatility Targeting**: 2% daily volatility target

---

## 🚨 Alert System

### **Alert Categories**

#### **🔴 Critical Alerts** (Immediate notification via all channels)
- Daily loss limit exceeded ($1,000+)
- System health degraded (<70%)
- API connectivity lost
- Emergency shutdown triggered
- Account restrictions detected

#### **🟡 Warning Alerts** (Email + dashboard)
- Stop loss triggered
- Unusual market volatility detected
- Position held >20 hours
- Win rate below 50%
- High correlation risk (>80%)

#### **🔵 Info Alerts** (Daily digest only)
- New position opened
- Daily profit target reached ($500+)
- Successful trade completion
- Model performance update
- System maintenance completed

### **Notification Channels**
- **📧 Email**: Detailed alerts with context
- **📱 SMS**: Critical alerts only (via Twilio)
- **💬 Telegram**: Real-time updates (optional)
- **🎮 Discord**: Community integration (optional)

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### **Development Setup**
```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
python -m pytest tests/

# Code formatting
black *.py
flake8 *.py

# Type checking
mypy main.py
```

### **Contribution Process**
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### **Areas for Contribution**
- 🧠 Advanced ML models and feature engineering
- 📊 Additional technical indicators and strategies
- 🌐 Multi-broker integration (TD Ameritrade, Interactive Brokers)
- 📱 Mobile app for monitoring
- ☁️ Cloud deployment automation
- 🧪 Enhanced backtesting framework

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Important Disclaimers

### **Risk Warning**
> **This software is for educational and research purposes only. Algorithmic trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. You should never trade with money you cannot afford to lose.**

### **No Financial Advice**
> **This software does not constitute financial advice. All trading decisions are made by the user at their own discretion and risk. The authors and contributors are not licensed financial advisors and are not responsible for any financial losses incurred.**

### **Paper Trading Recommended**
> **We strongly recommend running the bot in paper trading mode extensively before considering live trading. Start with small amounts and gradually increase exposure only after thorough testing and validation.**

---

## 📞 Support

For questions, issues, or contributions:

- **🐛 Bug Reports**: [Create an issue](https://github.com/yourusername/autonomous-trading-bot/issues)
- **💡 Feature Requests**: [Open a discussion](https://github.com/yourusername/autonomous-trading-bot/discussions)
- **📖 Documentation**: Check the troubleshooting section above
- **📊 Logs**: Review logs in the `logs/` directory for detailed information
- **✅ Prerequisites**: Ensure all requirements are met before reporting issues

---

## 🎯 Roadmap

### **Phase 1 - Core Enhancement** (Current)
- [x] Multi-strategy trading engine
- [x] Advanced risk management
- [x] Error recovery system
- [x] Real-time monitoring
- [ ] Comprehensive backtesting framework

### **Phase 2 - Intelligence** (Q3 2025)
- [ ] Advanced ML model integration
- [ ] Sentiment analysis from news/social media
- [ ] Options trading capabilities
- [ ] Multi-timeframe analysis
- [ ] Market regime classification

### **Phase 3 - Scale** (Q4 2025)
- [ ] Multi-broker support
- [ ] Portfolio optimization algorithms
- [ ] Real-time web dashboard
- [ ] Mobile app for monitoring
- [ ] Cloud deployment templates

### **Phase 4 - Enterprise** (2026)
- [ ] Institutional features
- [ ] Advanced reporting and analytics
- [ ] API for third-party integration
- [ ] White-label solutions
- [ ] Regulatory compliance tools

---

## 🏆 Performance Goals

### **Target Metrics**
- **Annual Return**: 15-25% (net of fees)
- **Sharpe Ratio**: >1.5
- **Maximum Drawdown**: <10%
- **Win Rate**: >60%
- **Daily Trading**: 3-8 trades per day
- **Uptime**: >99.5%

### **Risk Targets**
- **Daily VaR**: <2% of portfolio
- **Maximum Position**: <5% of portfolio
- **Correlation Limit**: <60% average
- **Leverage**: None (cash account)

---

**Happy Trading! 🚀📈**

---