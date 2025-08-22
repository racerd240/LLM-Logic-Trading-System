"""
Main trading system orchestrator.
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from loguru import logger

from src.data_sources import PriceFetcher, SentimentAnalyzer
from src.portfolio import CoinbasePortfolioManager
from src.risk import RiskManager
from src.llm import LLMTradingAdvisor
from src.utils import config


class TradingSystem:
    """Main trading system orchestrator that coordinates all components."""
    
    def __init__(self):
        # Initialize components
        self.price_fetcher = PriceFetcher()
        self.sentiment_analyzer = SentimentAnalyzer(
            news_api_key=config.get('data_sources.news_api_key')
        )
        
        coinbase_config = config.get_coinbase_config()
        self.portfolio_manager = CoinbasePortfolioManager(
            api_key=coinbase_config['api_key'],
            api_secret=coinbase_config['api_secret'],
            passphrase=coinbase_config['passphrase'],
            sandbox=coinbase_config['sandbox']
        )
        
        risk_config = config.get_risk_config()
        self.risk_manager = RiskManager(
            max_position_size=risk_config['max_drawdown'],
            risk_per_trade=config.get('trading.risk_per_trade'),
            max_drawdown=risk_config['max_drawdown']
        )
        
        llm_config = config.get_llm_config()
        self.llm_advisor = LLMTradingAdvisor(
            api_key=llm_config['api_key'],
            model=llm_config['model']
        )
        
        # Trading configuration
        trading_config = config.get_trading_config()
        self.supported_coins = trading_config['supported_coins']
        self.min_trade_amount = trading_config['min_trade_amount']
        
        # System state
        self.running = False
        self.last_analysis_time = {}
        self.analysis_interval = 300  # 5 minutes
    
    async def run_analysis_cycle(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a complete analysis cycle for given symbols.
        
        Args:
            symbols: List of cryptocurrency symbols to analyze
            
        Returns:
            Analysis results and recommendations
        """
        if not symbols:
            symbols = self.supported_coins
        
        logger.info(f"Starting analysis cycle for symbols: {symbols}")
        
        try:
            # Step 1: Fetch and verify prices
            logger.info("Fetching price data...")
            raw_prices = await self.price_fetcher.get_prices(symbols)
            verified_prices = self.price_fetcher.verify_prices(raw_prices)
            
            if not verified_prices:
                logger.error("No verified prices available")
                return {'error': 'No price data available'}
            
            # Step 2: Get sentiment data
            logger.info("Analyzing sentiment...")
            sentiment_data = await self.sentiment_analyzer.get_sentiment_data(symbols)
            
            # Step 3: Get portfolio information
            logger.info("Retrieving portfolio data...")
            portfolio_balance = self.portfolio_manager.get_portfolio_balance()
            portfolio_value = self.portfolio_manager.calculate_portfolio_value(verified_prices)
            
            # Step 4: Generate trading recommendations
            recommendations = {}
            
            for symbol in symbols:
                if symbol not in verified_prices:
                    logger.warning(f"Skipping {symbol} - no price data")
                    continue
                
                logger.info(f"Generating recommendation for {symbol}")
                recommendation = await self._generate_recommendation(
                    symbol, verified_prices, sentiment_data, portfolio_balance, portfolio_value
                )
                recommendations[symbol] = recommendation
            
            # Step 5: Portfolio risk assessment
            risk_assessment = self.risk_manager.assess_portfolio_risk(
                portfolio_value.get('positions', {})
            )
            
            # Compile results
            analysis_results = {
                'timestamp': time.time(),
                'prices': verified_prices,
                'sentiment': sentiment_data,
                'portfolio': portfolio_value,
                'risk_assessment': risk_assessment,
                'recommendations': recommendations,
                'status': 'success'
            }
            
            logger.info("Analysis cycle completed successfully")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in analysis cycle: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e),
                'status': 'error'
            }
    
    async def _generate_recommendation(self, symbol: str, prices: Dict[str, float],
                                     sentiment_data: Dict[str, Dict],
                                     portfolio_balance: Dict[str, Dict],
                                     portfolio_value: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading recommendation for a specific symbol."""
        try:
            current_price = prices[symbol]
            
            # Get current position
            position_info = self.portfolio_manager.get_position_value(symbol, prices)
            
            # Calculate risk metrics
            # For demo, use 5% stop loss
            stop_loss_price = current_price * 0.95
            
            risk_metrics = self.risk_manager.calculate_position_size(
                portfolio_value['total_value_usd'],
                current_price,
                stop_loss_price,
                confidence=sentiment_data.get(symbol, {}).get('confidence', 0.5),
                method=config.get('risk_management.position_sizing_method', 'kelly')
            )
            
            # Calculate stop loss and take profit levels
            levels = self.risk_manager.calculate_stop_loss_take_profit(
                current_price, 'buy'
            )
            
            # Build context for LLM
            context = {
                'symbol': symbol,
                'price_data': {
                    'current_price': current_price,
                    'sources': list(prices.keys()),
                    'verified': True
                },
                'sentiment_data': sentiment_data.get(symbol, {}),
                'portfolio_data': portfolio_value,
                'risk_data': {
                    **risk_metrics,
                    'stop_loss_price': levels['stop_loss'],
                    'take_profit_price': levels['take_profit']
                },
                'position_info': position_info,
                'market_context': {
                    'trend': 'unknown',
                    'volatility': 'high',  # Crypto is typically high volatility
                    'volume': 'unknown'
                }
            }
            
            # Get LLM recommendation
            llm_recommendation = self.llm_advisor.get_trading_recommendation(context)
            
            # Combine all data
            recommendation = {
                'symbol': symbol,
                'current_price': current_price,
                'position_info': position_info,
                'risk_metrics': risk_metrics,
                'levels': levels,
                'sentiment': sentiment_data.get(symbol, {}),
                'llm_recommendation': llm_recommendation,
                'actionable': self._is_actionable(llm_recommendation, risk_metrics),
                'timestamp': time.time()
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendation for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _is_actionable(self, llm_recommendation: Dict, risk_metrics: Dict) -> bool:
        """Determine if a recommendation is actionable based on risk criteria."""
        # Check minimum trade amount
        position_value = risk_metrics.get('position_value_usd', 0)
        if position_value < self.min_trade_amount:
            return False
        
        # Check confidence threshold
        confidence = llm_recommendation.get('confidence', 0)
        if confidence < 60:  # Minimum 60% confidence
            return False
        
        # Check risk percentage
        risk_percentage = risk_metrics.get('max_loss_percentage', 0)
        if risk_percentage > config.get('trading.risk_per_trade', 0.02) * 100:
            return False
        
        return True
    
    async def execute_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading recommendation.
        
        Args:
            recommendation: Trading recommendation to execute
            
        Returns:
            Execution result
        """
        try:
            symbol = recommendation['symbol']
            llm_rec = recommendation['llm_recommendation']
            action = llm_rec['recommendation']
            
            if not recommendation.get('actionable', False):
                logger.info(f"Recommendation for {symbol} is not actionable")
                return {
                    'symbol': symbol,
                    'action': 'no_action',
                    'reason': 'Recommendation not actionable',
                    'status': 'skipped'
                }
            
            if action == 'HOLD':
                logger.info(f"Holding position for {symbol}")
                return {
                    'symbol': symbol,
                    'action': 'hold',
                    'status': 'success'
                }
            
            # Calculate order parameters
            risk_metrics = recommendation['risk_metrics']
            position_size = risk_metrics['position_size']
            
            if action == 'BUY':
                trading_pair = f"{symbol}-USD"
                logger.info(f"Placing buy order for {position_size} {symbol}")
                
                order_result = self.portfolio_manager.place_market_order(
                    trading_pair, 'buy', position_size
                )
                
                return {
                    'symbol': symbol,
                    'action': 'buy',
                    'size': position_size,
                    'order_result': order_result,
                    'status': 'executed' if order_result.get('id') else 'failed'
                }
            
            elif action == 'SELL':
                # Get current position size
                position_info = recommendation['position_info']
                available_quantity = position_info['available']
                
                if available_quantity > 0:
                    trading_pair = f"{symbol}-USD"
                    sell_size = min(available_quantity, position_size)
                    
                    logger.info(f"Placing sell order for {sell_size} {symbol}")
                    
                    order_result = self.portfolio_manager.place_market_order(
                        trading_pair, 'sell', sell_size
                    )
                    
                    return {
                        'symbol': symbol,
                        'action': 'sell',
                        'size': sell_size,
                        'order_result': order_result,
                        'status': 'executed' if order_result.get('id') else 'failed'
                    }
                else:
                    logger.info(f"No {symbol} position to sell")
                    return {
                        'symbol': symbol,
                        'action': 'no_sell',
                        'reason': 'No position to sell',
                        'status': 'skipped'
                    }
            
        except Exception as e:
            logger.error(f"Error executing recommendation for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'status': 'error'
            }
    
    async def run_continuous_trading(self, symbols: Optional[List[str]] = None,
                                   execute_trades: bool = False):
        """
        Run continuous trading loop.
        
        Args:
            symbols: Symbols to trade (default: all supported)
            execute_trades: Whether to actually execute trades
        """
        if not symbols:
            symbols = self.supported_coins
        
        self.running = True
        logger.info(f"Starting continuous trading for {symbols}")
        logger.info(f"Trade execution: {'ENABLED' if execute_trades else 'DISABLED'}")
        
        while self.running:
            try:
                # Run analysis cycle
                results = await self.run_analysis_cycle(symbols)
                
                if results.get('status') == 'success':
                    recommendations = results.get('recommendations', {})
                    
                    # Log summary
                    logger.info("=== Analysis Summary ===")
                    for symbol, rec in recommendations.items():
                        if 'error' not in rec:
                            llm_rec = rec.get('llm_recommendation', {})
                            action = llm_rec.get('recommendation', 'UNKNOWN')
                            confidence = llm_rec.get('confidence', 0)
                            actionable = rec.get('actionable', False)
                            
                            logger.info(f"{symbol}: {action} (confidence: {confidence}%, actionable: {actionable})")
                    
                    # Execute trades if enabled
                    if execute_trades:
                        logger.info("Executing trades...")
                        for symbol, recommendation in recommendations.items():
                            if 'error' not in recommendation:
                                execution_result = await self.execute_recommendation(recommendation)
                                logger.info(f"Execution result for {symbol}: {execution_result.get('status')}")
                
                # Wait before next cycle
                logger.info(f"Waiting {self.analysis_interval} seconds before next cycle...")
                await asyncio.sleep(self.analysis_interval)
                
            except KeyboardInterrupt:
                logger.info("Received stop signal")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
        
        self.running = False
        logger.info("Trading system stopped")
    
    def stop(self):
        """Stop the trading system."""
        self.running = False


if __name__ == "__main__":
    # Initialize and test the trading system
    trading_system = TradingSystem()
    
    async def main():
        # Run a single analysis cycle
        logger.info("Running single analysis cycle...")
        results = await trading_system.run_analysis_cycle(['BTC', 'ETH'])
        
        print("\n=== Analysis Results ===")
        print(json.dumps(results, indent=2, default=str))
    
    asyncio.run(main())