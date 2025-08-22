#!/usr/bin/env python3
"""
Demo script for the LLM Logic Trading System with mock data.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_sources import PriceFetcher, SentimentAnalyzer
from src.portfolio import CoinbasePortfolioManager
from src.risk import RiskManager
from src.llm import LLMTradingAdvisor
from src.utils import config
from loguru import logger


async def demo_individual_components():
    """Demonstrate individual components with mock data."""
    print("="*60)
    print("LLM LOGIC TRADING SYSTEM - COMPONENT DEMO")
    print("="*60)
    
    # 1. Price Fetcher Demo
    print("\n1. PRICE FETCHING DEMO")
    print("-" * 30)
    
    price_fetcher = PriceFetcher()
    
    # Simulate price data since we can't access real APIs
    mock_prices = {
        'BTC': {'coingecko': 45000, 'coinbase': 45100},
        'ETH': {'coingecko': 3000, 'coinbase': 2950}
    }
    
    verified_prices = price_fetcher.verify_prices(mock_prices)
    print(f"Mock prices verified: {json.dumps(verified_prices, indent=2)}")
    
    # 2. Sentiment Analysis Demo
    print("\n2. SENTIMENT ANALYSIS DEMO")
    print("-" * 30)
    
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_data = await sentiment_analyzer.get_sentiment_data(['BTC', 'ETH'])
    
    for symbol, data in sentiment_data.items():
        print(f"{symbol} Sentiment: {data['interpretation']} (Score: {data['overall_score']:.2f})")
    
    # 3. Portfolio Management Demo
    print("\n3. PORTFOLIO MANAGEMENT DEMO")
    print("-" * 30)
    
    portfolio_manager = CoinbasePortfolioManager(sandbox=True)
    portfolio_balance = portfolio_manager.get_portfolio_balance()
    portfolio_value = portfolio_manager.calculate_portfolio_value(verified_prices)
    
    print(f"Portfolio Value: ${portfolio_value['total_value_usd']:,.2f}")
    print(f"USD Balance: ${portfolio_value['usd_balance']:,.2f}")
    print(f"Crypto Value: ${portfolio_value['crypto_value_usd']:,.2f}")
    
    print("\nPositions:")
    for symbol, position in portfolio_value['positions'].items():
        print(f"  {symbol}: {position['quantity']:.6f} coins (${position['value_usd']:,.2f})")
    
    # 4. Risk Management Demo
    print("\n4. RISK MANAGEMENT DEMO")
    print("-" * 30)
    
    risk_manager = RiskManager()
    
    # Calculate position sizing for BTC
    btc_price = verified_prices['BTC']
    stop_loss_price = btc_price * 0.95  # 5% stop loss
    
    position_info = risk_manager.calculate_position_size(
        portfolio_value['total_value_usd'],
        btc_price,
        stop_loss_price,
        confidence=0.8,
        method='kelly'
    )
    
    print(f"Recommended BTC position size: {position_info['position_size']:.6f} BTC")
    print(f"Position value: ${position_info['position_value_usd']:,.2f}")
    print(f"Portfolio percentage: {position_info['portfolio_percentage']:.2f}%")
    print(f"Maximum loss: ${position_info['max_loss_usd']:,.2f}")
    
    # Portfolio risk assessment
    risk_assessment = risk_manager.assess_portfolio_risk(portfolio_value['positions'])
    print(f"\nPortfolio Risk Level: {risk_assessment['risk_level']}")
    print(f"Total Crypto Exposure: {risk_assessment['total_crypto_exposure']:.1f}%")
    
    # 5. LLM Trading Advisor Demo
    print("\n5. LLM TRADING ADVISOR DEMO")
    print("-" * 30)
    
    llm_advisor = LLMTradingAdvisor()
    
    # Build context for BTC
    context = {
        'symbol': 'BTC',
        'price_data': {
            'current_price': btc_price,
            'sources': ['coingecko', 'coinbase'],
            'verified': True
        },
        'sentiment_data': sentiment_data['BTC'],
        'portfolio_data': portfolio_value,
        'risk_data': position_info,
        'market_context': {
            'trend': 'bullish',
            'volatility': 'high',
            'volume': 'above_average'
        }
    }
    
    recommendation = llm_advisor.get_trading_recommendation(context)
    
    print(f"Trading Recommendation for BTC:")
    print(f"  Action: {recommendation['recommendation']}")
    print(f"  Confidence: {recommendation['confidence']}%")
    print(f"  Risk Level: {recommendation['risk_level']}")
    print(f"  Reasoning: {recommendation['reasoning'][:100]}...")
    
    return {
        'prices': verified_prices,
        'sentiment': sentiment_data,
        'portfolio': portfolio_value,
        'risk_assessment': risk_assessment,
        'btc_recommendation': recommendation
    }


async def demo_integrated_system():
    """Demonstrate the integrated trading system."""
    print("\n" + "="*60)
    print("INTEGRATED SYSTEM DEMO")
    print("="*60)
    
    # Create mock trading system with simulated data
    from src.trading_system import TradingSystem
    
    # Override price fetcher to return mock data
    class MockTradingSystem(TradingSystem):
        async def run_analysis_cycle(self, symbols=None):
            """Override with mock data for demo."""
            if not symbols:
                symbols = ['BTC', 'ETH']
            
            # Mock verified prices
            verified_prices = {'BTC': 45050, 'ETH': 2975}
            
            # Get real sentiment data (mock)
            sentiment_data = await self.sentiment_analyzer.get_sentiment_data(symbols)
            
            # Get portfolio data
            portfolio_balance = self.portfolio_manager.get_portfolio_balance()
            portfolio_value = self.portfolio_manager.calculate_portfolio_value(verified_prices)
            
            # Generate recommendations
            recommendations = {}
            for symbol in symbols:
                recommendation = await self._generate_recommendation(
                    symbol, verified_prices, sentiment_data, portfolio_balance, portfolio_value
                )
                recommendations[symbol] = recommendation
            
            # Portfolio risk assessment
            risk_assessment = self.risk_manager.assess_portfolio_risk(
                portfolio_value.get('positions', {})
            )
            
            return {
                'timestamp': 1704067200,  # Mock timestamp
                'prices': verified_prices,
                'sentiment': sentiment_data,
                'portfolio': portfolio_value,
                'risk_assessment': risk_assessment,
                'recommendations': recommendations,
                'status': 'success'
            }
    
    mock_system = MockTradingSystem()
    results = await mock_system.run_analysis_cycle(['BTC', 'ETH'])
    
    print("\nINTEGRATED ANALYSIS RESULTS:")
    print("-" * 40)
    
    portfolio = results['portfolio']
    print(f"Portfolio Value: ${portfolio['total_value_usd']:,.2f}")
    print(f"Risk Level: {results['risk_assessment']['risk_level']}")
    
    print("\nTRADING RECOMMENDATIONS:")
    for symbol, rec in results['recommendations'].items():
        if 'error' not in rec:
            llm_rec = rec['llm_recommendation']
            print(f"\n{symbol} @ ${rec['current_price']:,.2f}")
            print(f"  Recommendation: {llm_rec['recommendation']}")
            print(f"  Confidence: {llm_rec['confidence']}%")
            print(f"  Risk Level: {llm_rec['risk_level']}")
            print(f"  Actionable: {'Yes' if rec['actionable'] else 'No'}")
            print(f"  Position Size: {rec['risk_metrics']['position_size']:.6f} {symbol}")
            print(f"  Stop Loss: ${rec['levels']['stop_loss']:,.2f}")
            print(f"  Take Profit: ${rec['levels']['take_profit']:,.2f}")
    
    return results


async def main():
    """Main demo function."""
    print("Starting LLM Logic Trading System Demo...")
    print("Note: Using mock data due to API restrictions in this environment")
    
    # Demo individual components
    component_results = await demo_individual_components()
    
    # Demo integrated system
    system_results = await demo_integrated_system()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nThe system demonstrates:")
    print("✓ Multi-source price fetching and verification")
    print("✓ Sentiment analysis from news sources")
    print("✓ Portfolio management and position tracking")
    print("✓ Advanced risk management and position sizing")
    print("✓ LLM-powered trading recommendations")
    print("✓ Integrated analysis and decision-making")
    print("\nTo run with real data, configure API keys in .env file")
    print("and run: python main.py --mode analyze --symbols BTC ETH")


if __name__ == "__main__":
    asyncio.run(main())