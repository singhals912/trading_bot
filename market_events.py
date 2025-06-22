"""
Market Events Manager
Coordinates all event-driven position management and risk adjustments
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    EARNINGS = "earnings"
    FOMC = "fomc"
    ECONOMIC_DATA = "economic_data"
    NEWS_NEGATIVE = "news_negative"
    NEWS_POSITIVE = "news_positive"
    MARKET_STRESS = "market_stress"

class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class MarketEvent:
    """Market event data structure"""
    event_type: EventType
    symbol: Optional[str]
    date: datetime
    description: str
    risk_level: RiskLevel
    risk_adjustment: float  # Multiplier for position size
    duration_hours: int = 24  # How long the event impact lasts

@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    symbol: str
    overall_risk_level: RiskLevel
    position_size_multiplier: float
    should_trade: bool
    risk_factors: List[str]
    active_events: List[MarketEvent]

class MarketEventManager:
    """
    Central coordinator for all market events and risk management
    Integrates fundamental data, economic calendar, and news sentiment
    """
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.logger = logging.getLogger('AlgoTradingBot.events')
        
        # Initialize sub-modules if they exist
        self.fundamental_data = getattr(bot_instance, 'fundamental_data', None)
        self.economic_calendar = getattr(bot_instance, 'economic_calendar', None)
        self.news_analyzer = getattr(bot_instance, 'news_analyzer', None)
        
        # Event tracking
        self.active_events = {}  # symbol -> List[MarketEvent]
        self.global_events = []  # Market-wide events
        
        # Risk thresholds
        self.risk_thresholds = {
            'earnings_days_before': 2,
            'fomc_days_before': 3,
            'negative_news_hours': 4,
            'market_stress_threshold': 'elevated'
        }
        
        # Data file paths
        os.makedirs('data/events', exist_ok=True)
        self.events_file = 'data/events/active_events.json'
        
        # Load active events
        self._load_active_events()
        
    def _load_active_events(self):
        """Load active events from disk"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                    # Parse and validate events (simplified for now)
                    self.logger.info("Loaded active events from disk")
        except Exception as e:
            self.logger.error(f"Failed to load active events: {str(e)}")
            
    def _save_active_events(self):
        """Save active events to disk"""
        try:
            # Convert events to serializable format
            data = {
                'timestamp': datetime.now().isoformat(),
                'active_events': {},
                'global_events': []
            }
            
            with open(self.events_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save active events: {str(e)}")
            
    def assess_symbol_risk(self, symbol: str) -> RiskAssessment:
        """
        Perform comprehensive risk assessment for a symbol
        Integrates all available data sources
        """
        try:
            risk_factors = []
            risk_multipliers = []
            active_events = []
            
            # 1. Earnings Risk Assessment
            if self.fundamental_data:
                try:
                    earnings_adjustment = self.fundamental_data.get_earnings_risk_adjustment(symbol)
                    if earnings_adjustment < 1.0:
                        risk_factors.append(f"Earnings proximity (adjustment: {earnings_adjustment:.1f})")
                        risk_multipliers.append(earnings_adjustment)
                        
                        if earnings_adjustment == 0.0:
                            active_events.append(MarketEvent(
                                event_type=EventType.EARNINGS,
                                symbol=symbol,
                                date=datetime.now() + timedelta(days=1),  # Approximate
                                description="Earnings announcement within 2 days",
                                risk_level=RiskLevel.VERY_HIGH,
                                risk_adjustment=0.0,
                                duration_hours=48
                            ))
                except Exception as e:
                    self.logger.debug(f"Earnings assessment failed for {symbol}: {str(e)}")
                    
            # 2. Economic Calendar Risk Assessment
            if self.economic_calendar:
                try:
                    economic_adjustment = self.economic_calendar.get_economic_risk_adjustment()
                    if economic_adjustment < 1.0:
                        risk_factors.append(f"Economic events (adjustment: {economic_adjustment:.1f})")
                        risk_multipliers.append(economic_adjustment)
                        
                        # Check for FOMC meetings
                        is_fomc, fomc_date = self.economic_calendar.is_fomc_week()
                        if is_fomc:
                            active_events.append(MarketEvent(
                                event_type=EventType.FOMC,
                                symbol=None,  # Market-wide event
                                date=fomc_date,
                                description=f"FOMC meeting on {fomc_date.strftime('%Y-%m-%d')}",
                                risk_level=RiskLevel.HIGH,
                                risk_adjustment=economic_adjustment,
                                duration_hours=72
                            ))
                            
                except Exception as e:
                    self.logger.debug(f"Economic assessment failed: {str(e)}")
                    
            # 3. News Sentiment Risk Assessment
            if self.news_analyzer:
                try:
                    sentiment_adjustment = self.news_analyzer.get_sentiment_based_risk_adjustment(symbol)
                    
                    if sentiment_adjustment < 1.0:
                        risk_factors.append(f"Negative news sentiment (adjustment: {sentiment_adjustment:.1f})")
                        risk_multipliers.append(sentiment_adjustment)
                        
                        if sentiment_adjustment == 0.0:
                            active_events.append(MarketEvent(
                                event_type=EventType.NEWS_NEGATIVE,
                                symbol=symbol,
                                date=datetime.now(),
                                description="Recent negative news detected",
                                risk_level=RiskLevel.VERY_HIGH,
                                risk_adjustment=0.0,
                                duration_hours=6
                            ))
                            
                except Exception as e:
                    self.logger.debug(f"News sentiment assessment failed for {symbol}: {str(e)}")
                    
            # 4. Market Stress Assessment
            if self.economic_calendar:
                try:
                    stress_indicators = self.economic_calendar.get_market_stress_indicators()
                    if stress_indicators.stress_level in ['elevated', 'high']:
                        stress_multiplier = 0.7 if stress_indicators.stress_level == 'elevated' else 0.4
                        risk_factors.append(f"Market stress: {stress_indicators.stress_level}")
                        risk_multipliers.append(stress_multiplier)
                        
                        active_events.append(MarketEvent(
                            event_type=EventType.MARKET_STRESS,
                            symbol=None,
                            date=datetime.now(),
                            description=f"Market stress level: {stress_indicators.stress_level}",
                            risk_level=RiskLevel.ELEVATED if stress_indicators.stress_level == 'elevated' else RiskLevel.HIGH,
                            risk_adjustment=stress_multiplier,
                            duration_hours=24
                        ))
                        
                except Exception as e:
                    self.logger.debug(f"Market stress assessment failed: {str(e)}")
                    
            # 5. Calculate Overall Risk Assessment
            if not risk_multipliers:
                # No risk factors detected
                final_multiplier = 1.0
                overall_risk = RiskLevel.NORMAL
                should_trade = True
            else:
                # Take the most conservative (lowest) multiplier
                final_multiplier = min(risk_multipliers)
                
                # Determine overall risk level
                if final_multiplier == 0.0:
                    overall_risk = RiskLevel.VERY_HIGH
                    should_trade = False
                elif final_multiplier <= 0.3:
                    overall_risk = RiskLevel.HIGH
                    should_trade = True
                elif final_multiplier <= 0.6:
                    overall_risk = RiskLevel.ELEVATED
                    should_trade = True
                elif final_multiplier <= 0.8:
                    overall_risk = RiskLevel.LOW
                    should_trade = True
                else:
                    overall_risk = RiskLevel.NORMAL
                    should_trade = True
                    
            assessment = RiskAssessment(
                symbol=symbol,
                overall_risk_level=overall_risk,
                position_size_multiplier=final_multiplier,
                should_trade=should_trade,
                risk_factors=risk_factors,
                active_events=active_events
            )
            
            # Log significant risk adjustments
            if final_multiplier < 1.0:
                self.logger.info(f"Risk assessment for {symbol}: "
                               f"multiplier={final_multiplier:.2f}, "
                               f"risk_level={overall_risk.value}, "
                               f"factors={len(risk_factors)}")
                               
            return assessment
            
        except Exception as e:
            self.logger.error(f"Risk assessment failed for {symbol}: {str(e)}")
            
            # Return default safe assessment
            return RiskAssessment(
                symbol=symbol,
                overall_risk_level=RiskLevel.NORMAL,
                position_size_multiplier=1.0,
                should_trade=True,
                risk_factors=[],
                active_events=[]
            )
            
    def should_enter_position(self, symbol: str, signal: str) -> Tuple[bool, float, str]:
        """
        Determine if we should enter a position based on all risk factors
        Returns: (should_enter, position_size_multiplier, reason)
        """
        try:
            assessment = self.assess_symbol_risk(symbol)
            
            if not assessment.should_trade:
                return False, 0.0, f"Trading blocked: {', '.join(assessment.risk_factors)}"
                
            if assessment.position_size_multiplier == 0.0:
                return False, 0.0, "Position size reduced to zero due to risk factors"
                
            # Additional checks for buy signals
            if signal == 'buy':
                # Don't buy on recent negative news
                for event in assessment.active_events:
                    if (event.event_type == EventType.NEWS_NEGATIVE and 
                        event.symbol == symbol and
                        (datetime.now() - event.date).total_seconds() < 4 * 3600):  # 4 hours
                        return False, 0.0, "Recent negative news detected"
                        
            # Check market-wide events
            market_stress_adjustment = 1.0
            for event in assessment.active_events:
                if event.symbol is None:  # Market-wide event
                    market_stress_adjustment = min(market_stress_adjustment, event.risk_adjustment)
                    
            final_multiplier = assessment.position_size_multiplier * market_stress_adjustment
            
            if final_multiplier < 0.1:
                return False, 0.0, "Combined risk factors too high"
                
            reason = "Normal trading" if final_multiplier >= 0.9 else f"Reduced size due to: {', '.join(assessment.risk_factors)}"
            
            return True, final_multiplier, reason
            
        except Exception as e:
            self.logger.error(f"Position entry check failed for {symbol}: {str(e)}")
            return True, 1.0, "Error in risk assessment - defaulting to normal"
            
    def should_exit_position(self, symbol: str, current_pnl: float) -> Tuple[bool, str]:
        """
        Determine if we should exit a position based on new events
        Returns: (should_exit, reason)
        """
        try:
            assessment = self.assess_symbol_risk(symbol)
            
            # Exit immediately on very high risk
            if assessment.overall_risk_level == RiskLevel.VERY_HIGH:
                return True, f"Very high risk detected: {', '.join(assessment.risk_factors)}"
                
            # Exit on new negative news if we're profitable
            for event in assessment.active_events:
                if (event.event_type == EventType.NEWS_NEGATIVE and
                    event.symbol == symbol and
                    current_pnl > 0 and
                    (datetime.now() - event.date).total_seconds() < 2 * 3600):  # 2 hours
                    return True, "New negative news - taking profits"
                    
            # Exit before earnings if we're close and profitable
            for event in assessment.active_events:
                if (event.event_type == EventType.EARNINGS and
                    event.symbol == symbol and
                    current_pnl > 0 and
                    (event.date - datetime.now()).total_seconds() < 24 * 3600):  # 24 hours
                    return True, "Earnings approaching - taking profits"
                    
            # Exit on FOMC day if we have significant profits
            for event in assessment.active_events:
                if (event.event_type == EventType.FOMC and
                    current_pnl > 100 and  # More than $100 profit
                    (event.date - datetime.now()).total_seconds() < 12 * 3600):  # 12 hours
                    return True, "FOMC meeting today - securing profits"
                    
            return False, "No exit signal"
            
        except Exception as e:
            self.logger.error(f"Position exit check failed for {symbol}: {str(e)}")
            return False, "Error in exit assessment"
            
    def get_pre_market_risk_adjustment(self, symbol: str) -> float:
        """
        Get risk adjustment specifically for pre-market trading
        """
        try:
            assessment = self.assess_symbol_risk(symbol)
            
            # Pre-market is inherently riskier, so apply additional reduction
            base_multiplier = assessment.position_size_multiplier * 0.5  # 50% reduction for pre-market
            
            # Additional reductions for specific events
            for event in assessment.active_events:
                if event.event_type == EventType.EARNINGS:
                    base_multiplier *= 0.3  # Severe reduction before earnings
                elif event.event_type == EventType.NEWS_NEGATIVE:
                    base_multiplier = 0.0  # No pre-market trading on negative news
                    
            return base_multiplier
            
        except Exception as e:
            self.logger.error(f"Pre-market risk assessment failed for {symbol}: {str(e)}")
            return 0.5  # Default to 50% reduction
            
    def get_market_regime_assessment(self) -> Dict:
        """
        Get overall market regime assessment
        """
        try:
            assessment = {
                'timestamp': datetime.now().isoformat(),
                'overall_risk_level': 'normal',
                'recommended_max_positions': 3,
                'recommended_risk_per_trade': 0.02,
                'market_conditions': [],
                'active_global_events': []
            }
            
            risk_adjustments = []
            
            # Check economic conditions
            if self.economic_calendar:
                stress = self.economic_calendar.get_market_stress_indicators()
                is_fomc, fomc_date = self.economic_calendar.is_fomc_week()
                
                if stress.stress_level in ['elevated', 'high']:
                    risk_adjustments.append(0.7 if stress.stress_level == 'elevated' else 0.4)
                    assessment['market_conditions'].append(f"Market stress: {stress.stress_level}")
                    
                if is_fomc:
                    risk_adjustments.append(0.6)
                    assessment['market_conditions'].append(f"FOMC meeting: {fomc_date.strftime('%Y-%m-%d')}")
                    assessment['active_global_events'].append({
                        'type': 'FOMC',
                        'date': fomc_date.strftime('%Y-%m-%d'),
                        'impact': 'high_volatility'
                    })
                    
            # Check market sentiment
            if self.news_analyzer:
                market_sentiment = self.news_analyzer.get_market_sentiment()
                if market_sentiment['sentiment_label'] == 'negative':
                    risk_adjustments.append(0.8)
                    assessment['market_conditions'].append("Negative market sentiment")
                    
            # Determine overall assessment
            if risk_adjustments:
                min_adjustment = min(risk_adjustments)
                if min_adjustment <= 0.4:
                    assessment['overall_risk_level'] = 'high'
                    assessment['recommended_max_positions'] = 1
                    assessment['recommended_risk_per_trade'] = 0.01
                elif min_adjustment <= 0.7:
                    assessment['overall_risk_level'] = 'elevated'
                    assessment['recommended_max_positions'] = 2
                    assessment['recommended_risk_per_trade'] = 0.015
                    
            return assessment
            
        except Exception as e:
            self.logger.error(f"Market regime assessment failed: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_risk_level': 'normal',
                'error': str(e)
            }
            
    def cleanup_expired_events(self):
        """Remove expired events from tracking"""
        try:
            current_time = datetime.now()
            
            # Clean up symbol-specific events
            for symbol in list(self.active_events.keys()):
                self.active_events[symbol] = [
                    event for event in self.active_events[symbol]
                    if (current_time - event.date).total_seconds() < event.duration_hours * 3600
                ]
                
                if not self.active_events[symbol]:
                    del self.active_events[symbol]
                    
            # Clean up global events
            self.global_events = [
                event for event in self.global_events
                if (current_time - event.date).total_seconds() < event.duration_hours * 3600
            ]
            
            self._save_active_events()
            
        except Exception as e:
            self.logger.error(f"Event cleanup failed: {str(e)}")
            
    def get_events_summary(self) -> Dict:
        """Get summary of all active events for monitoring"""
        try:
            self.cleanup_expired_events()
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_active_events': len(self.global_events),
                'symbols_with_events': list(self.active_events.keys()),
                'global_events': [],
                'symbol_events': {},
                'market_regime': self.get_market_regime_assessment()
            }
            
            # Add global events
            for event in self.global_events:
                summary['global_events'].append({
                    'type': event.event_type.value,
                    'description': event.description,
                    'risk_level': event.risk_level.value,
                    'expires_in_hours': event.duration_hours - ((datetime.now() - event.date).total_seconds() / 3600)
                })
                
            # Add symbol-specific events
            for symbol, events in self.active_events.items():
                summary['symbol_events'][symbol] = []
                for event in events:
                    summary['symbol_events'][symbol].append({
                        'type': event.event_type.value,
                        'description': event.description,
                        'risk_level': event.risk_level.value,
                        'risk_adjustment': event.risk_adjustment,
                        'expires_in_hours': event.duration_hours - ((datetime.now() - event.date).total_seconds() / 3600)
                    })
                    
            return summary
            
        except Exception as e:
            self.logger.error(f"Events summary failed: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }