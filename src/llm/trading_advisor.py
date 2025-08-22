"""
LLM integration module for trading decision making.
"""
import os
import json
import time
from typing import Dict, Any
from loguru import logger


class LLMTradingAdvisor:
    """Uses LLM to analyze market data and provide trading recommendations."""
    
    def __init__(self, endpoint_url: Optional[str] = None, model: str = "Meta-Llama-3.1-8B-Instruct-Q4_K_M"):
        self.endpoint_url = endpoint_url or os.getenv('LLM_ENDPOINT_URL')
        self.model = model
        
        if not self.endpoint_url:
            logger.error("LM Studio endpoint URL not provided. Ensure LLM_ENDPOINT_URL is set.")
        
        self.system_prompt = """You are a professional cryptocurrency trading advisor with expertise in technical analysis, market sentiment, and risk management. 
Your role is to analyze provided market data, sentiment analysis, portfolio information, and risk metrics to make informed trading decisions.
Provide: 
1. A clear trading recommendation.
2. Confidence level (0-100%).
3. Detailed reasoning."""

    def get_trading_recommendation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get trading recommendation from LLM based on market context.
        """
        try:
            if not self.endpoint_url:
                return self._get_mock_recommendation(context)
            
            # Build the prompt
            prompt = self._build_context_prompt(context)
            
            # Send request to LM Studio endpoint
            response = self._query_llm(prompt)
            
            # Parse response
            return self._parse_llm_response(response, context)

        except Exception as e:
            logger.error(f"Error getting LLM recommendation: {e}")
            return self._get_mock_recommendation(context)
    
    def _query_llm(self, prompt: str) -> str:
        """
        Query LM Studio endpoint with the prompt.
        """
        import requests
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(self.endpoint_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def _build_context_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt context for the trading recommendation."""
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
                f"Sentiment Score: {sentiment.get('score', 'N/A')}",
                f"Sentiment Sources: {', '.join(sentiment.get('sources', []))}",
            ])
        
        return "\n".join(prompt_parts)