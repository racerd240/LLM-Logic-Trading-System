# LLM Logic Trading System

A sophisticated cryptocurrency trading system that combines Large Language Model (LLM) intelligence with traditional technical analysis, risk management, and real-time market data to make informed trading decisions.

## Features

### 🔄 Multi-Source Price Fetching
- Fetches cryptocurrency prices from multiple sources (CoinGecko, Coinbase)
- Verifies price accuracy across sources to prevent manipulation
- Intelligent caching to reduce API calls

### 📊 Sentiment Analysis
- Analyzes market sentiment from news sources
- Processes social media sentiment (extensible framework)
- Provides confidence scores for sentiment reliability

### 💼 Portfolio Management
- Integrates with Coinbase Pro API for portfolio management
- Real-time position tracking and valuation
- Supports both sandbox and live trading environments

### ⚖️ Advanced Risk Management
- Multiple position sizing algorithms (Fixed Risk, Kelly Criterion, Volatility-based)
- Automatic stop-loss and take-profit calculation
- Portfolio-wide risk assessment and concentration analysis

### 🤖 LLM-Powered Decision Making
- Leverages GPT-4 for comprehensive market analysis
- Considers price data, sentiment, portfolio status, and risk metrics
- Provides detailed reasoning for each trading recommendation

### 🛡️ Safety Features
- Configurable risk limits and position sizing
- Dry-run mode for testing strategies
- Comprehensive logging and error handling

## Installation

### Prerequisites
- Python 3.10 or 3.11 (recommended)
- pip package manager
- Git

### Quickstart Setup

⚠️ **Safety First**: Always start with sandbox mode and paper trading before risking real money.

1. **Clone and setup environment**:
```bash
git clone https://github.com/racerd240/LLM-Logic-Trading-System.git
cd LLM-Logic-Trading-System

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
# Copy environment template and edit with your API keys
cp .env.example .env
nano .env  # or use your preferred editor
```

3. **Test the setup**:
```bash
# Test with demo mode (no API keys needed)
python demo.py

# Test with real APIs in safe analyze mode
python main.py --mode analyze --symbols BTC ETH
```

### Required API Keys

1. **OpenAI API Key** (Required)
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Add your key to `.env` as `OPENAI_API_KEY`

