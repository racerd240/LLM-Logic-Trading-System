"""
Configuration management for the LLM Logic Trading System.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration for the trading system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to config/trading_config.json relative to project root
            self.config_path = Path(__file__).parent.parent.parent / "config" / "trading_config.json"
        
        self._config_data = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config_data = json.load(f)
            else:
                # Fallback to default configuration
                self._config_data = self._get_default_config()
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            self._config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "trading": {
                "max_position_size": 0.1,
                "risk_per_trade": 0.02,
                "min_trade_amount": 10.0,
                "supported_coins": ["BTC", "ETH", "ADA", "SOL", "MATIC"]
            },
            "risk_management": {
                "max_drawdown": 0.15,
                "stop_loss_percentage": 0.05,
                "take_profit_percentage": 0.10,
                "position_sizing_method": "kelly"
            },
            "llm": {
                "model": "gpt-4",
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "data_sources": {
                "price_sources": ["coingecko", "coinbase"],
                "sentiment_sources": ["newsapi", "reddit"],
                "cache_duration_minutes": 5
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        if not self._config_data:
            return default
        
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration."""
        return self._config_data.get('trading', {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return self._config_data.get('risk_management', {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        base_config = self._config_data.get('llm', {})
        return {
            'api_key': os.getenv('OPENAI_API_KEY') or os.getenv('LM_STUDIO_API_KEY'),
            'model': os.getenv('LLM_MODEL', base_config.get('model', 'gpt-4')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', base_config.get('max_tokens', 1000))),
            'temperature': float(os.getenv('LLM_TEMPERATURE', base_config.get('temperature', 0.7)))
        }
    
    def get_coinbase_config(self) -> Dict[str, Any]:
        """Get Coinbase configuration from environment variables."""
        return {
            'api_key': os.getenv('COINBASE_API_KEY'),
            'api_secret': os.getenv('COINBASE_API_SECRET'),
            'passphrase': os.getenv('COINBASE_PASSPHRASE'),
            'sandbox': os.getenv('COINBASE_USE_SANDBOX', 'true').lower() in ('true', '1', 'yes'),
            'api_target': os.getenv('COINBASE_API_TARGET', 'exchange')
        }
    
    def get_data_sources_config(self) -> Dict[str, Any]:
        """Get data sources configuration."""
        base_config = self._config_data.get('data_sources', {})
        return {
            **base_config,
            'news_api_key': os.getenv('NEWS_API_KEY'),
            'lunarcrush_api_key': os.getenv('LUNARCRUSH_API_KEY'),
            'coinmarketcap_api_key': os.getenv('COINMARKETCAP_API_KEY'),
            'whalealert_api_key': os.getenv('WHALEALERT_API_KEY')
        }


# Global configuration instance
config = ConfigManager()