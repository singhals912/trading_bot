# Quick test script - save as test_apis.py
import os
import requests
from fredapi import Fred
import yfinance as yf

# Test Alpha Vantage
# av_key = os.getenv('ALPHA_VANTAGE_KEY')
# url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={av_key}"
# print("Alpha Vantage:", requests.get(url).status_code)

# # Test NewsAPI  
# news_key = os.getenv('NEWS_API_KEY')
# url = f"https://newsapi.org/v2/everything?q=AAPL&apiKey={news_key}"
# print("NewsAPI:", requests.get(url).status_code)

# Test FRED
# fred = Fred(api_key=os.getenv('FRED_API_KEY'))
# print("FRED:", type(fred.get_series('GDP', limit=1)))

# # Test Yahoo Finance
print("Yahoo Finance:", yf.Ticker('AAPL').fast_info)