2. **Coinbase Pro API** (Required for trading)
   - Create API credentials at [Coinbase Pro](https://pro.coinbase.com/)
   - Enable permissions: View ✅, Trade ✅, Transfer ❌
   - Add to `.env`: `COINBASE_API_KEY`, `COINBASE_API_SECRET`, `COINBASE_PASSPHRASE`
   - **Important**: Set `COINBASE_USE_SANDBOX=true` for testing

3. **News API Key** (Optional but recommended)
   - Get free key at [NewsAPI.org](https://newsapi.org/)
   - Add to `.env` as `NEWS_API_KEY`

## Usage

### 🚀 Quick Start (Safe Development Workflow)

1. **Start with demo mode** (no API keys required):
```bash
python demo.py
```

2. **Test with analyze mode** (read-only):
```bash
python main.py --mode analyze --symbols BTC ETH
```

3. **Try dry-run mode** (simulated trading):
```bash
python main.py --mode test --symbols BTC ETH
```

4. **Sandbox trading** (fake money on real exchange):
```bash
# Ensure COINBASE_USE_SANDBOX=true in .env
python main.py --mode continuous --symbols BTC ETH
```

5. **Live trading** (real money - use extreme caution):
```bash
# Set COINBASE_USE_SANDBOX=false in .env
python main.py --mode continuous --symbols BTC ETH --execute
```

### Operating Modes

| Mode | Description | Safety Level | API Keys Required |
|------|-------------|--------------|-------------------|
| `demo` | Mock data demonstration | ✅ Safe | None |
| `analyze` | Read-only market analysis | ✅ Safe | OpenAI, Coinbase (read-only) |
| `test` | Dry-run with real data | ✅ Safe | OpenAI, Coinbase |
| `continuous` | Live monitoring (sandbox) | ⚠️ Caution | All APIs |
| `continuous --execute` | Live trading | ❌ High Risk | All APIs |

### Safety Guidelines

- **Always start with sandbox trading** (`COINBASE_USE_SANDBOX=true`)
- **Use small amounts** you can afford to lose completely
- **Monitor the system closely** during initial runs
- **Understand the risks** of automated trading
- **Have emergency stop procedures** ready
- **Read the full documentation** in `docs/RUNBOOK.md`

### Command Examples

```bash
# Safe exploration and testing
python demo.py                                    # Demo with mock data
python main.py --mode analyze --symbols BTC ETH   # Read-only analysis
python main.py --mode test                        # System validation

# Sandbox trading (recommended before live)
python main.py --mode continuous --symbols BTC    # Sandbox monitoring
python main.py --mode continuous --symbols BTC ETH # Multiple coins

# Live trading (use extreme caution)
python main.py --mode continuous --symbols BTC --execute
```

## Configuration

### Trading Configuration (`config/trading_config.json`)

```json
{
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
    }
}
```

### Environment Variables (`.env`)

Key configuration options:
- `COINBASE_SANDBOX=true` - Use sandbox for testing
- `MAX_POSITION_SIZE=0.1` - Maximum 10% of portfolio per position
- `RISK_PER_TRADE=0.02` - Risk 2% of portfolio per trade
- `LOG_LEVEL=INFO` - Logging verbosity

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Portfolio     │    │   Risk Manager  │
│                 │    │   Manager       │    │                 │
│ • Price Fetch   │    │ • Coinbase API  │    │ • Position Size │
│ • Sentiment     │    │ • Balance Track │    │ • Stop Loss     │
│ • News Analysis │    │ • Order Exec    │    │ • Risk Assessment│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                 ┌─────────────────────────────┐
                 │      LLM Trading Advisor    │
                 │                             │
                 │ • Market Analysis           │
                 │ • Decision Making           │
                 │ • Strategy Recommendations  │
                 └─────────────────────────────┘
                                 │
                 ┌─────────────────────────────┐
                 │     Trading System          │
                 │                             │
                 │ • Orchestration             │
                 │ • Execution Engine          │
                 │ • Monitoring & Logging      │
                 └─────────────────────────────┘
```

## Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Or run basic component tests:
```bash
python tests/test_trading_system.py
```

## Risk Management

This system implements multiple layers of risk management:

### Position Sizing
- **Fixed Risk**: Risk a fixed percentage of portfolio per trade
- **Kelly Criterion**: Mathematically optimal position sizing
- **Volatility-based**: Adjust size based on market volatility

### Portfolio Protection
- Maximum position size limits (default: 10% per position)
- Portfolio-wide exposure limits
- Correlation analysis and concentration risk monitoring

### Trade Execution Safety
- Mandatory stop-loss levels
- Take-profit targets with favorable risk/reward ratios
- Minimum trade amount thresholds

## Logging and Monitoring

The system provides comprehensive logging:
- All API calls and responses
- Trading decisions and reasoning
- Risk calculations and portfolio changes
- Error handling and system health

Logs are stored in `logs/trading_system.log` with automatic rotation.

## Development

### Project Structure
```
LLM-Logic-Trading-System/
├── src/
│   ├── data_sources/        # Price and sentiment data
│   ├── portfolio/           # Portfolio management
│   ├── risk/               # Risk management
│   ├── llm/                # LLM integration
│   ├── utils/              # Utilities and config
│   └── trading_system.py   # Main orchestrator
├── config/                 # Configuration files
├── tests/                  # Test suite
├── main.py                 # Entry point
└── requirements.txt        # Dependencies
```

### Adding New Features

1. **New Data Sources**: Extend `src/data_sources/`
2. **Additional Exchanges**: Extend `src/portfolio/`
3. **New LLM Providers**: Extend `src/llm/`
4. **Risk Models**: Extend `src/risk/`

## Disclaimer

⚠️ **Important Warning**: This software is for educational and research purposes. Cryptocurrency trading involves substantial risk and may result in significant financial losses. 

- Start with small amounts and sandbox environments
- Never risk more than you can afford to lose
- Understand the risks of automated trading
- Monitor the system closely during operation
- The developers are not responsible for any financial losses

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Review the documentation
- Check the test suite for usage examples