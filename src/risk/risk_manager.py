"""
Risk management and position sizing module.
"""
import numpy as np
import math
from typing import Dict, List, Optional, Tuple
from loguru import logger
import json


class RiskManager:
    """Calculates position sizes and manages trading risk."""
    
    def __init__(self, max_position_size: float = 0.1, 
                 risk_per_trade: float = 0.02,
                 max_drawdown: float = 0.15):
        self.max_position_size = max_position_size  # Maximum 10% of portfolio per position
        self.risk_per_trade = risk_per_trade  # Risk 2% of portfolio per trade
        self.max_drawdown = max_drawdown  # Maximum 15% drawdown
        
        # Historical performance tracking
        self.trade_history = []
        self.current_drawdown = 0.0
    
    def calculate_position_size(self, 
                              portfolio_value: float,
                              entry_price: float,
                              stop_loss_price: float,
                              confidence: float = 1.0,
                              method: str = "fixed_risk") -> Dict[str, float]:
        """
        Calculate optimal position size based on risk management parameters.
        
        Args:
            portfolio_value: Total portfolio value in USD
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            confidence: Confidence level (0.0 to 1.0)
            method: Position sizing method ('fixed_risk', 'kelly', 'volatility')
            
        Returns:
            Dict with position sizing information
        """
        if entry_price <= 0 or stop_loss_price <= 0:
            logger.error("Invalid entry or stop loss price")
            return self._get_zero_position()
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        risk_percentage = risk_per_share / entry_price
        
        # Calculate position size based on method
        if method == "fixed_risk":
            position_size = self._calculate_fixed_risk_size(
                portfolio_value, risk_per_share, confidence
            )
        elif method == "kelly":
            position_size = self._calculate_kelly_size(
                portfolio_value, entry_price, risk_percentage, confidence
            )
        elif method == "volatility":
            position_size = self._calculate_volatility_size(
                portfolio_value, entry_price, risk_percentage, confidence
            )
        else:
            logger.error(f"Unknown position sizing method: {method}")
            return self._get_zero_position()
        
        # Apply maximum position size constraint
        max_position_value = portfolio_value * self.max_position_size
        max_shares = max_position_value / entry_price
        
        position_size = min(position_size, max_shares)
        
        # Calculate position metrics
        position_value = position_size * entry_price
        portfolio_percentage = (position_value / portfolio_value) * 100
        max_loss = position_size * risk_per_share
        max_loss_percentage = (max_loss / portfolio_value) * 100
        
        return {
            'position_size': position_size,
            'position_value_usd': position_value,
            'portfolio_percentage': portfolio_percentage,
            'max_loss_usd': max_loss,
            'max_loss_percentage': max_loss_percentage,
            'risk_per_share': risk_per_share,
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price,
            'confidence_adjusted': confidence,
            'method_used': method
        }
    
    def _calculate_fixed_risk_size(self, portfolio_value: float, 
                                 risk_per_share: float, 
                                 confidence: float) -> float:
        """Calculate position size using fixed risk method."""
        # Risk amount is a percentage of portfolio value
        risk_amount = portfolio_value * self.risk_per_trade * confidence
        
        # Position size is risk amount divided by risk per share
        if risk_per_share > 0:
            return risk_amount / risk_per_share
        return 0
    
    def _calculate_kelly_size(self, portfolio_value: float, 
                            entry_price: float,
                            risk_percentage: float,
                            confidence: float) -> float:
        """Calculate position size using Kelly Criterion."""
        # Simplified Kelly formula: f = (bp - q) / b
        # where f = fraction of capital to wager
        # b = odds of winning (reward/risk ratio)
        # p = probability of winning
        # q = probability of losing (1-p)
        
        # Use confidence as probability of winning
        p = min(max(confidence, 0.1), 0.9)  # Clamp between 0.1 and 0.9
        q = 1 - p
        
        # Assume 2:1 reward to risk ratio
        reward_risk_ratio = 2.0
        b = reward_risk_ratio
        
        # Kelly fraction
        kelly_fraction = (b * p - q) / b
        
        # Apply Kelly fraction but cap it at our max position size
        kelly_fraction = max(0, min(kelly_fraction, self.max_position_size))
        
        # Further reduce by risk per trade constraint
        final_fraction = min(kelly_fraction, self.risk_per_trade / risk_percentage)
        
        position_value = portfolio_value * final_fraction
        return position_value / entry_price
    
    def _calculate_volatility_size(self, portfolio_value: float,
                                 entry_price: float,
                                 risk_percentage: float,
                                 confidence: float) -> float:
        """Calculate position size based on volatility."""
        # This is a simplified volatility-based sizing
        # In practice, you would use historical volatility data
        
        # Assume base volatility of 5% daily for crypto
        base_volatility = 0.05
        
        # Adjust for current risk percentage
        volatility_factor = base_volatility / max(risk_percentage, 0.01)
        
        # Scale by confidence
        adjusted_factor = volatility_factor * confidence
        
        # Calculate position size
        target_risk = portfolio_value * self.risk_per_trade
        position_value = target_risk * adjusted_factor
        
        return position_value / entry_price
    
    def calculate_stop_loss_take_profit(self, entry_price: float,
                                      side: str,
                                      atr: Optional[float] = None,
                                      volatility: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate stop loss and take profit levels.
        
        Args:
            entry_price: Entry price for the position
            side: 'buy' or 'sell'
            atr: Average True Range (optional)
            volatility: Price volatility (optional)
            
        Returns:
            Dict with stop loss and take profit levels
        """
        # Use ATR if available, otherwise use default percentages
        if atr and atr > 0:
            stop_distance = atr * 2  # 2 ATR stop loss
            profit_distance = atr * 4  # 4 ATR take profit (2:1 R/R)
        else:
            # Default crypto percentages
            stop_percentage = 0.05  # 5% stop loss
            profit_percentage = 0.10  # 10% take profit
            
            stop_distance = entry_price * stop_percentage
            profit_distance = entry_price * profit_percentage
        
        if side.lower() == 'buy':
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + profit_distance
        else:  # sell
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - profit_distance
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'stop_distance': stop_distance,
            'profit_distance': profit_distance,
            'risk_reward_ratio': profit_distance / stop_distance
        }
    
    def assess_portfolio_risk(self, positions: Dict[str, Dict],
                            correlations: Optional[Dict] = None) -> Dict[str, float]:
        """
        Assess overall portfolio risk including correlation effects.
        
        Args:
            positions: Current portfolio positions
            correlations: Correlation matrix between assets (optional)
            
        Returns:
            Portfolio risk assessment
        """
        total_exposure = 0
        crypto_exposure = 0
        max_single_position = 0
        
        position_sizes = []
        
        for symbol, position in positions.items():
            if symbol == 'USD':
                continue
            
            percentage = position.get('percentage', 0)
            position_sizes.append(percentage)
            
            crypto_exposure += percentage
            max_single_position = max(max_single_position, percentage)
        
        total_exposure = crypto_exposure
        
        # Calculate concentration risk
        if len(position_sizes) > 0:
            # Herfindahl Index for concentration
            concentration_index = sum(p**2 for p in position_sizes) / 100
        else:
            concentration_index = 0
        
        # Simple correlation adjustment (if correlations provided)
        if correlations and len(position_sizes) > 1:
            # This is a simplified correlation adjustment
            avg_correlation = 0.7  # Assume high correlation in crypto markets
            correlation_adjustment = 1 + (avg_correlation * (len(position_sizes) - 1) / len(position_sizes))
            adjusted_risk = crypto_exposure * correlation_adjustment
        else:
            adjusted_risk = crypto_exposure
        
        risk_level = "Low"
        if adjusted_risk > 80:
            risk_level = "Very High"
        elif adjusted_risk > 60:
            risk_level = "High"
        elif adjusted_risk > 40:
            risk_level = "Medium"
        
        return {
            'total_crypto_exposure': crypto_exposure,
            'max_single_position': max_single_position,
            'concentration_index': concentration_index,
            'adjusted_risk': adjusted_risk,
            'risk_level': risk_level,
            'within_limits': (max_single_position <= self.max_position_size * 100 and
                            crypto_exposure <= 90),  # Max 90% in crypto
            'recommendations': self._get_risk_recommendations(
                crypto_exposure, max_single_position, concentration_index
            )
        }
    
    def _get_risk_recommendations(self, crypto_exposure: float,
                                max_position: float,
                                concentration: float) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if crypto_exposure > 80:
            recommendations.append("Consider reducing overall crypto exposure")
        
        if max_position > self.max_position_size * 100:
            recommendations.append(f"Largest position exceeds {self.max_position_size*100}% limit")
        
        if concentration > 0.3:
            recommendations.append("Portfolio is highly concentrated - consider diversification")
        
        if len(recommendations) == 0:
            recommendations.append("Portfolio risk levels are within acceptable limits")
        
        return recommendations
    
    def _get_zero_position(self) -> Dict[str, float]:
        """Return zero position sizing."""
        return {
            'position_size': 0,
            'position_value_usd': 0,
            'portfolio_percentage': 0,
            'max_loss_usd': 0,
            'max_loss_percentage': 0,
            'risk_per_share': 0,
            'entry_price': 0,
            'stop_loss_price': 0,
            'confidence_adjusted': 0,
            'method_used': 'none'
        }


if __name__ == "__main__":
    # Test the risk manager
    risk_manager = RiskManager()
    
    # Test position sizing
    portfolio_value = 10000
    entry_price = 45000
    stop_loss_price = 43000
    confidence = 0.8
    
    position_info = risk_manager.calculate_position_size(
        portfolio_value, entry_price, stop_loss_price, confidence, "kelly"
    )
    print("Position sizing:", json.dumps(position_info, indent=2))
    
    # Test stop loss/take profit calculation
    levels = risk_manager.calculate_stop_loss_take_profit(entry_price, 'buy')
    print("Stop/Profit levels:", json.dumps(levels, indent=2))
    
    # Test portfolio risk assessment
    mock_positions = {
        'BTC': {'percentage': 30},
        'ETH': {'percentage': 25},
        'ADA': {'percentage': 10}
    }
    risk_assessment = risk_manager.assess_portfolio_risk(mock_positions)
    print("Risk assessment:", json.dumps(risk_assessment, indent=2))