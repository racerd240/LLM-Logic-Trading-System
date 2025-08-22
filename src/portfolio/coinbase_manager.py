"""
Coinbase portfolio management module.
"""
import os
import time
import hmac
import hashlib
import base64
import json
from typing import Dict, List, Optional, Tuple
import requests
from loguru import logger
from decimal import Decimal


class CoinbasePortfolioManager:
    """Manages Coinbase Pro portfolio and trading operations."""
    
    def __init__(self, api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None,
                 passphrase: Optional[str] = None,
                 sandbox: bool = True):
        self.api_key = api_key or os.getenv('COINBASE_API_KEY')
        self.api_secret = api_secret or os.getenv('COINBASE_API_SECRET')
        self.passphrase = passphrase or os.getenv('COINBASE_PASSPHRASE')
        self.sandbox = sandbox or os.getenv('COINBASE_SANDBOX', 'true').lower() == 'true'
        
        # Set API URLs
        if self.sandbox:
            self.api_url = 'https://api-public.sandbox.exchange.coinbase.com'
        else:
            self.api_url = 'https://api.exchange.coinbase.com'
        
        # Portfolio cache
        self.portfolio_cache = {}
        self.cache_duration = 60  # 1 minute cache
        self.last_cache_time = 0
    
    def _generate_signature(self, timestamp: str, method: str, 
                          request_path: str, body: str = '') -> str:
        """Generate signature for Coinbase Pro API authentication."""
        if not self.api_secret:
            raise ValueError("API secret not provided")
        
        message = timestamp + method + request_path + body
        hmac_key = base64.b64decode(self.api_secret)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode()
        
        return signature_b64
    
    def _get_headers(self, method: str, request_path: str, body: str = '') -> Dict[str, str]:
        """Get headers for API request."""
        if not all([self.api_key, self.api_secret, self.passphrase]):
            logger.warning("Coinbase API credentials not provided, using mock mode")
            return {}
        
        timestamp = str(time.time())
        signature = self._generate_signature(timestamp, method, request_path, body)
        
        return {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    def get_portfolio_balance(self) -> Dict[str, Dict[str, float]]:
        """
        Get current portfolio balance.
        
        Returns:
            Dict with balance information for each currency
        """
        # Check cache first
        if self._is_cache_valid():
            logger.info("Using cached portfolio data")
            return self.portfolio_cache
        
        try:
            if not all([self.api_key, self.api_secret, self.passphrase]):
                logger.warning("Using mock portfolio data")
                return self._get_mock_portfolio()
            
            request_path = '/accounts'
            headers = self._get_headers('GET', request_path)
            
            response = requests.get(
                f"{self.api_url}{request_path}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                accounts = response.json()
                portfolio = {}
                
                for account in accounts:
                    currency = account['currency']
                    portfolio[currency] = {
                        'balance': float(account['balance']),
                        'available': float(account['available']),
                        'hold': float(account['hold'])
                    }
                
                self._update_cache(portfolio)
                logger.info(f"Retrieved portfolio with {len(portfolio)} currencies")
                return portfolio
            else:
                logger.error(f"Failed to get portfolio: {response.status_code} - {response.text}")
                return self._get_mock_portfolio()
                
        except Exception as e:
            logger.error(f"Error getting portfolio balance: {e}")
            return self._get_mock_portfolio()
    
    def get_position_value(self, symbol: str, current_prices: Dict[str, float]) -> Dict[str, float]:
        """
        Get position value for a specific cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            current_prices: Dictionary of current prices
            
        Returns:
            Dict with position information
        """
        portfolio = self.get_portfolio_balance()
        
        if symbol not in portfolio:
            return {
                'quantity': 0.0,
                'value_usd': 0.0,
                'available': 0.0,
                'hold': 0.0
            }
        
        quantity = portfolio[symbol]['balance']
        available = portfolio[symbol]['available']
        hold = portfolio[symbol]['hold']
        
        current_price = current_prices.get(symbol, 0.0)
        value_usd = quantity * current_price
        
        return {
            'quantity': quantity,
            'value_usd': value_usd,
            'available': available,
            'hold': hold,
            'current_price': current_price
        }
    
    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate total portfolio value.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Dict with portfolio valuation information
        """
        portfolio = self.get_portfolio_balance()
        total_value = 0.0
        crypto_value = 0.0
        usd_balance = 0.0
        
        positions = {}
        
        for currency, balance_info in portfolio.items():
            quantity = balance_info['balance']
            
            if currency == 'USD':
                usd_balance = quantity
                total_value += quantity
            else:
                current_price = current_prices.get(currency, 0.0)
                position_value = quantity * current_price
                crypto_value += position_value
                total_value += position_value
                
                if quantity > 0:
                    positions[currency] = {
                        'quantity': quantity,
                        'value_usd': position_value,
                        'percentage': 0.0  # Will be calculated below
                    }
        
        # Calculate percentages
        if total_value > 0:
            for currency in positions:
                positions[currency]['percentage'] = (positions[currency]['value_usd'] / total_value) * 100
        
        return {
            'total_value_usd': total_value,
            'crypto_value_usd': crypto_value,
            'usd_balance': usd_balance,
            'positions': positions
        }
    
    def place_market_order(self, symbol: str, side: str, size: float) -> Dict:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USD')
            side: 'buy' or 'sell'
            size: Order size
            
        Returns:
            Order response
        """
        try:
            if not all([self.api_key, self.api_secret, self.passphrase]):
                logger.warning("Using mock order placement")
                return self._mock_order_response(symbol, side, size)
            
            request_path = '/orders'
            body = json.dumps({
                'type': 'market',
                'side': side,
                'product_id': symbol,
                'size': str(size)
            })
            
            headers = self._get_headers('POST', request_path, body)
            
            response = requests.post(
                f"{self.api_url}{request_path}",
                headers=headers,
                data=body,
                timeout=10
            )
            
            if response.status_code == 200:
                order_data = response.json()
                logger.info(f"Placed {side} order for {size} {symbol}: {order_data['id']}")
                return order_data
            else:
                logger.error(f"Failed to place order: {response.status_code} - {response.text}")
                return self._mock_order_response(symbol, side, size, success=False)
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return self._mock_order_response(symbol, side, size, success=False)
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get status of a specific order."""
        try:
            if not all([self.api_key, self.api_secret, self.passphrase]):
                return {'status': 'filled', 'id': order_id}
            
            request_path = f'/orders/{order_id}'
            headers = self._get_headers('GET', request_path)
            
            response = requests.get(
                f"{self.api_url}{request_path}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get order status: {response.status_code}")
                return {'status': 'unknown', 'id': order_id}
                
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {'status': 'error', 'id': order_id}
    
    def _get_mock_portfolio(self) -> Dict[str, Dict[str, float]]:
        """Get mock portfolio for testing."""
        return {
            'USD': {'balance': 10000.0, 'available': 10000.0, 'hold': 0.0},
            'BTC': {'balance': 0.1, 'available': 0.1, 'hold': 0.0},
            'ETH': {'balance': 1.5, 'available': 1.5, 'hold': 0.0},
        }
    
    def _mock_order_response(self, symbol: str, side: str, size: float, success: bool = True) -> Dict:
        """Generate mock order response."""
        if success:
            return {
                'id': f'mock-order-{int(time.time())}',
                'product_id': symbol,
                'side': side,
                'size': str(size),
                'status': 'pending',
                'type': 'market'
            }
        else:
            return {
                'message': 'Mock order failed',
                'success': False
            }
    
    def _is_cache_valid(self) -> bool:
        """Check if portfolio cache is still valid."""
        return time.time() - self.last_cache_time < self.cache_duration
    
    def _update_cache(self, portfolio: Dict):
        """Update portfolio cache."""
        self.portfolio_cache = portfolio
        self.last_cache_time = time.time()


if __name__ == "__main__":
    # Test the portfolio manager
    manager = CoinbasePortfolioManager(sandbox=True)
    
    # Test portfolio balance
    portfolio = manager.get_portfolio_balance()
    print("Portfolio balance:", json.dumps(portfolio, indent=2))
    
    # Test portfolio value calculation
    mock_prices = {'BTC': 45000, 'ETH': 3000}
    portfolio_value = manager.calculate_portfolio_value(mock_prices)
    print("Portfolio value:", json.dumps(portfolio_value, indent=2))