"""
Basic tests for the trading system components.
"""
import unittest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.data_sources import PriceFetcher, SentimentAnalyzer
from src.portfolio import CoinbasePortfolioManager
from src.risk import RiskManager
from src.utils import config


class TestPriceFetcher(unittest.TestCase):
    """Test price fetching functionality."""
    
    def setUp(self):
        self.price_fetcher = PriceFetcher()
    
    def test_initialization(self):
        """Test that price fetcher initializes correctly."""
        self.assertIsNotNone(self.price_fetcher)
        self.assertIn('coingecko', self.price_fetcher.sources)
        self.assertIn('coinbase', self.price_fetcher.sources)
    
    def test_verify_prices(self):
        """Test price verification logic."""
        test_prices = {
            'BTC': {'coingecko': 45000, 'coinbase': 45100},
            'ETH': {'coingecko': 3000, 'coinbase': 2950}
        }
        
        verified = self.price_fetcher.verify_prices(test_prices)
        
        self.assertIn('BTC', verified)
        self.assertIn('ETH', verified)
        self.assertAlmostEqual(verified['BTC'], 45050, delta=100)


class TestSentimentAnalyzer(unittest.TestCase):
    """Test sentiment analysis functionality."""
    
    def setUp(self):
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def test_initialization(self):
        """Test sentiment analyzer initialization."""
        self.assertIsNotNone(self.sentiment_analyzer)
    
    def test_sentiment_interpretation(self):
        """Test sentiment score interpretation."""
        self.assertEqual(self.sentiment_analyzer._interpret_sentiment(0.4), "Very Bullish")
        self.assertEqual(self.sentiment_analyzer._interpret_sentiment(0.2), "Bullish")
        self.assertEqual(self.sentiment_analyzer._interpret_sentiment(0.0), "Neutral")
        self.assertEqual(self.sentiment_analyzer._interpret_sentiment(-0.2), "Bearish")
        self.assertEqual(self.sentiment_analyzer._interpret_sentiment(-0.4), "Very Bearish")


class TestPortfolioManager(unittest.TestCase):
    """Test portfolio management functionality."""
    
    def setUp(self):
        self.portfolio_manager = CoinbasePortfolioManager(sandbox=True)
    
    def test_initialization(self):
        """Test portfolio manager initialization."""
        self.assertIsNotNone(self.portfolio_manager)
        self.assertTrue(self.portfolio_manager.sandbox)
    
    def test_mock_portfolio(self):
        """Test mock portfolio functionality."""
        portfolio = self.portfolio_manager._get_mock_portfolio()
        
        self.assertIn('USD', portfolio)
        self.assertIn('BTC', portfolio)
        self.assertIn('ETH', portfolio)
        
        self.assertEqual(portfolio['USD']['balance'], 10000.0)
    
    def test_position_value_calculation(self):
        """Test position value calculation."""
        mock_prices = {'BTC': 45000, 'ETH': 3000}
        position = self.portfolio_manager.get_position_value('BTC', mock_prices)
        
        self.assertIn('quantity', position)
        self.assertIn('value_usd', position)
        self.assertIn('current_price', position)


class TestRiskManager(unittest.TestCase):
    """Test risk management functionality."""
    
    def setUp(self):
        self.risk_manager = RiskManager()
    
    def test_initialization(self):
        """Test risk manager initialization."""
        self.assertIsNotNone(self.risk_manager)
        self.assertEqual(self.risk_manager.max_position_size, 0.1)
        self.assertEqual(self.risk_manager.risk_per_trade, 0.02)
    
    def test_position_sizing(self):
        """Test position size calculation."""
        portfolio_value = 10000
        entry_price = 45000
        stop_loss_price = 43000
        
        position_info = self.risk_manager.calculate_position_size(
            portfolio_value, entry_price, stop_loss_price
        )
        
        self.assertIn('position_size', position_info)
        self.assertIn('position_value_usd', position_info)
        self.assertIn('max_loss_usd', position_info)
        self.assertGreater(position_info['position_size'], 0)
    
    def test_stop_loss_calculation(self):
        """Test stop loss and take profit calculation."""
        entry_price = 45000
        levels = self.risk_manager.calculate_stop_loss_take_profit(entry_price, 'buy')
        
        self.assertIn('stop_loss', levels)
        self.assertIn('take_profit', levels)
        self.assertLess(levels['stop_loss'], entry_price)
        self.assertGreater(levels['take_profit'], entry_price)


class TestConfiguration(unittest.TestCase):
    """Test configuration management."""
    
    def test_config_loading(self):
        """Test configuration loading."""
        trading_config = config.get_trading_config()
        
        self.assertIn('max_position_size', trading_config)
        self.assertIn('supported_coins', trading_config)
        self.assertIsInstance(trading_config['supported_coins'], list)
    
    def test_config_get_method(self):
        """Test configuration get method with dot notation."""
        max_position = config.get('trading.max_position_size')
        self.assertIsNotNone(max_position)
        
        # Test default value
        unknown_value = config.get('unknown.setting', 'default')
        self.assertEqual(unknown_value, 'default')


class TestAsyncComponents(unittest.TestCase):
    """Test async components."""
    
    def test_price_fetching_async(self):
        """Test async price fetching."""
        async def test_fetch():
            price_fetcher = PriceFetcher()
            prices = await price_fetcher.get_prices(['BTC'])
            return prices
        
        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_fetch())
            self.assertIsInstance(result, dict)
        finally:
            loop.close()
    
    def test_sentiment_analysis_async(self):
        """Test async sentiment analysis."""
        async def test_sentiment():
            sentiment_analyzer = SentimentAnalyzer()
            sentiment = await sentiment_analyzer.get_sentiment_data(['BTC'])
            return sentiment
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_sentiment())
            self.assertIsInstance(result, dict)
        finally:
            loop.close()


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)