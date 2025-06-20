# 🧠 Trading Bot

A modular, production-grade trading bot built in Python that supports **real-time trading**, **extended hours**, **error recovery**, and **automated monitoring**, with a web-based dashboard and ML integrations.

---

## 🚀 Features

### ✅ Core Trading
- **Main Bot Engine (`main.py`)**: Manages full trading lifecycle, scheduling, and recovery.
- **Custom Trading Logic (`algo_trading_bot_v5.py`)**: Implements strategies using technical indicators.
- **Error Recovery (`error_recovery.py`)**: Recovers from disconnections, failed orders, or API issues.
- **Extended Hours Support (`extended_hours.py`)**: Handles pre-market and after-hours trades.

### 🏗️ Infrastructure
- **Infrastructure Module (`infrastructure.py`)**: Manages services like broker API sessions, connection stability, data caching, etc.

### 📊 Monitoring & Alerts
- **Monitoring Module (`monitoring.py`)**: Sends alerts via Telegram, Discord, or Twilio SMS on bot status, trades, or failures.
- **Health Checks**: Via shell scripts or scheduled cron jobs.

### 🧠 Machine Learning (Optional)
- ML models are stored in `data/ml_models/` and can be used for:
  - Predictive trading
  - Signal enhancement
  - Strategy tuning

### 🖥️ Web Dashboard
- Built using **Flask** and **Dash**.
- Monitors trading performance, live trades, balance, etc.
- Located at `dashboard/app.py`.

---

## 🗂️ Project Structure
<pre> ```plaintext trading_bot/ ├── main.py ├── algo_trading_bot_v5.py ├── error_recovery.py ├── extended_hours.py ├── infrastructure.py ├── monitoring.py ├── config/ │ ├── config.json │ ├── symbols.json │ └── strategies.json ├── logs/ │ ├── trading.log │ ├── errors.log │ ├── trades.log │ └── performance/ ├── data/ │ ├── historical/ │ ├── realtime/ │ └── ml_models/ ├── backups/ │ ├── daily/ │ └── critical/ ├── dashboard/ │ ├── static/ │ ├── templates/ │ └── app.py ├── tests/ │ ├── test_strategies.py │ ├── test_execution.py │ └── test_recovery.py ├── scripts/ │ ├── setup.sh │ ├── health_check.sh │ └── emergency_stop.sh ├── .env ├── .gitignore ├── requirements.txt └── README.md ``` </pre>