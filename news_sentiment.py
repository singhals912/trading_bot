"""
News Sentiment Analysis
Real-time news monitoring and sentiment analysis for individual stocks and market
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import re
from collections import defaultdict

# NLP libraries with fallbacks
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
    
    # Download required NLTK data if not present
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon')
        
except ImportError:
    NLTK_AVAILABLE = False

@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    description: str
    source: str
    published_at: datetime
    url: str
    symbol: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    relevance_score: Optional[float] = None

@dataclass
class SentimentAnalysis:
    """Sentiment analysis results"""
    symbol: str
    overall_sentiment: float  # -1 (very negative) to +1 (very positive)
    sentiment_label: str      # 'very_negative', 'negative', 'neutral', 'positive', 'very_positive'
    article_count: int
    confidence: float         # 0 to 1
    recent_negative_news: bool
    major_news_detected: bool

class NewsSentimentAnalyzer:
    """
    Real-time news sentiment analysis using NewsAPI and multiple sentiment engines
    """
    
    def __init__(self, news_api_key: str):
        self.news_api_key = news_api_key
        self.base_url = "https://newsapi.org/v2"
        self.logger = logging.getLogger('AlgoTradingBot.news')
        
        # Initialize sentiment analyzers
        self.vader_analyzer = SentimentIntensityAnalyzer() if NLTK_AVAILABLE else None
        
        # Caching
        self.news_cache = {}
        self.sentiment_cache = {}
        self.cache_expiry = 3600  # 1 hour for news
        
        # Data file paths
        os.makedirs('data/news', exist_ok=True)
        self.news_file = 'data/news/news_cache.json'
        self.sentiment_file = 'data/news/sentiment_cache.json'
        
        # Company name mappings for better symbol detection
        self.company_names = {
            'AAPL': ['Apple', 'Apple Inc', 'iPhone', 'iPad', 'Mac'],
            'MSFT': ['Microsoft', 'Microsoft Corp', 'Windows', 'Azure', 'Office'],
            'GOOGL': ['Google', 'Alphabet', 'YouTube', 'Android', 'Chrome'],
            'AMZN': ['Amazon', 'Amazon.com', 'AWS', 'Prime', 'Alexa'],
            'TSLA': ['Tesla', 'Tesla Inc', 'Elon Musk', 'Model S', 'Model 3', 'Model Y'],
            'META': ['Meta', 'Facebook', 'Instagram', 'WhatsApp', 'Metaverse'],
            'NVDA': ['NVIDIA', 'Nvidia Corp', 'GPU', 'AI chips'],
            'JPM': ['JPMorgan', 'JP Morgan', 'Chase'],
            'JNJ': ['Johnson & Johnson', 'J&J'],
            'V': ['Visa Inc', 'Visa Corp'],
            'PG': ['Procter & Gamble', 'P&G'],
            'UNH': ['UnitedHealth', 'United Health'],
            'HD': ['Home Depot'],
            'MA': ['Mastercard'],
            'DIS': ['Disney', 'Walt Disney']
        }
        
        # Negative keywords that indicate potentially bad news
        self.negative_keywords = [
            'lawsuit', 'sued', 'investigation', 'probe', 'scandal', 'fraud',
            'hack', 'breach', 'cyberattack', 'data breach', 'privacy violation',
            'recall', 'defect', 'safety issue', 'warning', 'alert',
            'bankruptcy', 'debt', 'loss', 'decline', 'drop', 'plunge', 'crash',
            'layoffs', 'fired', 'terminated', 'cuts', 'downsizing',
            'regulatory action', 'fine', 'penalty', 'violation', 'compliance',
            'disappointed', 'missed', 'below expectations', 'weak', 'poor'
        ]
        
        # Positive keywords
        self.positive_keywords = [
            'breakthrough', 'innovation', 'award', 'recognition', 'achievement',
            'partnership', 'deal', 'agreement', 'acquisition', 'merger',
            'growth', 'expansion', 'increase', 'rise', 'surge', 'boom',
            'profit', 'revenue', 'earnings beat', 'exceeded', 'outperform',
            'launch', 'new product', 'upgrade', 'improvement', 'success',
            'bullish', 'optimistic', 'positive', 'strong', 'robust'
        ]
        
        # Load cached data
        self._load_cached_data()
        
    def _load_cached_data(self):
        """Load cached data from disk"""
        try:
            if os.path.exists(self.news_file):
                with open(self.news_file, 'r') as f:
                    self.news_cache = json.load(f)
                    
            if os.path.exists(self.sentiment_file):
                with open(self.sentiment_file, 'r') as f:
                    self.sentiment_cache = json.load(f)
                    
            self.logger.info("Loaded cached news data")
        except Exception as e:
            self.logger.error(f"Failed to load cached news data: {str(e)}")
            
    def _save_cached_data(self):
        """Save cached data to disk"""
        try:
            with open(self.news_file, 'w') as f:
                json.dump(self.news_cache, f, default=str, indent=2)
                
            with open(self.sentiment_file, 'w') as f:
                json.dump(self.sentiment_cache, f, default=str, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save cached news data: {str(e)}")
            
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
            
    def _make_news_request(self, endpoint: str, params: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Make NewsAPI request with retry logic"""
        for attempt in range(max_retries):
            try:
                params['apiKey'] = self.news_api_key
                response = requests.get(f"{self.base_url}/{endpoint}", params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if data.get('status') == 'error':
                    self.logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                    return None
                    
                return data
                
            except requests.RequestException as e:
                self.logger.warning(f"NewsAPI request attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
        
    def _extract_symbol_from_text(self, text: str) -> List[str]:
        """Extract stock symbols from news text"""
        symbols = []
        
        # Check company name mappings
        text_lower = text.lower()
        for symbol, names in self.company_names.items():
            for name in names:
                if name.lower() in text_lower:
                    symbols.append(symbol)
                    break
                    
        # Remove duplicates and return
        return list(set(symbols))
        
    def _calculate_keyword_sentiment(self, text: str) -> float:
        """Calculate sentiment based on positive/negative keywords"""
        text_lower = text.lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0.0
            
        return (positive_count - negative_count) / total_count
        
    def _analyze_sentiment(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment using multiple methods
        Returns: (sentiment_score, confidence)
        """
        sentiments = []
        
        # Method 1: VADER sentiment (if available)
        if self.vader_analyzer:
            try:
                vader_scores = self.vader_analyzer.polarity_scores(text)
                vader_sentiment = vader_scores['compound']
                sentiments.append(vader_sentiment)
            except Exception as e:
                self.logger.debug(f"VADER sentiment failed: {str(e)}")
                
        # Method 2: TextBlob sentiment (if available)
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                textblob_sentiment = blob.sentiment.polarity
                sentiments.append(textblob_sentiment)
            except Exception as e:
                self.logger.debug(f"TextBlob sentiment failed: {str(e)}")
                
        # Method 3: Keyword-based sentiment (always available)
        keyword_sentiment = self._calculate_keyword_sentiment(text)
        sentiments.append(keyword_sentiment)
        
        if not sentiments:
            return 0.0, 0.0
            
        # Calculate average sentiment and confidence
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Confidence based on agreement between methods
        if len(sentiments) > 1:
            variance = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments)
            confidence = max(0.1, 1.0 - variance)  # Lower variance = higher confidence
        else:
            confidence = 0.5  # Medium confidence for single method
            
        return avg_sentiment, confidence
        
    def _get_news_for_symbol(self, symbol: str, hours_back: int = 24) -> List[NewsArticle]:
        """Get news articles for a specific symbol"""
        cache_key = f"{symbol}_{hours_back}h"
        
        # Check cache first
        if self._is_cache_valid(cache_key, self.news_cache):
            self.logger.debug(f"Using cached news for {symbol}")
            return self._parse_cached_news(self.news_cache[cache_key]['data'])
            
        articles = []
        
        # Search terms for the symbol
        search_terms = [symbol]
        if symbol in self.company_names:
            search_terms.extend(self.company_names[symbol][:2])  # Add top 2 company names
            
        # Calculate date range
        from_date = datetime.now() - timedelta(hours=hours_back)
        
        for search_term in search_terms:
            try:
                params = {
                    'q': search_term,
                    'from': from_date.strftime('%Y-%m-%d'),
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'pageSize': 20
                }
                
                data = self._make_news_request('everything', params)
                if not data or 'articles' not in data:
                    continue
                    
                for article_data in data['articles']:
                    try:
                        # Parse article
                        article = NewsArticle(
                            title=article_data.get('title', ''),
                            description=article_data.get('description', ''),
                            source=article_data.get('source', {}).get('name', 'Unknown'),
                            published_at=datetime.strptime(
                                article_data['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'
                            ),
                            url=article_data.get('url', ''),
                            symbol=symbol
                        )
                        
                        # Calculate relevance score
                        text = f"{article.title} {article.description}".lower()
                        relevance = 0
                        
                        # Check if symbol/company mentioned
                        for term in search_terms:
                            if term.lower() in text:
                                relevance += 0.3
                                
                        # Boost relevance for financial sources
                        financial_sources = ['reuters', 'bloomberg', 'cnbc', 'marketwatch', 'yahoo finance']
                        if any(source in article.source.lower() for source in financial_sources):
                            relevance += 0.2
                            
                        article.relevance_score = min(1.0, relevance)
                        
                        # Analyze sentiment
                        combined_text = f"{article.title} {article.description}"
                        sentiment_score, confidence = self._analyze_sentiment(combined_text)
                        article.sentiment_score = sentiment_score
                        
                        # Only keep relevant articles
                        if article.relevance_score >= 0.3:
                            articles.append(article)
                            
                    except Exception as e:
                        self.logger.debug(f"Failed to parse article: {str(e)}")
                        continue
                        
                # Rate limiting - NewsAPI allows 1000 requests/day
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Failed to fetch news for {search_term}: {str(e)}")
                continue
                
        # Remove duplicates based on URL
        unique_articles = {}
        for article in articles:
            if article.url not in unique_articles:
                unique_articles[article.url] = article
                
        final_articles = list(unique_articles.values())
        
        # Cache the articles
        self.news_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': [self._article_to_dict(article) for article in final_articles]
        }
        self._save_cached_data()
        
        return final_articles
        
    def get_stock_sentiment(self, symbol: str, hours_back: int = 24) -> SentimentAnalysis:
        """
        Get comprehensive sentiment analysis for a specific stock
        """
        cache_key = f"sentiment_{symbol}_{hours_back}h"
        
        # Check cache first
        if self._is_cache_valid(cache_key, self.sentiment_cache):
            self.logger.debug(f"Using cached sentiment for {symbol}")
            return self._parse_cached_sentiment(self.sentiment_cache[cache_key]['data'])
            
        try:
            # Get news articles
            articles = self._get_news_for_symbol(symbol, hours_back)
            
            if not articles:
                # No news found
                sentiment = SentimentAnalysis(
                    symbol=symbol,
                    overall_sentiment=0.0,
                    sentiment_label='neutral',
                    article_count=0,
                    confidence=0.0,
                    recent_negative_news=False,
                    major_news_detected=False
                )
            else:
                # Calculate weighted sentiment
                total_weight = 0
                weighted_sentiment = 0
                recent_negative = False
                major_news = False
                
                for article in articles:
                    # Weight by relevance and recency
                    age_hours = (datetime.now() - article.published_at).total_seconds() / 3600
                    recency_weight = max(0.1, 1.0 - (age_hours / hours_back))
                    weight = article.relevance_score * recency_weight
                    
                    weighted_sentiment += article.sentiment_score * weight
                    total_weight += weight
                    
                    # Check for recent negative news (last 4 hours)
                    if age_hours <= 4 and article.sentiment_score < -0.3:
                        recent_negative = True
                        
                    # Check for major news (high relevance + strong sentiment)
                    if article.relevance_score > 0.7 and abs(article.sentiment_score) > 0.5:
                        major_news = True
                        
                # Calculate final sentiment
                overall_sentiment = weighted_sentiment / total_weight if total_weight > 0 else 0.0
                
                # Determine sentiment label
                if overall_sentiment >= 0.6:
                    sentiment_label = 'very_positive'
                elif overall_sentiment >= 0.2:
                    sentiment_label = 'positive'
                elif overall_sentiment >= -0.2:
                    sentiment_label = 'neutral'
                elif overall_sentiment >= -0.6:
                    sentiment_label = 'negative'
                else:
                    sentiment_label = 'very_negative'
                    
                # Calculate confidence based on article count and agreement
                confidence = min(1.0, len(articles) / 5.0)  # More articles = higher confidence
                
                sentiment = SentimentAnalysis(
                    symbol=symbol,
                    overall_sentiment=overall_sentiment,
                    sentiment_label=sentiment_label,
                    article_count=len(articles),
                    confidence=confidence,
                    recent_negative_news=recent_negative,
                    major_news_detected=major_news
                )
                
            # Cache the sentiment
            self.sentiment_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': self._sentiment_to_dict(sentiment)
            }
            self._save_cached_data()
            
            return sentiment
            
        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment for {symbol}: {str(e)}")
            return SentimentAnalysis(
                symbol=symbol,
                overall_sentiment=0.0,
                sentiment_label='neutral',
                article_count=0,
                confidence=0.0,
                recent_negative_news=False,
                major_news_detected=False
            )
            
    def has_negative_news(self, symbol: str, hours_back: int = 2, threshold: float = -0.3) -> bool:
        """
        Check if there's significant negative news for a symbol in recent hours
        """
        try:
            sentiment = self.get_stock_sentiment(symbol, hours_back)
            
            # Check multiple criteria for negative news
            criteria = [
                sentiment.recent_negative_news,
                sentiment.overall_sentiment < threshold,
                sentiment.sentiment_label in ['negative', 'very_negative'] and sentiment.confidence > 0.3
            ]
            
            has_negative = any(criteria)
            
            if has_negative:
                self.logger.info(f"Negative news detected for {symbol}: "
                               f"sentiment={sentiment.overall_sentiment:.2f}, "
                               f"label={sentiment.sentiment_label}, "
                               f"articles={sentiment.article_count}")
                
            return has_negative
            
        except Exception as e:
            self.logger.error(f"Failed to check negative news for {symbol}: {str(e)}")
            return False  # Default to no negative news if check fails
            
    def get_market_sentiment(self, symbols: List[str] = None) -> Dict:
        """
        Get overall market sentiment based on major stocks
        """
        if symbols is None:
            symbols = ['SPY', 'QQQ', 'DIA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            
        try:
            sentiments = []
            total_articles = 0
            
            for symbol in symbols:
                sentiment = self.get_stock_sentiment(symbol, hours_back=12)
                if sentiment.article_count > 0:
                    sentiments.append(sentiment.overall_sentiment)
                    total_articles += sentiment.article_count
                    
            if not sentiments:
                return {
                    'overall_sentiment': 0.0,
                    'sentiment_label': 'neutral',
                    'confidence': 0.0,
                    'symbols_analyzed': 0,
                    'total_articles': 0
                }
                
            # Calculate market sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Determine label
            if avg_sentiment >= 0.3:
                label = 'positive'
            elif avg_sentiment >= -0.3:
                label = 'neutral'
            else:
                label = 'negative'
                
            return {
                'overall_sentiment': avg_sentiment,
                'sentiment_label': label,
                'confidence': min(1.0, len(sentiments) / len(symbols)),
                'symbols_analyzed': len(sentiments),
                'total_articles': total_articles,
                'sentiment_range': {
                    'min': min(sentiments),
                    'max': max(sentiments)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate market sentiment: {str(e)}")
            return {
                'overall_sentiment': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }
            
    def get_sentiment_based_risk_adjustment(self, symbol: str) -> float:
        """
        Get risk adjustment factor based on news sentiment
        Returns: multiplier for position size (0.0 to 1.2)
        """
        try:
            sentiment = self.get_stock_sentiment(symbol, hours_back=6)
            
            # Base adjustment on sentiment and confidence
            if sentiment.confidence < 0.2:
                return 1.0  # Low confidence, no adjustment
                
            if sentiment.recent_negative_news:
                return 0.0  # Don't trade on recent negative news
                
            if sentiment.sentiment_label == 'very_negative':
                return 0.2  # Severely reduce position
            elif sentiment.sentiment_label == 'negative':
                return 0.5  # Reduce position
            elif sentiment.sentiment_label == 'neutral':
                return 1.0  # Normal position
            elif sentiment.sentiment_label == 'positive':
                return 1.1  # Slightly increase position
            elif sentiment.sentiment_label == 'very_positive':
                return 1.2  # Increase position
            else:
                return 1.0
                
        except Exception as e:
            self.logger.error(f"Failed to get sentiment risk adjustment for {symbol}: {str(e)}")
            return 1.0
            
    def _parse_cached_news(self, cached_data: List[Dict]) -> List[NewsArticle]:
        """Parse cached news articles"""
        articles = []
        for item in cached_data:
            try:
                articles.append(NewsArticle(
                    title=item['title'],
                    description=item['description'],
                    source=item['source'],
                    published_at=datetime.fromisoformat(item['published_at']),
                    url=item['url'],
                    symbol=item.get('symbol'),
                    sentiment_score=item.get('sentiment_score'),
                    sentiment_label=item.get('sentiment_label'),
                    relevance_score=item.get('relevance_score')
                ))
            except Exception as e:
                self.logger.debug(f"Failed to parse cached article: {str(e)}")
                
        return articles
        
    def _parse_cached_sentiment(self, cached_data: Dict) -> SentimentAnalysis:
        """Parse cached sentiment analysis"""
        return SentimentAnalysis(
            symbol=cached_data['symbol'],
            overall_sentiment=cached_data['overall_sentiment'],
            sentiment_label=cached_data['sentiment_label'],
            article_count=cached_data['article_count'],
            confidence=cached_data['confidence'],
            recent_negative_news=cached_data['recent_negative_news'],
            major_news_detected=cached_data['major_news_detected']
        )
        
    def _article_to_dict(self, article: NewsArticle) -> Dict:
        """Convert article to dictionary for caching"""
        return {
            'title': article.title,
            'description': article.description,
            'source': article.source,
            'published_at': article.published_at.isoformat(),
            'url': article.url,
            'symbol': article.symbol,
            'sentiment_score': article.sentiment_score,
            'sentiment_label': article.sentiment_label,
            'relevance_score': article.relevance_score
        }
        
    def _sentiment_to_dict(self, sentiment: SentimentAnalysis) -> Dict:
        """Convert sentiment analysis to dictionary for caching"""
        return {
            'symbol': sentiment.symbol,
            'overall_sentiment': sentiment.overall_sentiment,
            'sentiment_label': sentiment.sentiment_label,
            'article_count': sentiment.article_count,
            'confidence': sentiment.confidence,
            'recent_negative_news': sentiment.recent_negative_news,
            'major_news_detected': sentiment.major_news_detected
        }
        
    def refresh_all_data(self):
        """Refresh all cached news data"""
        self.logger.info("Refreshing all news data")
        
        # Clear caches to force refresh
        self.news_cache.clear()
        self.sentiment_cache.clear()
        
        self.logger.info("News data refresh complete")
        
    def get_news_summary(self, symbols: List[str]) -> Dict:
        """Get news summary for multiple symbols"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'symbols_analyzed': [],
            'negative_news_alerts': [],
            'positive_news_highlights': [],
            'market_sentiment': self.get_market_sentiment(),
            'total_articles': 0
        }
        
        try:
            for symbol in symbols:
                sentiment = self.get_stock_sentiment(symbol, hours_back=6)
                summary['symbols_analyzed'].append({
                    'symbol': symbol,
                    'sentiment': sentiment.overall_sentiment,
                    'label': sentiment.sentiment_label,
                    'articles': sentiment.article_count
                })
                summary['total_articles'] += sentiment.article_count
                
                # Check for alerts
                if sentiment.recent_negative_news or sentiment.sentiment_label in ['negative', 'very_negative']:
                    summary['negative_news_alerts'].append({
                        'symbol': symbol,
                        'sentiment': sentiment.overall_sentiment,
                        'confidence': sentiment.confidence
                    })
                    
                if sentiment.sentiment_label in ['positive', 'very_positive'] and sentiment.confidence > 0.5:
                    summary['positive_news_highlights'].append({
                        'symbol': symbol,
                        'sentiment': sentiment.overall_sentiment,
                        'confidence': sentiment.confidence
                    })
                    
        except Exception as e:
            self.logger.error(f"Failed to generate news summary: {str(e)}")
            summary['error'] = str(e)
            
        return summary