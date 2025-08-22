"""
Price fetcher module for multiple cryptocurrency data sources.
"""
import asyncio
import aiohttp
import requests
import time
from typing import Dict, List, Optional, Union
from loguru import logger
import json


class PriceFetcher:
    """Fetches cryptocurrency prices from multiple sources and verifies data."""
    
    def __init__(self):
        self.sources = {
            'coingecko': self._fetch_coingecko,
            'coinbase': self._fetch_coinbase
        }
        self.last_fetch_time = {}
        self.cache_duration = 300  # 5 minutes cache
        self.price_cache = {}
    
    async def get_prices(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Fetch prices from multiple sources and return aggregated data.
        
        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC', 'ETH'])
            
        Returns:
            Dict with structure: {symbol: {source: price}}
        """
        results = {}
        
        for symbol in symbols:
            # Check cache first
            if self._is_cache_valid(symbol):
                results[symbol] = self.price_cache[symbol]
                continue
            
            symbol_results = {}
            
            # Fetch from all sources
            for source_name, fetch_func in self.sources.items():
                try:
                    price = await fetch_func(symbol)
                    if price:
                        symbol_results[source_name] = price
                        logger.info(f"Fetched {symbol} price from {source_name}: ${price}")
                except Exception as e:
                    logger.error(f"Error fetching {symbol} from {source_name}: {e}")
            
            if symbol_results:
                results[symbol] = symbol_results
                self._update_cache(symbol, symbol_results)
        
        return results
    
    def verify_prices(self, prices: Dict[str, Dict[str, float]], 
                     max_deviation: float = 0.05) -> Dict[str, float]:
        """
        Verify prices from multiple sources and return consensus prices.
        
        Args:
            prices: Price data from multiple sources
            max_deviation: Maximum allowed deviation between sources (5%)
            
        Returns:
            Dict with verified consensus prices
        """
        verified_prices = {}
        
        for symbol, source_prices in prices.items():
            if len(source_prices) < 2:
                # If only one source, use it but mark as unverified
                if source_prices:
                    verified_prices[symbol] = list(source_prices.values())[0]
                    logger.warning(f"Only one price source for {symbol}")
                continue
            
            price_values = list(source_prices.values())
            avg_price = sum(price_values) / len(price_values)
            
            # Check if all prices are within acceptable deviation
            valid_prices = []
            for price in price_values:
                deviation = abs(price - avg_price) / avg_price
                if deviation <= max_deviation:
                    valid_prices.append(price)
                else:
                    logger.warning(f"Price deviation for {symbol}: {deviation:.2%}")
            
            if valid_prices:
                verified_prices[symbol] = sum(valid_prices) / len(valid_prices)
                logger.info(f"Verified price for {symbol}: ${verified_prices[symbol]:.2f}")
            else:
                logger.error(f"No valid prices for {symbol} - all sources deviate too much")
        
        return verified_prices
    
    async def _fetch_coingecko(self, symbol: str) -> Optional[float]:
        """Fetch price from CoinGecko API."""
        try:
            coin_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'ADA': 'cardano',
                'SOL': 'solana',
                'MATIC': 'polygon'
            }
            
            coin_id = coin_map.get(symbol.upper())
            if not coin_id:
                logger.error(f"Unsupported symbol for CoinGecko: {symbol}")
                return None
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[coin_id]['usd']
                    else:
                        logger.error(f"CoinGecko API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching from CoinGecko: {e}")
            return None
    
    async def _fetch_coinbase(self, symbol: str) -> Optional[float]:
        """Fetch price from Coinbase Pro API."""
        try:
            product_id = f"{symbol.upper()}-USD"
            url = f"https://api.exchange.coinbase.com/products/{product_id}/ticker"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                    else:
                        logger.error(f"Coinbase API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching from Coinbase: {e}")
            return None
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached price is still valid."""
        if symbol not in self.price_cache:
            return False
        
        if symbol not in self.last_fetch_time:
            return False
        
        return time.time() - self.last_fetch_time[symbol] < self.cache_duration
    
    def _update_cache(self, symbol: str, prices: Dict[str, float]):
        """Update price cache."""
        self.price_cache[symbol] = prices
        self.last_fetch_time[symbol] = time.time()


if __name__ == "__main__":
    # Test the price fetcher
    async def test_price_fetcher():
        fetcher = PriceFetcher()
        symbols = ['BTC', 'ETH']
        
        prices = await fetcher.get_prices(symbols)
        print("Raw prices:", json.dumps(prices, indent=2))
        
        verified = fetcher.verify_prices(prices)
        print("Verified prices:", json.dumps(verified, indent=2))
    
    asyncio.run(test_price_fetcher())