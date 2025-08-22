"""
LLM integration module for trading decision making.
"""
import os
import json
import time
from typing import Dict, List, Optional, Any
from loguru import logger
import openai
from openai import OpenAI


class LLMTradingAdvisor:
    """Uses LLM to analyze market data and provide trading recommendations."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not provided, using mock responses")
        
        self.system_prompt = """You are a professional cryptocurrency trading advisor with expertise in technical analysis, market sentiment, and risk management. 

Your role is to analyze provided market data, sentiment analysis, portfolio information, and risk metrics to make informed trading decisions.

Always provide:
1. A clear trading recommendation (BUY, SELL, or HOLD)
2. Confidence level (0-100%)
3. Detailed reasoning for your recommendation
4. Risk assessment
5. Position sizing guidance
6. Entry/exit strategy

Be conservative with risk and always consider market volatility in cryptocurrency trading."""
    
    def get_trading_recommendation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get trading recommendation from LLM based on market context.
        
        Args:
            context: Market context including prices, sentiment, portfolio, etc.
            
        Returns:
            Trading recommendation with reasoning
        """
        try:
            if not self.client:
                return self._get_mock_recommendation(context)
            
            # Build the prompt with market context
            prompt = self._build_context_prompt(context)
            
            # Get LLM response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Parse response
            content = response.choices[0].message.content
            recommendation = self._parse_llm_response(content, context)
            
            logger.info(f"LLM recommendation generated for {context.get('symbol', 'unknown')}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error getting LLM recommendation: {e}")
            return self._get_mock_recommendation(context)
    
    def _build_context_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt with market context."""
        symbol = context.get('symbol', 'UNKNOWN')
        
        prompt_parts = [
            f"Please analyze the following market data for {symbol} and provide a trading recommendation:",
            "",
            "=== PRICE DATA ===",
        ]
        
        # Add price information
        if 'price_data' in context:
            price_data = context['price_data']
            prompt_parts.extend([
                f"Current Price: ${price_data.get('current_price', 'N/A')}",
                f"Price Sources: {', '.join(price_data.get('sources', []))}",
                f"Price Verification: {'Verified' if price_data.get('verified', False) else 'Unverified'}",
            ])
        
        # Add sentiment information
        prompt_parts.append("\n=== SENTIMENT ANALYSIS ===")
        if 'sentiment_data' in context:
            sentiment = context['sentiment_data']
            prompt_parts.extend([
                f"Overall Sentiment Score: {sentiment.get('overall_score', 0):.2f}",
                f"Interpretation: {sentiment.get('interpretation', 'Neutral')}",
                f"News Articles: {sentiment.get('news_sentiment', {}).get('article_count', 0)}",
                f"Confidence: {sentiment.get('confidence', 0):.2f}",
            ])
        
        # Add portfolio information
        prompt_parts.append("\n=== PORTFOLIO INFORMATION ===")
        if 'portfolio_data' in context:
            portfolio = context['portfolio_data']
            prompt_parts.extend([
                f"Total Portfolio Value: ${portfolio.get('total_value_usd', 0):,.2f}",
                f"USD Balance: ${portfolio.get('usd_balance', 0):,.2f}",
                f"Current Position in {symbol}: {portfolio.get('positions', {}).get(symbol, {}).get('quantity', 0)} coins",
                f"Position Value: ${portfolio.get('positions', {}).get(symbol, {}).get('value_usd', 0):,.2f}",
            ])
        
        # Add risk metrics
        prompt_parts.append("\n=== RISK ANALYSIS ===")
        if 'risk_data' in context:
            risk = context['risk_data']
            prompt_parts.extend([
                f"Recommended Position Size: {risk.get('position_size', 0):.6f} coins",
                f"Portfolio Percentage: {risk.get('portfolio_percentage', 0):.2f}%",
                f"Maximum Loss: ${risk.get('max_loss_usd', 0):.2f} ({risk.get('max_loss_percentage', 0):.2f}%)",
                f"Stop Loss Level: ${risk.get('stop_loss_price', 0)}",
                f"Take Profit Level: ${risk.get('take_profit_price', 0)}",
            ])
        
        # Add market context
        prompt_parts.append("\n=== MARKET CONTEXT ===")
        market_context = context.get('market_context', {})
        prompt_parts.extend([
            f"Market Trend: {market_context.get('trend', 'Unknown')}",
            f"Volatility: {market_context.get('volatility', 'Unknown')}",
            f"Volume: {market_context.get('volume', 'Unknown')}",
        ])
        
        prompt_parts.extend([
            "",
            "Based on this comprehensive analysis, please provide:",
            "1. Trading recommendation (BUY/SELL/HOLD)",
            "2. Confidence level (0-100%)",
            "3. Detailed reasoning",
            "4. Risk assessment",
            "5. Specific entry/exit strategy",
            "",
            "Format your response as JSON with the following structure:",
            "{",
            '  "recommendation": "BUY|SELL|HOLD",',
            '  "confidence": 85,',
            '  "reasoning": "Detailed explanation...",',
            '  "risk_level": "LOW|MEDIUM|HIGH",',
            '  "entry_strategy": "Specific entry guidance...",',
            '  "exit_strategy": "Specific exit guidance...",',
            '  "position_size_advice": "Position sizing recommendation..."',
            "}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured recommendation."""
        try:
            # Try to extract JSON from the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Validate required fields
                recommendation = {
                    'symbol': context.get('symbol', 'UNKNOWN'),
                    'recommendation': parsed.get('recommendation', 'HOLD').upper(),
                    'confidence': max(0, min(100, parsed.get('confidence', 50))),
                    'reasoning': parsed.get('reasoning', 'No reasoning provided'),
                    'risk_level': parsed.get('risk_level', 'MEDIUM').upper(),
                    'entry_strategy': parsed.get('entry_strategy', 'No entry strategy provided'),
                    'exit_strategy': parsed.get('exit_strategy', 'No exit strategy provided'),
                    'position_size_advice': parsed.get('position_size_advice', 'Use risk management guidelines'),
                    'timestamp': time.time(),
                    'llm_response': content
                }
                
                return recommendation
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            # Return fallback recommendation
            return {
                'symbol': context.get('symbol', 'UNKNOWN'),
                'recommendation': 'HOLD',
                'confidence': 50,
                'reasoning': f'Failed to parse LLM response: {e}',
                'risk_level': 'HIGH',
                'entry_strategy': 'Wait for clearer signals',
                'exit_strategy': 'Monitor closely',
                'position_size_advice': 'Use conservative sizing',
                'timestamp': time.time(),
                'llm_response': content
            }
    
    def _get_mock_recommendation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock recommendation when LLM is not available."""
        symbol = context.get('symbol', 'UNKNOWN')
        
        # Simple logic based on sentiment and price
        sentiment_score = context.get('sentiment_data', {}).get('overall_score', 0)
        
        if sentiment_score > 0.3:
            recommendation = 'BUY'
            confidence = 75
            reasoning = 'Strong positive sentiment and favorable market conditions'
        elif sentiment_score < -0.3:
            recommendation = 'SELL'
            confidence = 70
            reasoning = 'Negative sentiment suggests potential downside'
        else:
            recommendation = 'HOLD'
            confidence = 60
            reasoning = 'Neutral sentiment, waiting for clearer signals'
        
        return {
            'symbol': symbol,
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': reasoning,
            'risk_level': 'MEDIUM',
            'entry_strategy': 'Use dollar-cost averaging for entries',
            'exit_strategy': 'Set stop-loss at 5% below entry',
            'position_size_advice': 'Use recommended position sizing from risk management',
            'timestamp': time.time(),
            'llm_response': 'Mock response - LLM not available'
        }
    
    def analyze_market_context(self, prices: Dict[str, float], 
                             sentiment: Dict[str, Dict],
                             portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market context to provide additional insights.
        
        Args:
            prices: Current cryptocurrency prices
            sentiment: Sentiment analysis data
            portfolio: Portfolio information
            
        Returns:
            Market context analysis
        """
        context = {
            'overall_sentiment': 'neutral',
            'market_fear_greed': 50,  # 0-100 scale
            'trend_analysis': {},
            'volatility_assessment': 'medium',
            'recommendations': []
        }
        
        # Analyze overall sentiment
        sentiment_scores = []
        for symbol, data in sentiment.items():
            score = data.get('overall_score', 0)
            sentiment_scores.append(score)
        
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            if avg_sentiment > 0.2:
                context['overall_sentiment'] = 'bullish'
                context['market_fear_greed'] = 70
            elif avg_sentiment < -0.2:
                context['overall_sentiment'] = 'bearish'
                context['market_fear_greed'] = 30
        
        # Portfolio diversification check
        crypto_positions = {k: v for k, v in portfolio.get('positions', {}).items() if k != 'USD'}
        if len(crypto_positions) > 5:
            context['recommendations'].append('Consider consolidating positions for better risk management')
        elif len(crypto_positions) < 3:
            context['recommendations'].append('Consider diversifying across more cryptocurrencies')
        
        return context


if __name__ == "__main__":
    # Test the LLM advisor
    advisor = LLMTradingAdvisor()
    
    # Mock context data
    test_context = {
        'symbol': 'BTC',
        'price_data': {
            'current_price': 45000,
            'sources': ['coingecko', 'coinbase'],
            'verified': True
        },
        'sentiment_data': {
            'overall_score': 0.3,
            'interpretation': 'Bullish',
            'confidence': 0.8
        },
        'portfolio_data': {
            'total_value_usd': 10000,
            'usd_balance': 5000,
            'positions': {
                'BTC': {'quantity': 0.1, 'value_usd': 4500}
            }
        },
        'risk_data': {
            'position_size': 0.05,
            'portfolio_percentage': 2.25,
            'max_loss_usd': 200,
            'stop_loss_price': 43000
        }
    }
    
    recommendation = advisor.get_trading_recommendation(test_context)
    print("Trading recommendation:", json.dumps(recommendation, indent=2))