"""
Economic Calendar and FOMC Meeting Awareness
Handles economic events, interest rates, and market stress indicators
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
from fredapi import Fred

@dataclass
class EconomicEvent:
    """Economic event data structure"""
    event_name: str
    date: datetime
    importance: str  # 'high', 'medium', 'low'
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    impact: Optional[str] = None  # 'bullish', 'bearish', 'neutral'

@dataclass
class MarketStressIndicators:
    """Market stress indicators data structure"""
    vix: Optional[float] = None
    yield_10y: Optional[float] = None
    yield_2y: Optional[float] = None
    yield_curve_spread: Optional[float] = None
    dxy: Optional[float] = None  # Dollar index
    unemployment_rate: Optional[float] = None
    inflation_rate: Optional[float] = None
    stress_level: str = 'normal'  # 'low', 'normal', 'elevated', 'high'

class EconomicCalendar:
    """
    Economic calendar and FOMC meeting awareness system
    Uses FRED API for economic data and maintains FOMC meeting schedule
    """
    
    def __init__(self, fred_api_key: str):
        self.fred = Fred(api_key=fred_api_key)
        self.logger = logging.getLogger('AlgoTradingBot.economic')
        
        # Caching
        self.events_cache = {}
        self.indicators_cache = {}
        self.cache_expiry = 12 * 3600  # 12 hours for economic data
        
        # Data file paths
        os.makedirs('data/economic', exist_ok=True)
        self.events_file = 'data/economic/economic_events.json'
        self.indicators_file = 'data/economic/market_indicators.json'
        
        # FOMC meeting dates for 2025 (update annually)
        self.fomc_dates_2025 = [
            datetime(2025, 1, 29),  # January 28-29
            datetime(2025, 3, 19),  # March 18-19
            datetime(2025, 5, 1),   # April 30 - May 1
            datetime(2025, 6, 18),  # June 17-18
            datetime(2025, 7, 30),  # July 29-30
            datetime(2025, 9, 17),  # September 16-17
            datetime(2025, 11, 6),  # November 5-6
            datetime(2025, 12, 17)  # December 16-17
        ]
        
        # Load cached data
        self._load_cached_data()
        
    def _load_cached_data(self):
        """Load cached data from disk"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    self.events_cache = json.load(f)
                    
            if os.path.exists(self.indicators_file):
                with open(self.indicators_file, 'r') as f:
                    self.indicators_cache = json.load(f)
                    
            self.logger.info("Loaded cached economic data")
        except Exception as e:
            self.logger.error(f"Failed to load cached economic data: {str(e)}")
            
    def _save_cached_data(self):
        """Save cached data to disk"""
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.events_cache, f, default=str, indent=2)
                
            with open(self.indicators_file, 'w') as f:
                json.dump(self.indicators_cache, f, default=str, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save cached economic data: {str(e)}")
            
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
            
    def _fetch_fred_data(self, series_id: str, limit: int = 1) -> Optional[float]:
        """Fetch data from FRED with error handling"""
        try:
            data = self.fred.get_series(series_id, limit=limit)
            if not data.empty:
                return float(data.iloc[-1])
        except Exception as e:
            self.logger.debug(f"Failed to fetch FRED series {series_id}: {str(e)}")
        return None
        
    def is_fomc_week(self, days_ahead: int = 7) -> Tuple[bool, Optional[datetime]]:
        """
        Check if FOMC meeting is within the next N days
        Returns: (is_fomc_week, meeting_date)
        """
        try:
            current_date = datetime.now()
            cutoff_date = current_date + timedelta(days=days_ahead)
            
            for meeting_date in self.fomc_dates_2025:
                if current_date <= meeting_date <= cutoff_date:
                    days_until = (meeting_date - current_date).days
                    self.logger.info(f"FOMC meeting detected in {days_until} days on {meeting_date.strftime('%Y-%m-%d')}")
                    return True, meeting_date
                    
            return False, None
            
        except Exception as e:
            self.logger.error(f"Failed to check FOMC schedule: {str(e)}")
            return False, None
            
    def get_fomc_risk_adjustment(self) -> float:
        """
        Get risk adjustment factor based on proximity to FOMC meeting
        Returns: multiplier for position size (0.2 to 1.0)
        """
        try:
            is_fomc_week, meeting_date = self.is_fomc_week(days_ahead=7)
            
            if not is_fomc_week:
                return 1.0  # Full position size
                
            days_until = (meeting_date - datetime.now()).days
            
            if days_until <= 1:
                return 0.2  # 20% position size day of/before meeting
            elif days_until <= 3:
                return 0.4  # 40% position size 2-3 days before
            else:
                return 0.6  # 60% position size week of meeting
                
        except Exception as e:
            self.logger.error(f"Failed to get FOMC risk adjustment: {str(e)}")
            return 1.0  # Default to full size if check fails
            
    def get_high_impact_events(self, days_ahead: int = 7) -> List[EconomicEvent]:
        """
        Get high-impact economic events for the next N days
        """
        cache_key = f"events_{days_ahead}d"
        
        # Check cache first
        if self._is_cache_valid(cache_key, self.events_cache):
            self.logger.debug("Using cached economic events")
            return self._parse_cached_events(self.events_cache[cache_key]['data'])
            
        events = []
        current_date = datetime.now()
        
        # Define high-impact economic events and their typical release patterns
        high_impact_indicators = {
            'UNRATE': {  # Unemployment Rate
                'name': 'Unemployment Rate',
                'frequency': 'monthly',
                'release_day': 'first_friday',
                'importance': 'high'
            },
            'CPIAUCSL': {  # Consumer Price Index
                'name': 'CPI (Inflation)',
                'frequency': 'monthly', 
                'release_day': 'mid_month',
                'importance': 'high'
            },
            'GDP': {  # GDP
                'name': 'GDP Growth',
                'frequency': 'quarterly',
                'release_day': 'end_month',
                'importance': 'high'
            },
            'PAYEMS': {  # Non-farm Payrolls
                'name': 'Non-farm Payrolls',
                'frequency': 'monthly',
                'release_day': 'first_friday', 
                'importance': 'high'
            }
        }
        
        # Check for upcoming FOMC meetings
        is_fomc, meeting_date = self.is_fomc_week(days_ahead)
        if is_fomc:
            events.append(EconomicEvent(
                event_name="FOMC Meeting",
                date=meeting_date,
                importance="high",
                impact="high_volatility"
            ))
            
        # Add other high-impact events (simplified schedule)
        # In production, you'd integrate with a proper economic calendar API
        
        # Cache the events
        self.events_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': [self._event_to_dict(event) for event in events]
        }
        self._save_cached_data()
        
        return events
        
    def get_market_stress_indicators(self) -> MarketStressIndicators:
        """
        Get comprehensive market stress indicators
        """
        cache_key = "market_stress"
        
        # Check cache first
        if self._is_cache_valid(cache_key, self.indicators_cache):
            self.logger.debug("Using cached market stress indicators")
            return self._parse_cached_indicators(self.indicators_cache[cache_key]['data'])
            
        indicators = MarketStressIndicators()
        
        try:
            # Fetch key indicators from FRED
            indicators.yield_10y = self._fetch_fred_data('GS10')  # 10-Year Treasury
            indicators.yield_2y = self._fetch_fred_data('GS2')   # 2-Year Treasury
            indicators.unemployment_rate = self._fetch_fred_data('UNRATE')
            indicators.dxy = self._fetch_fred_data('DEXUSEU')  # USD/EUR exchange rate
            
            # Calculate yield curve spread
            if indicators.yield_10y and indicators.yield_2y:
                indicators.yield_curve_spread = indicators.yield_10y - indicators.yield_2y
                
            # Get recent CPI for inflation
            indicators.inflation_rate = self._fetch_fred_data('CPIAUCSL')
            
            # Determine stress level
            indicators.stress_level = self._calculate_stress_level(indicators)
            
            # Cache the indicators
            self.indicators_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': self._indicators_to_dict(indicators)
            }
            self._save_cached_data()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch market stress indicators: {str(e)}")
            
        return indicators
        
    def _calculate_stress_level(self, indicators: MarketStressIndicators) -> str:
        """Calculate overall market stress level"""
        stress_factors = 0
        total_factors = 0
        
        # Yield curve inversion (strong recession indicator)
        if indicators.yield_curve_spread is not None:
            total_factors += 1
            if indicators.yield_curve_spread < 0:
                stress_factors += 2  # Inverted curve is very concerning
            elif indicators.yield_curve_spread < 0.5:
                stress_factors += 1  # Flattening curve
                
        # High unemployment
        if indicators.unemployment_rate is not None:
            total_factors += 1
            if indicators.unemployment_rate > 6.0:
                stress_factors += 1
                
        # Check for FOMC meeting proximity
        is_fomc, _ = self.is_fomc_week(days_ahead=3)
        if is_fomc:
            stress_factors += 1
            total_factors += 1
            
        # Determine stress level
        if total_factors == 0:
            return 'normal'
            
        stress_ratio = stress_factors / total_factors
        
        if stress_ratio >= 0.7:
            return 'high'
        elif stress_ratio >= 0.4:
            return 'elevated'
        elif stress_ratio >= 0.2:
            return 'normal'
        else:
            return 'low'
            
    def get_economic_risk_adjustment(self) -> float:
        """
        Get overall economic risk adjustment factor
        Combines FOMC proximity and market stress
        """
        try:
            # Get FOMC adjustment
            fomc_adjustment = self.get_fomc_risk_adjustment()
            
            # Get market stress adjustment
            stress_indicators = self.get_market_stress_indicators()
            stress_adjustment = {
                'low': 1.2,      # Slightly increase risk in low stress
                'normal': 1.0,   # Normal risk
                'elevated': 0.7, # Reduce risk
                'high': 0.3      # Significantly reduce risk
            }.get(stress_indicators.stress_level, 1.0)
            
            # Take the more conservative adjustment
            final_adjustment = min(fomc_adjustment, stress_adjustment)
            
            if final_adjustment < 1.0:
                self.logger.info(f"Economic risk adjustment: {final_adjustment:.2f} "
                               f"(FOMC: {fomc_adjustment:.2f}, Stress: {stress_adjustment:.2f})")
                
            return final_adjustment
            
        except Exception as e:
            self.logger.error(f"Failed to calculate economic risk adjustment: {str(e)}")
            return 1.0
            
    def is_high_volatility_period(self) -> bool:
        """
        Check if we're in a high volatility period based on economic factors
        """
        try:
            # Check FOMC proximity
            is_fomc, meeting_date = self.is_fomc_week(days_ahead=2)
            if is_fomc:
                return True
                
            # Check market stress
            stress = self.get_market_stress_indicators()
            if stress.stress_level in ['elevated', 'high']:
                return True
                
            # Check yield curve inversion
            if stress.yield_curve_spread is not None and stress.yield_curve_spread < 0:
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check volatility period: {str(e)}")
            return False
            
    def get_interest_rate_trend(self) -> Dict[str, any]:
        """
        Analyze interest rate trends for market context
        """
        try:
            # Get recent 10-year and 2-year yields
            ten_year_data = self.fred.get_series('GS10', limit=30)  # Last 30 data points
            two_year_data = self.fred.get_series('GS2', limit=30)
            
            if ten_year_data.empty or two_year_data.empty:
                return {'trend': 'unknown', 'spread': None}
                
            # Calculate trends
            ten_year_trend = 'rising' if ten_year_data.iloc[-1] > ten_year_data.iloc[-10] else 'falling'
            spread_current = ten_year_data.iloc[-1] - two_year_data.iloc[-1]
            spread_past = ten_year_data.iloc[-10] - two_year_data.iloc[-10]
            
            return {
                'ten_year_trend': ten_year_trend,
                'current_spread': spread_current,
                'spread_trend': 'widening' if spread_current > spread_past else 'narrowing',
                'is_inverted': spread_current < 0,
                'current_10y': ten_year_data.iloc[-1],
                'current_2y': two_year_data.iloc[-1]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze interest rate trends: {str(e)}")
            return {'trend': 'unknown', 'spread': None}
            
    def _parse_cached_events(self, cached_data: List[Dict]) -> List[EconomicEvent]:
        """Parse cached economic events"""
        events = []
        for item in cached_data:
            try:
                events.append(EconomicEvent(
                    event_name=item['event_name'],
                    date=datetime.fromisoformat(item['date']),
                    importance=item['importance'],
                    actual=item.get('actual'),
                    forecast=item.get('forecast'),
                    previous=item.get('previous'),
                    impact=item.get('impact')
                ))
            except Exception as e:
                self.logger.debug(f"Failed to parse cached event: {str(e)}")
                
        return events
        
    def _parse_cached_indicators(self, cached_data: Dict) -> MarketStressIndicators:
        """Parse cached market stress indicators"""
        return MarketStressIndicators(
            vix=cached_data.get('vix'),
            yield_10y=cached_data.get('yield_10y'),
            yield_2y=cached_data.get('yield_2y'),
            yield_curve_spread=cached_data.get('yield_curve_spread'),
            dxy=cached_data.get('dxy'),
            unemployment_rate=cached_data.get('unemployment_rate'),
            inflation_rate=cached_data.get('inflation_rate'),
            stress_level=cached_data.get('stress_level', 'normal')
        )
        
    def _event_to_dict(self, event: EconomicEvent) -> Dict:
        """Convert economic event to dictionary for caching"""
        return {
            'event_name': event.event_name,
            'date': event.date.isoformat(),
            'importance': event.importance,
            'actual': event.actual,
            'forecast': event.forecast,
            'previous': event.previous,
            'impact': event.impact
        }
        
    def _indicators_to_dict(self, indicators: MarketStressIndicators) -> Dict:
        """Convert indicators to dictionary for caching"""
        return {
            'vix': indicators.vix,
            'yield_10y': indicators.yield_10y,
            'yield_2y': indicators.yield_2y,
            'yield_curve_spread': indicators.yield_curve_spread,
            'dxy': indicators.dxy,
            'unemployment_rate': indicators.unemployment_rate,
            'inflation_rate': indicators.inflation_rate,
            'stress_level': indicators.stress_level
        }
        
    def refresh_all_data(self):
        """Refresh all cached economic data"""
        self.logger.info("Refreshing all economic data")
        
        # Clear caches to force refresh
        self.events_cache.clear()
        self.indicators_cache.clear()
        
        # Refresh data
        self.get_high_impact_events()
        self.get_market_stress_indicators()
        
        self.logger.info("Economic data refresh complete")
        
    def get_daily_economic_summary(self) -> Dict:
        """Get daily economic summary for monitoring"""
        try:
            is_fomc, fomc_date = self.is_fomc_week()
            stress = self.get_market_stress_indicators()
            events = self.get_high_impact_events()
            rates = self.get_interest_rate_trend()
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'fomc_meeting_this_week': is_fomc,
                'fomc_date': fomc_date.strftime('%Y-%m-%d') if fomc_date else None,
                'market_stress_level': stress.stress_level,
                'yield_curve_inverted': stress.yield_curve_spread < 0 if stress.yield_curve_spread else False,
                'upcoming_events_count': len(events),
                'risk_adjustment_factor': self.get_economic_risk_adjustment(),
                'interest_rate_trend': rates.get('ten_year_trend', 'unknown'),
                'current_10y_yield': rates.get('current_10y'),
                'yield_spread': stress.yield_curve_spread
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate economic summary: {str(e)}")
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'error': str(e)
            }