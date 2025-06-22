"""
Fundamental Data Provider
Handles earnings calendar, financial metrics, and fundamental analysis
"""

import os
import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import yfinance as yf

@dataclass
class EarningsEvent:
    """Earnings event data structure"""
    symbol: str
    date: datetime
    estimate: Optional[float] = None
    actual: Optional[float] = None
    surprise_pct: Optional[float] = None

@dataclass
class FinancialMetrics:
    """Financial metrics data structure"""
    symbol: str
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    revenue_growth: Optional[float] = None
    market_cap: Optional[float] = None
    beta: Optional[float] = None

class FundamentalDataProvider:
    """
    Comprehensive fundamental data provider using multiple sources
    Primary: Alpha Vantage, Backup: Yahoo Finance
    """
    
    def __init__(self, alpha_vantage_key: str):
        self.av_key = alpha_vantage_key
        self.base_url = "https://www.alphavantage.co/query"
        self.logger = logging.getLogger('AlgoTradingBot.fundamental')
        
        # Caching
        self.earnings_cache = {}
        self.metrics_cache = {}
        self.cache_expiry = 24 * 3600  # 24 hours
        
        # Data file paths
        os.makedirs('data/fundamental', exist_ok=True)
        self.earnings_file = 'data/fundamental/earnings_calendar.json'
        self.metrics_file = 'data/fundamental/financial_metrics.json'
        
        # Load cached data
        self._load_cached_data()
        
    def _load_cached_data(self):
        """Load cached data from disk"""
        try:
            if os.path.exists(self.earnings_file):
                with open(self.earnings_file, 'r') as f:
                    self.earnings_cache = json.load(f)
                    
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    self.metrics_cache = json.load(f)
                    
            self.logger.info("Loaded cached fundamental data")
        except Exception as e:
            self.logger.error(f"Failed to load cached data: {str(e)}")
            
    def _save_cached_data(self):
        """Save cached data to disk"""
        try:
            with open(self.earnings_file, 'w') as f:
                json.dump(self.earnings_cache, f, default=str, indent=2)
                
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics_cache, f, default=str, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save cached data: {str(e)}")
            
    def _is_cache_valid(self, cache_key: str, cache_dict: dict) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in cache_dict:
            return False
            
        cached_time = cache_dict[cache_key].get('timestamp')
        if not cached_time:
            return False
            
        try:
            if isinstance(cached_time, str):
                cached_time = datetime.fromisoformat(cached_time)
            
            return (datetime.now() - cached_time).total_seconds() < self.cache_expiry
        except:
            return False
            
    def _make_av_request(self, params: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Make Alpha Vantage API request with retry logic"""
        for attempt in range(max_retries):
            try:
                params['apikey'] = self.av_key
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    self.logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return None
                    
                if 'Note' in data:
                    self.logger.warning(f"Alpha Vantage note: {data['Note']}")
                    # Rate limit hit, wait and retry
                    if attempt < max_retries - 1:
                        time.sleep(60)  # Wait 1 minute
                        continue
                    return None
                    
                return data
                
            except requests.RequestException as e:
                self.logger.warning(f"Alpha Vantage request attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
        
    def get_earnings_calendar(self, horizon: str = "3month") -> List[EarningsEvent]:
        """
        Get earnings calendar for the specified horizon
        Args:
            horizon: "3month", "6month", or "12month"
        """
        cache_key = f"earnings_{horizon}"
        
        # Check cache first
        if self._is_cache_valid(cache_key, self.earnings_cache):
            self.logger.debug("Using cached earnings calendar")
            return self._parse_cached_earnings(self.earnings_cache[cache_key]['data'])
            
        # Fetch from Alpha Vantage
        params = {
            'function': 'EARNINGS_CALENDAR',
            'horizon': horizon
        }
        
        data = self._make_av_request(params)
        if not data:
            self.logger.warning("Failed to fetch earnings from Alpha Vantage, using Yahoo Finance backup")
            return self._get_earnings_yahoo_backup()
            
        # Parse and cache data
        earnings_events = self._parse_av_earnings(data)
        
        # Cache the data
        self.earnings_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': [self._earnings_event_to_dict(event) for event in earnings_events]
        }
        self._save_cached_data()
        
        return earnings_events
        
    def _parse_av_earnings(self, data: Dict) -> List[EarningsEvent]:
        """Parse Alpha Vantage earnings data"""
        events = []
        
        try:
            # Alpha Vantage returns CSV-like data
            csv_data = data.get('data', '')
            if not csv_data:
                return events
                
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                return events
                
            headers = lines[0].split(',')
            
            for line in lines[1:]:
                values = line.split(',')
                if len(values) >= 3:
                    try:
                        symbol = values[0].strip()
                        date_str = values[1].strip()
                        
                        # Parse date
                        event_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # Parse estimate if available
                        estimate = None
                        if len(values) > 2 and values[2].strip():
                            try:
                                estimate = float(values[2].strip())
                            except ValueError:
                                pass
                                
                        events.append(EarningsEvent(
                            symbol=symbol,
                            date=event_date,
                            estimate=estimate
                        ))
                        
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Failed to parse earnings line: {line}, error: {str(e)}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to parse Alpha Vantage earnings: {str(e)}")
            
        return events
        
    def _get_earnings_yahoo_backup(self) -> List[EarningsEvent]:
        """Backup earnings data from Yahoo Finance"""
        events = []
        
        try:
            # Get earnings for major symbols (limited data available)
            major_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
            
            for symbol in major_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    calendar = ticker.calendar
                    
                    if calendar is not None and not calendar.empty:
                        # Yahoo Finance calendar has earnings dates
                        for date in calendar.index:
                            events.append(EarningsEvent(
                                symbol=symbol,
                                date=pd.to_datetime(date).to_pydatetime()
                            ))
                            
                except Exception as e:
                    self.logger.debug(f"Failed to get Yahoo earnings for {symbol}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Yahoo Finance backup failed: {str(e)}")
            
        return events
        
    def _parse_cached_earnings(self, cached_data: List[Dict]) -> List[EarningsEvent]:
        """Parse cached earnings data"""
        events = []
        for item in cached_data:
            try:
                events.append(EarningsEvent(
                    symbol=item['symbol'],
                    date=datetime.fromisoformat(item['date']),
                    estimate=item.get('estimate'),
                    actual=item.get('actual'),
                    surprise_pct=item.get('surprise_pct')
                ))
            except Exception as e:
                self.logger.debug(f"Failed to parse cached earnings item: {str(e)}")
                
        return events
        
    def _earnings_event_to_dict(self, event: EarningsEvent) -> Dict:
        """Convert earnings event to dictionary for caching"""
        return {
            'symbol': event.symbol,
            'date': event.date.isoformat(),
            'estimate': event.estimate,
            'actual': event.actual,
            'surprise_pct': event.surprise_pct
        }
        
    def is_earnings_week(self, symbol: str, days_ahead: int = 7) -> bool:
        """
        Check if symbol has earnings in the next N days
        Args:
            symbol: Stock symbol
            days_ahead: Number of days to look ahead (default 7)
        """
        try:
            earnings_events = self.get_earnings_calendar()
            current_date = datetime.now()
            cutoff_date = current_date + timedelta(days=days_ahead)
            
            for event in earnings_events:
                if (event.symbol.upper() == symbol.upper() and 
                    current_date <= event.date <= cutoff_date):
                    self.logger.info(f"Earnings detected for {symbol} on {event.date.strftime('%Y-%m-%d')}")
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check earnings for {symbol}: {str(e)}")
            return False  # Default to no earnings if check fails
            
    def get_financial_metrics(self, symbol: str) -> FinancialMetrics:
        """
        Get comprehensive financial metrics for a symbol
        """
        cache_key = f"metrics_{symbol}"
        
        # Check cache first
        if self._is_cache_valid(cache_key, self.metrics_cache):
            self.logger.debug(f"Using cached metrics for {symbol}")
            return self._parse_cached_metrics(self.metrics_cache[cache_key]['data'])
            
        # Try Alpha Vantage first
        metrics = self._get_av_metrics(symbol)
        
        # Fallback to Yahoo Finance if AV fails
        if not metrics or not metrics.pe_ratio:
            self.logger.debug(f"Using Yahoo Finance for {symbol} metrics")
            metrics = self._get_yahoo_metrics(symbol)
            
        # Cache the data
        if metrics:
            self.metrics_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': self._metrics_to_dict(metrics)
            }
            self._save_cached_data()
            
        return metrics or FinancialMetrics(symbol=symbol)
        
    def _get_av_metrics(self, symbol: str) -> Optional[FinancialMetrics]:
        """Get financial metrics from Alpha Vantage"""
        try:
            # Get overview data
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol
            }
            
            data = self._make_av_request(params)
            if not data:
                return None
                
            # Parse metrics
            def safe_float(value):
                try:
                    return float(value) if value and value != 'None' else None
                except (ValueError, TypeError):
                    return None
                    
            metrics = FinancialMetrics(
                symbol=symbol,
                pe_ratio=safe_float(data.get('PERatio')),
                peg_ratio=safe_float(data.get('PEGRatio')),
                debt_to_equity=safe_float(data.get('DebtToEquityRatio')),
                roe=safe_float(data.get('ReturnOnEquityTTM')),
                revenue_growth=safe_float(data.get('QuarterlyRevenueGrowthYOY')),
                market_cap=safe_float(data.get('MarketCapitalization')),
                beta=safe_float(data.get('Beta'))
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get Alpha Vantage metrics for {symbol}: {str(e)}")
            return None
            
    def _get_yahoo_metrics(self, symbol: str) -> Optional[FinancialMetrics]:
        """Get financial metrics from Yahoo Finance (backup)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Yahoo Finance provides different field names
            metrics = FinancialMetrics(
                symbol=symbol,
                pe_ratio=info.get('trailingPE'),
                peg_ratio=info.get('pegRatio'),
                debt_to_equity=info.get('debtToEquity'),
                roe=info.get('returnOnEquity'),
                revenue_growth=info.get('revenueGrowth'),
                market_cap=info.get('marketCap'),
                beta=info.get('beta')
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get Yahoo metrics for {symbol}: {str(e)}")
            return None
            
    def _parse_cached_metrics(self, cached_data: Dict) -> FinancialMetrics:
        """Parse cached metrics data"""
        return FinancialMetrics(
            symbol=cached_data['symbol'],
            pe_ratio=cached_data.get('pe_ratio'),
            peg_ratio=cached_data.get('peg_ratio'),
            debt_to_equity=cached_data.get('debt_to_equity'),
            roe=cached_data.get('roe'),
            revenue_growth=cached_data.get('revenue_growth'),
            market_cap=cached_data.get('market_cap'),
            beta=cached_data.get('beta')
        )
        
    def _metrics_to_dict(self, metrics: FinancialMetrics) -> Dict:
        """Convert metrics to dictionary for caching"""
        return {
            'symbol': metrics.symbol,
            'pe_ratio': metrics.pe_ratio,
            'peg_ratio': metrics.peg_ratio,
            'debt_to_equity': metrics.debt_to_equity,
            'roe': metrics.roe,
            'revenue_growth': metrics.revenue_growth,
            'market_cap': metrics.market_cap,
            'beta': metrics.beta
        }
        
    def is_fundamentally_strong(self, symbol: str) -> bool:
        """
        Determine if a stock is fundamentally strong based on key metrics
        """
        try:
            metrics = self.get_financial_metrics(symbol)
            
            # Define criteria for fundamental strength
            criteria_met = 0
            total_criteria = 0
            
            # P/E ratio check (reasonable valuation)
            if metrics.pe_ratio is not None:
                total_criteria += 1
                if 5 <= metrics.pe_ratio <= 25:  # Reasonable P/E range
                    criteria_met += 1
                    
            # PEG ratio check (growth at reasonable price)
            if metrics.peg_ratio is not None:
                total_criteria += 1
                if metrics.peg_ratio <= 1.5:  # PEG <= 1.5 indicates good value
                    criteria_met += 1
                    
            # Debt to equity check (not over-leveraged)
            if metrics.debt_to_equity is not None:
                total_criteria += 1
                if metrics.debt_to_equity <= 1.0:  # D/E <= 1.0 is generally healthy
                    criteria_met += 1
                    
            # ROE check (profitable and efficient)
            if metrics.roe is not None:
                total_criteria += 1
                if metrics.roe >= 0.15:  # ROE >= 15% is strong
                    criteria_met += 1
                    
            # Revenue growth check (growing business)
            if metrics.revenue_growth is not None:
                total_criteria += 1
                if metrics.revenue_growth >= 0.05:  # 5%+ revenue growth
                    criteria_met += 1
                    
            # Need at least 3 criteria and 60% pass rate
            if total_criteria >= 3 and criteria_met / total_criteria >= 0.6:
                self.logger.info(f"{symbol} is fundamentally strong ({criteria_met}/{total_criteria} criteria met)")
                return True
            else:
                self.logger.debug(f"{symbol} is not fundamentally strong ({criteria_met}/{total_criteria} criteria met)")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to assess fundamental strength for {symbol}: {str(e)}")
            return True  # Default to allowing trade if check fails
            
    def get_earnings_risk_adjustment(self, symbol: str) -> float:
        """
        Get risk adjustment factor based on proximity to earnings
        Returns: multiplier for position size (0.0 to 1.0)
        """
        try:
            if self.is_earnings_week(symbol, days_ahead=2):
                return 0.0  # No trading within 2 days of earnings
            elif self.is_earnings_week(symbol, days_ahead=7):
                return 0.5  # Half position size within a week
            else:
                return 1.0  # Full position size
                
        except Exception as e:
            self.logger.error(f"Failed to get earnings risk adjustment for {symbol}: {str(e)}")
            return 1.0  # Default to full size if check fails
            
    def refresh_all_data(self):
        """Refresh all cached fundamental data"""
        self.logger.info("Refreshing all fundamental data")
        
        # Clear caches to force refresh
        self.earnings_cache.clear()
        self.metrics_cache.clear()
        
        # Refresh earnings calendar
        self.get_earnings_calendar()
        
        self.logger.info("Fundamental data refresh complete")
        
    def get_cached_data_status(self) -> Dict:
        """Get status of cached data for monitoring"""
        status = {
            'earnings_cache_size': len(self.earnings_cache),
            'metrics_cache_size': len(self.metrics_cache),
            'last_earnings_update': None,
            'last_metrics_update': None
        }
        
        # Find most recent cache entries
        for key, data in self.earnings_cache.items():
            timestamp = data.get('timestamp')
            if timestamp and (not status['last_earnings_update'] or timestamp > status['last_earnings_update']):
                status['last_earnings_update'] = timestamp
                
        for key, data in self.metrics_cache.items():
            timestamp = data.get('timestamp')
            if timestamp and (not status['last_metrics_update'] or timestamp > status['last_metrics_update']):
                status['last_metrics_update'] = timestamp
                
        return status