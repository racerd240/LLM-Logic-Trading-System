"""
LLM integration module for trading decision making.
"""
import os
import json
from typing import Dict, Any, Optional
from loguru import logger


class LLMTradingAdvisor:
    """Uses LLM to analyze market data and provide trading recommendations."""

    def __init__(self, endpoint_url: Optional[str] = None, model: str = "Meta-Llama-3.1-8B-Instruct-Q4_K_M"):
        # Prefer env overrides when present
        self.endpoint_url = endpoint_url or os.getenv('LLM_ENDPOINT_URL')
        self.model = os.getenv('LLM_MODEL', model)

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

            # Send request to LLM endpoint
            response = self._query_llm(context)

            # Parse response
            return self._parse_llm_response(response, context)

        except Exception as e:
            logger.error(f"Error getting LLM recommendation: {e}")
            return self._get_mock_recommendation(context)

    def _query_llm(self, context: Dict[str, Any]) -> Any:
        """
        Query endpoint with the market context.

        Supports two payload modes:
        - Decision endpoint (default from .env.example): POST {"context": "<json-string>"}
        - OpenAI-style completions (fallback): POST {"model","prompt","max_tokens","temperature"}
        """
        import requests

        headers = {"Content-Type": "application/json"}

        # If endpoint looks like the documented decision endpoint, send structured JSON context
        if self.endpoint_url.rstrip("/").endswith("/decision"):
            payload_context = self._build_context_payload(context)
            payload = {
                "context": json.dumps(payload_context)
            }
        else:
            # Fallback to prompt-based contract
            payload = {
                "model": self.model,
                "prompt": self._build_context_prompt(context),
                "max_tokens": 1000,
                "temperature": 0.7
            }

        response = requests.post(self.endpoint_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()

    def _build_context_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build structured JSON payload for the decision endpoint.
        """
        symbol = context.get('symbol', 'UNKNOWN')
        return {
            "system_prompt": self.system_prompt,
            "model": self.model,
            "symbol": symbol,
            "price_data": context.get('price_data', {}),
            "sentiment_data": context.get('sentiment_data', {}),
            "portfolio": context.get('portfolio', {}),
            "risk": context.get('risk', {}),
            "meta": {
                "timestamp": context.get('timestamp')
            }
        }

    def _build_context_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt context for the trading recommendation."""
        symbol = context.get('symbol', 'UNKNOWN')

        prompt_parts = [
            self.system_prompt,
            "",
            f"Please analyze the following market data for {symbol} and provide a trading recommendation:",
            "",
            "=== PRICE DATA ===",
        ]

        # Add price information
        if 'price_data' in context and isinstance(context['price_data'], dict):
            price_data = context['price_data']
            sources = price_data.get('sources') or []
            prompt_parts.extend([
                f"Current Price: ${price_data.get('current_price', 'N/A')}",
                f"Price Sources: {', '.join(sources) if sources else 'N/A'}",
                f"Price Verification: {'Verified' if price_data.get('verified', False) else 'Unverified'}",
            ])

        # Add sentiment information
        prompt_parts.append("\n=== SENTIMENT ANALYSIS ===")
        if 'sentiment_data' in context and isinstance(context['sentiment_data'], dict):
            sentiment = context['sentiment_data']
            sources = sentiment.get('sources') or []
            prompt_parts.extend([
                f"Sentiment Score: {sentiment.get('score', 'N/A')}",
                f"Sentiment Sources: {', '.join(sources) if sources else 'N/A'}",
            ])

        return "\n".join(prompt_parts)

    def _parse_llm_response(self, response: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize LLM response into a standard recommendation dict:
        {
            "symbol": str,
            "action": "BUY"|"SELL"|"HOLD",
            "confidence": float (0-100),
            "reason": str
        }
        """
        symbol = context.get('symbol', 'UNKNOWN')

        try:
            # 1) Decision endpoint format: {"decisions":[{symbol,action,confidence,reason},...], ...}
            if isinstance(response, dict) and isinstance(response.get("decisions"), list) and response["decisions"]:
                chosen = None
                for d in response["decisions"]:
                    if not isinstance(d, dict):
                        continue
                    s = (d.get("symbol") or "").upper()
                    if symbol and s == str(symbol).upper():
                        chosen = d
                        break
                if not chosen:
                    chosen = next((d for d in response["decisions"] if isinstance(d, dict)), {})

                action = str(chosen.get("action", "HOLD")).upper()
                confidence = float(chosen.get("confidence", 0.0))
                reason = chosen.get("reason") or chosen.get("explanation") or "No reason provided."

                return {
                    "symbol": symbol or chosen.get("symbol", "UNKNOWN"),
                    "action": action if action in ("BUY", "SELL", "HOLD") else "HOLD",
                    "confidence": max(0.0, min(100.0, confidence)),
                    "reason": reason,
                }

            # 2) OpenAI-style completions: {"choices":[{"text": "..."}]}
            if isinstance(response, dict) and isinstance(response.get("choices"), list) and response["choices"]:
                choice = response["choices"][0] or {}
                text = choice.get("text") or (choice.get("message") or {}).get("content") or ""
                action = "HOLD"
                lt = text.lower()
                if "buy" in lt and "sell" not in lt:
                    action = "BUY"
                elif "sell" in lt and "buy" not in lt:
                    action = "SELL"
                confidence = 0.0
                # naive extraction of confidence like "Confidence: 78%"
                for token in text.replace("%", " ").split():
                    try:
                        val = float(token)
                        if 0.0 <= val <= 100.0:
                            confidence = val
                            break
                    except Exception:
                        pass
                reason = text.strip() or "No reasoning provided."

                return {
                    "symbol": symbol,
                    "action": action,
                    "confidence": confidence,
                    "reason": reason,
                }

            # 3) Flat dict with keys
            if isinstance(response, dict) and ("action" in response or "recommendation" in response):
                action = str(response.get("action") or response.get("recommendation") or "HOLD").upper()
                confidence = float(response.get("confidence", 0.0))
                reason = response.get("reason") or response.get("explanation") or "No reason provided."
                sym = response.get("symbol") or symbol
                return {
                    "symbol": sym,
                    "action": action if action in ("BUY", "SELL", "HOLD") else "HOLD",
                    "confidence": max(0.0, min(100.0, confidence)),
                    "reason": reason,
                }

            # 4) String response: attempt to parse keywords
            if isinstance(response, str):
                text = response
            else:
                text = json.dumps(response)

            lt = text.lower()
            action = "HOLD"
            if "buy" in lt and "sell" not in lt:
                action = "BUY"
            elif "sell" in lt and "buy" not in lt:
                action = "SELL"

            confidence = 0.0
            for token in text.replace("%", " ").split():
                try:
                    val = float(token)
                    if 0.0 <= val <= 100.0:
                        confidence = val
                        break
                except Exception:
                    pass

            return {
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "reason": text if text else "No reasoning provided.",
            }

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._get_mock_recommendation(context)

    def _get_mock_recommendation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safe fallback recommendation when the LLM endpoint is not available or parsing fails.
        """
        symbol = context.get('symbol', 'UNKNOWN')
        return {
            "symbol": symbol,
            "action": "HOLD",
            "confidence": 0.0,
            "reason": "LLM endpoint not configured or response could not be parsed."
        }
