#!/usr/bin/env python3
"""
Main entry point for the LLM Logic Trading System.
"""
import asyncio
import argparse
import sys
import json
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.trading_system import TradingSystem
from src.utils import config
from loguru import logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='LLM Logic Trading System')
    
    parser.add_argument(
        '--mode',
        choices=['analyze', 'continuous', 'test'],
        default='analyze',
        help='Operating mode: analyze (single run), continuous (loop), or test (dry run)'
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=None,
        help='Cryptocurrency symbols to analyze (e.g., BTC ETH ADA)'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute trades (default: dry run only)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    return parser.parse_args()


async def run_single_analysis(trading_system: TradingSystem, symbols=None):
    """Run a single analysis cycle."""
    logger.info("Running single analysis cycle...")
    
    results = await trading_system.run_analysis_cycle(symbols)
    
    if results.get('status') == 'success':
        print("\n" + "="*50)
        print("TRADING ANALYSIS RESULTS")
        print("="*50)
        
        # Portfolio summary
        portfolio = results.get('portfolio', {})
        print(f"Portfolio Value: ${portfolio.get('total_value_usd', 0):,.2f}")
        print(f"USD Balance: ${portfolio.get('usd_balance', 0):,.2f}")
        print(f"Crypto Value: ${portfolio.get('crypto_value_usd', 0):,.2f}")
        
        # Risk assessment
        risk = results.get('risk_assessment', {})
        print(f"Risk Level: {risk.get('risk_level', 'Unknown')}")
        print(f"Crypto Exposure: {risk.get('total_crypto_exposure', 0):.1f}%")
        
        print("\nRECOMMENDations:")
        print("-"*30)
        
        recommendations = results.get('recommendations', {})
        for symbol, rec in recommendations.items():
            if 'error' in rec:
                print(f"{symbol}: ERROR - {rec['error']}")
                continue
            
            llm_rec = rec.get('llm_recommendation', {})
            action = llm_rec.get('recommendation', 'UNKNOWN')
            confidence = llm_rec.get('confidence', 0)
            reasoning = llm_rec.get('reasoning', 'No reasoning provided')
            actionable = rec.get('actionable', False)
            
            current_price = rec.get('current_price', 0)
            position_value = rec.get('position_info', {}).get('value_usd', 0)
            
            print(f"\n{symbol} @ ${current_price:,.2f}")
            print(f"  Action: {action} (Confidence: {confidence}%)")
            print(f"  Actionable: {'Yes' if actionable else 'No'}")
            print(f"  Current Position: ${position_value:,.2f}")
            print(f"  Reasoning: {reasoning[:100]}...")
        
        print("\n" + "="*50)
    else:
        print(f"Analysis failed: {results.get('error', 'Unknown error')}")


async def run_continuous_trading(trading_system: TradingSystem, symbols=None, execute=False):
    """Run continuous trading loop."""
    logger.info("Starting continuous trading mode...")
    
    if not execute:
        logger.warning("DRY RUN MODE - No trades will be executed")
    
    try:
        await trading_system.run_continuous_trading(symbols, execute_trades=execute)
    except KeyboardInterrupt:
        logger.info("Stopping trading system...")
        trading_system.stop()


async def run_test_mode(trading_system: TradingSystem):
    """Run system tests."""
    logger.info("Running system tests...")
    
    # Test 1: Configuration
    print("Testing configuration...")
    trading_config = config.get_trading_config()
    print(f"  Supported coins: {trading_config['supported_coins']}")
    print(f"  Max position size: {trading_config['max_position_size']}")
    
    # Test 2: Price fetching
    print("\nTesting price fetching...")
    try:
        from src.data_sources import PriceFetcher
        price_fetcher = PriceFetcher()
        prices = await price_fetcher.get_prices(['BTC', 'ETH'])
        print(f"  Price data retrieved for {len(prices)} symbols")
    except Exception as e:
        print(f"  Price fetching failed: {e}")
    
    # Test 3: Portfolio access
    print("\nTesting portfolio access...")
    try:
        from src.portfolio import CoinbasePortfolioManager
        portfolio_manager = CoinbasePortfolioManager(sandbox=True)
        portfolio = portfolio_manager.get_portfolio_balance()
        print(f"  Portfolio data retrieved: {len(portfolio)} currencies")
    except Exception as e:
        print(f"  Portfolio access failed: {e}")
    
    # Test 4: LLM connection
    print("\nTesting LLM connection...")
    try:
        from src.llm import LLMTradingAdvisor
        llm_advisor = LLMTradingAdvisor()
        test_context = {
            'symbol': 'BTC',
            'price_data': {'current_price': 45000},
            'sentiment_data': {'overall_score': 0.1}
        }
        recommendation = llm_advisor.get_trading_recommendation(test_context)
        print(f"  LLM recommendation generated: {recommendation['recommendation']}")
    except Exception as e:
        print(f"  LLM connection failed: {e}")
    
    print("\nSystem tests completed!")


async def main():
    """Main application entry point."""
    args = parse_args()
    
    # Update log level
    import os
    os.environ['LOG_LEVEL'] = args.log_level
    
    # Initialize trading system
    try:
        trading_system = TradingSystem()
        logger.info("Trading system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize trading system: {e}")
        return 1
    
    # Run in selected mode
    try:
        if args.mode == 'analyze':
            await run_single_analysis(trading_system, args.symbols)
        elif args.mode == 'continuous':
            await run_continuous_trading(trading_system, args.symbols, args.execute)
        elif args.mode == 'test':
            await run_test_mode(trading_system)
        
        return 0
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())