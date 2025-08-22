# LLM Logic Trading System - Operations Runbook

## Prerequisites

### System Requirements
- Python 3.10 or 3.11
- Minimum 4GB RAM
- Stable internet connection
- API access to required services

### Required API Keys and Setup

1. **OpenAI API** (Required)
   - Create account at [OpenAI Platform](https://platform.openai.com/)
   - Generate API key in Account Settings > API Keys
   - Recommended models: GPT-4 (better accuracy) or GPT-3.5-turbo (faster/cheaper)

2. **Coinbase Pro API** (Required for live trading)
   - Create account at [Coinbase Pro](https://pro.coinbase.com/)
   - Enable API access in Settings > API
   - Create API key with permissions:
     - View: ✅ (for portfolio data)
     - Trade: ✅ (for placing orders) 
     - Transfer: ❌ (not needed for trading)
   - **IMPORTANT**: Save the passphrase - it cannot be retrieved later

3. **News API** (Optional but recommended)
   - Free tier available at [NewsAPI.org](https://newsapi.org/)
   - 1000 requests/day limit on free tier

## Environment Setup

### 1. Initial Setup
```bash
# Clone repository
git clone https://github.com/racerd240/LLM-Logic-Trading-System.git
cd LLM-Logic-Trading-System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

### 3. Environment Variables Description

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM trading decisions |
| `COINBASE_API_KEY` | Yes | Coinbase Pro API key |
| `COINBASE_API_SECRET` | Yes | Coinbase Pro API secret (base64 encoded) |
| `COINBASE_PASSPHRASE` | Yes | Coinbase Pro API passphrase |
| `COINBASE_USE_SANDBOX` | Yes | Set to `true` for testing, `false` for live trading |
| `NEWS_API_KEY` | No | News API key for sentiment analysis |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |
| `LLM_MODEL` | No | Override LLM model (default: gpt-4) |

## Operating Modes

### 1. Analyze Mode (Read-only)
**Recommended for first-time users**
```bash
python main.py --mode analyze --symbols BTC ETH
```
- Analyzes market conditions without trading
- Safe way to test API connections
- Shows what the system would recommend

### 2. Test Mode (Dry-run)
**Recommended before live trading**
```bash
python main.py --mode test --symbols BTC ETH
```
- Simulates trading with fake money
- Tests all systems end-to-end
- No real trades executed
- Validates configuration and logic

### 3. Continuous Mode (Live Trading)
**⚠️ Only use after thorough testing**
```bash
# Sandbox trading (safe)
COINBASE_USE_SANDBOX=true python main.py --mode continuous --symbols BTC ETH

# Live trading (real money at risk)
COINBASE_USE_SANDBOX=false python main.py --mode continuous --symbols BTC ETH --execute
```

### 4. Demo Mode
```bash
python demo.py
```
- Runs component demos with mock data
- Good for understanding system capabilities
- No API keys required

## Expected Output and Interpretation

### Analysis Results
The system provides detailed analysis including:

```json
{
  "symbol": "BTC",
  "recommendation": "BUY|SELL|HOLD",
  "confidence": 75,
  "risk_level": "LOW|MEDIUM|HIGH",
  "reasoning": "Market analysis explanation...",
  "position_size": 0.025,
  "stop_loss": 42500.00,
  "take_profit": 47000.00
}
```

### Confidence Levels
- **90-100%**: Very high confidence, strong signals
- **70-89%**: High confidence, good entry points
- **60-69%**: Medium confidence, proceed with caution
- **40-59%**: Low confidence, consider waiting
- **Below 40%**: Very low confidence, avoid trading

### Risk Levels
- **LOW**: Safe conditions, low volatility
- **MEDIUM**: Normal market conditions
- **HIGH**: Volatile market, increased risk

## Troubleshooting

### API Connection Issues

**Problem**: "Coinbase API authentication failed"
```
Solution:
1. Verify API key, secret, and passphrase in .env
2. Check API permissions include "View" and "Trade"
3. Ensure secret is base64 encoded as provided by Coinbase
4. Test with sandbox first (COINBASE_USE_SANDBOX=true)
```

**Problem**: "OpenAI API rate limit exceeded"
```
Solution:
1. Check your OpenAI account billing and limits
2. Reduce analysis frequency
3. Consider upgrading OpenAI plan
4. Switch to gpt-3.5-turbo for faster/cheaper requests
```

**Problem**: "News API quota exceeded"
```
Solution:
1. Check NewsAPI.org dashboard for usage limits
2. Consider upgrading to paid plan
3. System continues without news sentiment (graceful degradation)
```

### Trading Issues

**Problem**: "Insufficient funds for trade"
```
Solution:
1. Check account balances in Coinbase Pro
2. Ensure funds are transferred to Pro trading account
3. Verify minimum trade amounts (usually $10-25)
4. Check if funds are tied up in pending orders
```

**Problem**: "Position size too small"
```
Solution:
1. Increase portfolio size or reduce supported coins
2. Lower min_trade_amount in config
3. Check risk_per_trade setting (may be too conservative)
```

### System Behavior Issues

**Problem**: "System keeps recommending HOLD"
```
Possible causes:
1. Market conditions genuinely warrant holding
2. Risk settings too conservative
3. Confidence thresholds too high
4. Check sentiment data availability

Solution:
1. Review risk_management settings in config
2. Check log files for decision reasoning
3. Run in analyze mode to understand recommendations
```

**Problem**: "Unexpected price differences"
```
Solution:
1. Check PRICE_GUARD_TOLERANCE setting
2. Verify internet connection stability
3. Check if exchanges are experiencing issues
4. Review price source configurations
```

## Graceful Fallbacks

The system includes several fallback mechanisms:

1. **Missing News API**: Uses basic sentiment scoring
2. **Price Source Failure**: Falls back to remaining sources
3. **LLM API Issues**: Uses conservative default recommendations
4. **Coinbase API Temporary Issues**: Retries with exponential backoff

## Safety Procedures

### Emergency Stop
```bash
# Immediate stop
Ctrl+C  # Stops the running process

# Review open positions
python -c "from data_feeds.coinbase_portfolio import get_coinbase_portfolio; print(get_coinbase_portfolio())"
```

### Pre-Live Trading Checklist
- [ ] Tested in analyze mode successfully
- [ ] Tested in test/dry-run mode successfully  
- [ ] Verified all API keys and permissions
- [ ] Started with small amounts in sandbox
- [ ] Reviewed and understood risk settings
- [ ] Set up monitoring and alerts
- [ ] Prepared emergency stop procedures
- [ ] Backed up configuration files

### Daily Operations
1. Check system logs for errors or warnings
2. Verify API rate limit usage
3. Review overnight trading decisions
4. Monitor portfolio performance and risk metrics
5. Check for any pending or failed orders

## Monitoring and Alerts

### Log Files
- Location: `logs/trading_system.log`
- Rotation: 10MB files, 1 week retention
- Levels: ERROR, WARNING, INFO, DEBUG

### Key Metrics to Monitor
- Portfolio value and performance
- Risk exposure levels
- API usage and rate limits
- Success/failure rates of trades
- System uptime and errors

## Release and Deployment

### Version Tagging
```bash
# After testing new features
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Pre-deployment Verification
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Configuration reviewed
- [ ] Backup procedures tested
- [ ] Rollback plan prepared

### Post-deployment Verification
- [ ] System starts correctly
- [ ] API connections successful
- [ ] Basic functionality working
- [ ] Monitoring systems active
- [ ] First trades execute properly

## Getting Help

1. **Check Logs**: Always review `logs/trading_system.log` first
2. **Test in Isolation**: Use analyze mode to test individual components
3. **Community**: Review GitHub issues and discussions
4. **Documentation**: Refer to README.md for additional context

## Security Best Practices

- Never commit `.env` file to source control
- Regularly rotate API keys
- Use sandbox for all testing
- Monitor account activity regularly
- Keep system and dependencies updated
- Use dedicated trading account with limited funds
- Enable two-factor authentication on all accounts