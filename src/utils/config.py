"""
Configuration management utility.
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


class ConfigManager:
    """Manages application configuration from files and environment variables."""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / "config"
        self.config_cache = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load default configuration
        self._load_trading_config()
    
    def _load_trading_config(self):
        """Load trading configuration from JSON file."""
        config_file = self.config_dir / "trading_config.json"
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config_cache = json.load(f)
                logger.info(f"Loaded configuration from {config_file}")
            else:
                logger.warning(f"Configuration file not found: {config_file}")
                self.config_cache = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config_cache = self._get_default_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with dot notation support.
        
        Args:
            key: Configuration key (supports dot notation like 'trading.max_position_size')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # First check environment variables
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)
        
        # Then check configuration file
        keys = key.split('.')
        value = self.config_cache
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_coinbase_config(self) -> Dict[str, str]:
        """Get Coinbase API configuration."""
        return {
            'api_key': os.getenv('COINBASE_API_KEY'),
            'api_secret': os.getenv('COINBASE_API_SECRET'),
            'passphrase': os.getenv('COINBASE_PASSPHRASE'),
            'sandbox': os.getenv('COINBASE_SANDBOX', 'true').lower() == 'true'
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('LLM_MODEL', self.get('llm.model', 'gpt-4')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', self.get('llm.max_tokens', 1000))),
            'temperature': float(self.get('llm.temperature', 0.7))
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration."""
        return {
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', self.get('trading.max_position_size', 0.1))),
            'risk_per_trade': float(os.getenv('RISK_PER_TRADE', self.get('trading.risk_per_trade', 0.02))),
            'min_trade_amount': float(os.getenv('MIN_TRADE_AMOUNT', self.get('trading.min_trade_amount', 10.0))),
            'supported_coins': self.get('trading.supported_coins', ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC']),
            'trading_pairs': self.get('trading.trading_pairs', ['BTC-USD', 'ETH-USD'])
        }
    
    def get_data_source_config(self) -> Dict[str, Any]:
        """Get data source configuration."""
        return {
            'coingecko_api_key': os.getenv('COINGECKO_API_KEY'),
            'news_api_key': os.getenv('NEWS_API_KEY'),
            'price_sources': self.get('data_sources.price_sources', ['coingecko', 'coinbase']),
            'sentiment_sources': self.get('data_sources.sentiment_sources', ['newsapi']),
            'cache_duration_minutes': int(self.get('data_sources.cache_duration_minutes', 5))
        }
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return {
            'max_drawdown': float(self.get('risk_management.max_drawdown', 0.15)),
            'stop_loss_percentage': float(self.get('risk_management.stop_loss_percentage', 0.05)),
            'take_profit_percentage': float(self.get('risk_management.take_profit_percentage', 0.10)),
            'position_sizing_method': self.get('risk_management.position_sizing_method', 'kelly')
        }
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when file is not available."""
        return {
            "trading": {
                "max_position_size": 0.1,
                "risk_per_trade": 0.02,
                "min_trade_amount": 10.0,
                "supported_coins": ["BTC", "ETH", "ADA", "SOL", "MATIC"],
                "trading_pairs": ["BTC-USD", "ETH-USD", "ADA-USD", "SOL-USD", "MATIC-USD"]
            },
            "data_sources": {
                "price_sources": ["coingecko", "coinbase"],
                "sentiment_sources": ["newsapi"],
                "cache_duration_minutes": 5
            },
            "llm": {
                "model": "gpt-4",
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "risk_management": {
                "max_drawdown": 0.15,
                "stop_loss_percentage": 0.05,
                "take_profit_percentage": 0.10,
                "position_sizing_method": "kelly"
            }
        }


# Global configuration instance
config = ConfigManager()


if __name__ == "__main__":
    # Test configuration manager
    config_mgr = ConfigManager()
    
    print("Trading config:", config_mgr.get_trading_config())
    print("LLM config:", config_mgr.get_llm_config())
    print("Coinbase config:", config_mgr.get_coinbase_config())
    print("Risk config:", config_mgr.get_risk_config())