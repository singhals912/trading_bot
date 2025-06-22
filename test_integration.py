import os
from fundamental_data import FundamentalDataProvider
from economic_calendar import EconomicCalendar  
from news_sentiment import NewsSentimentAnalyzer
from market_events import MarketEventManager

def test_integration():
    print("Testing Phase 1 integration...")
    
    # Test fundamental data
    if os.getenv('ALPHA_VANTAGE_KEY'):
        fundamental = FundamentalDataProvider(os.getenv('ALPHA_VANTAGE_KEY'))
        earnings_risk = fundamental.get_earnings_risk_adjustment('AAPL')
        print(f"✅ Fundamental data: AAPL earnings risk = {earnings_risk}")
    else:
        print("❌ Alpha Vantage key missing")
        
    # Test economic calendar
    if os.getenv('FRED_API_KEY'):
        economic = EconomicCalendar(os.getenv('FRED_API_KEY'))
        is_fomc, date = economic.is_fomc_week()
        print(f"✅ Economic calendar: FOMC this week = {is_fomc}")
    else:
        print("❌ FRED API key missing")
        
    # Test news sentiment
    if os.getenv('NEWS_API_KEY'):
        news = NewsSentimentAnalyzer(os.getenv('NEWS_API_KEY'))
        has_negative = news.has_negative_news('AAPL', hours_back=24)
        print(f"✅ News sentiment: AAPL negative news = {has_negative}")
    else:
        print("❌ News API key missing")
        
    print("Integration test complete!")

if __name__ == "__main__":
    test_integration()