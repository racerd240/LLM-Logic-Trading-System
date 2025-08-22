"""
Sentiment analysis module for cryptocurrency market sentiment.
"""
import asyncio
import aiohttp
import requests
import time
import json
from typing import Dict, List, Optional, Tuple
from loguru import logger
import os
from datetime import datetime, timedelta


class SentimentAnalyzer:
    """Analyzes cryptocurrency sentiment from news and social media sources."""
    
    def __init__(self, news_api_key: Optional[str] = None):
        self.news_api_key = news_api_key or os.getenv('NEWS_API_KEY')
        self.cache_duration = 1800  # 30 minutes cache
        self.sentiment_cache = {}
        self.last_fetch_time = {}
    
    async def get_sentiment_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get sentiment data for given cryptocurrency symbols.
        
        Args:
            symbols: List of cryptocurrency symbols
            
        Returns:
            Dict with sentiment scores and analysis
        """
        results = {}
        
        for symbol in symbols:
            # Check cache first
            if self._is_cache_valid(symbol):
                results[symbol] = self.sentiment_cache[symbol]
                continue
            
            try:
                # Fetch news sentiment
                news_sentiment = await self._fetch_news_sentiment(symbol)
                
                # Fetch social sentiment (placeholder for reddit/twitter)
                social_sentiment = await self._fetch_social_sentiment(symbol)
                
                # Combine sentiments
                combined_sentiment = self._combine_sentiments(news_sentiment, social_sentiment)
                
                results[symbol] = combined_sentiment
                self._update_cache(symbol, combined_sentiment)
                
                logger.info(f"Fetched sentiment for {symbol}: {combined_sentiment['overall_score']:.2f}")
                
            except Exception as e:
                logger.error(f"Error fetching sentiment for {symbol}: {e}")
                results[symbol] = self._get_neutral_sentiment()
        
        return results
    
    async def _fetch_news_sentiment(self, symbol: str) -> Dict:
        """Fetch news sentiment for a cryptocurrency."""
        if not self.news_api_key:
            logger.warning("No News API key provided, using placeholder sentiment")
            return self._get_placeholder_news_sentiment(symbol)
        
        try:
            # Calculate date range (last 24 hours)
            to_date = datetime.now()
            from_date = to_date - timedelta(days=1)
            
            # Search terms for different cryptocurrencies
            search_terms = {
                'BTC': 'Bitcoin OR BTC',
                'ETH': 'Ethereum OR ETH',
                'ADA': 'Cardano OR ADA',
                'SOL': 'Solana OR SOL',
                'MATIC': 'Polygon OR MATIC'
            }
            
            query = search_terms.get(symbol.upper(), symbol)
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'sortBy': 'popularity',
                'language': 'en',
                'apiKey': self.news_api_key,
                'pageSize': 20
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._analyze_news_sentiment(data['articles'])
                    else:
                        logger.error(f"News API error: {response.status}")
                        return self._get_placeholder_news_sentiment(symbol)
                        
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {e}")
            return self._get_placeholder_news_sentiment(symbol)
    
    async def _fetch_social_sentiment(self, symbol: str) -> Dict:
        """Fetch social media sentiment (placeholder implementation)."""
        # This is a placeholder for social media sentiment
        # In a real implementation, you would integrate with Reddit API, Twitter API, etc.
        return {
            'score': 0.0,  # Neutral
            'sources': ['reddit', 'twitter'],
            'mentions': 0,
            'confidence': 0.5
        }
    
    def _analyze_news_sentiment(self, articles: List[Dict]) -> Dict:
        """Analyze sentiment from news articles."""
        if not articles:
            return {
                'score': 0.0,
                'article_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'confidence': 0.0
            }
        
        # Simple sentiment analysis based on keywords
        positive_keywords = [
            'bull', 'bullish', 'rally', 'surge', 'moon', 'pump', 'gains', 
            'profit', 'buy', 'investing', 'adoption', 'breakthrough', 'success'
        ]
        
        negative_keywords = [
            'bear', 'bearish', 'crash', 'dump', 'sell', 'loss', 'decline',
            'fall', 'drop', 'risk', 'regulation', 'ban', 'hack', 'scam'
        ]
        
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            
            positive_score = sum(1 for keyword in positive_keywords if keyword in content)
            negative_score = sum(1 for keyword in negative_keywords if keyword in content)
            
            if positive_score > negative_score:
                sentiment_scores.append(1)
                positive_count += 1
            elif negative_score > positive_score:
                sentiment_scores.append(-1)
                negative_count += 1
            else:
                sentiment_scores.append(0)
                neutral_count += 1
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        return {
            'score': avg_sentiment,
            'article_count': len(articles),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'confidence': min(len(articles) / 20.0, 1.0)  # Confidence based on article count
        }
    
    def _combine_sentiments(self, news_sentiment: Dict, social_sentiment: Dict) -> Dict:
        """Combine news and social sentiment into overall sentiment."""
        news_score = news_sentiment.get('score', 0)
        social_score = social_sentiment.get('score', 0)
        
        news_confidence = news_sentiment.get('confidence', 0)
        social_confidence = social_sentiment.get('confidence', 0)
        
        # Weighted average based on confidence
        total_confidence = news_confidence + social_confidence
        if total_confidence > 0:
            overall_score = (news_score * news_confidence + social_score * social_confidence) / total_confidence
        else:
            overall_score = 0
        
        return {
            'overall_score': overall_score,
            'news_sentiment': news_sentiment,
            'social_sentiment': social_sentiment,
            'confidence': total_confidence / 2,
            'timestamp': time.time(),
            'interpretation': self._interpret_sentiment(overall_score)
        }
    
    def _interpret_sentiment(self, score: float) -> str:
        """Interpret sentiment score as human-readable text."""
        if score > 0.3:
            return "Very Bullish"
        elif score > 0.1:
            return "Bullish"
        elif score > -0.1:
            return "Neutral"
        elif score > -0.3:
            return "Bearish"
        else:
            return "Very Bearish"
    
    def _get_placeholder_news_sentiment(self, symbol: str) -> Dict:
        """Get placeholder news sentiment when API is not available."""
        return {
            'score': 0.0,
            'article_count': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'confidence': 0.0
        }
    
    def _get_neutral_sentiment(self) -> Dict:
        """Get neutral sentiment as fallback."""
        return {
            'overall_score': 0.0,
            'news_sentiment': {'score': 0.0, 'confidence': 0.0},
            'social_sentiment': {'score': 0.0, 'confidence': 0.0},
            'confidence': 0.0,
            'timestamp': time.time(),
            'interpretation': "Neutral"
        }
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached sentiment is still valid."""
        if symbol not in self.sentiment_cache:
            return False
        
        if symbol not in self.last_fetch_time:
            return False
        
        return time.time() - self.last_fetch_time[symbol] < self.cache_duration
    
    def _update_cache(self, symbol: str, sentiment: Dict):
        """Update sentiment cache."""
        self.sentiment_cache[symbol] = sentiment
        self.last_fetch_time[symbol] = time.time()


if __name__ == "__main__":
    # Test the sentiment analyzer
    async def test_sentiment_analyzer():
        analyzer = SentimentAnalyzer()
        symbols = ['BTC', 'ETH']
        
        sentiment_data = await analyzer.get_sentiment_data(symbols)
        print("Sentiment data:", json.dumps(sentiment_data, indent=2))
    
    asyncio.run(test_sentiment_analyzer())