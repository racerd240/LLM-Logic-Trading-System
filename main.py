import json
import os
from pathlib import Path

from data_feeds.coinbase_portfolio import get_coinbase_portfolio
from context.decision_context_builder import build_context
from llm.decision_engine import query_llm

def _load_env():
    try:
        from dotenv import load_dotenv  # type: ignore
        # Load .env from repo root if present
        root = Path(__file__).parent
        env_path = root / ".env"
        load_dotenv(dotenv_path=env_path if env_path.exists() else None)
    except Exception:
        # dotenv is optional in deployed environments
        pass

def _fallback_symbols():
    # fallback to observation_list.json if portfolio fails or empty
    obs = Path(__file__).parent / "data" / "observation_list.json"
    if obs.exists():
        try:
            data = json.loads(obs.read_text())
            return data.get("symbols") or []
        except Exception:
            return []
    return []

if __name__ == "__main__":
    _load_env()

    symbols = []
    try:
        portfolio = get_coinbase_portfolio()
        # Portfolio API returns a list of accounts; filter those with balance > 0
        symbols = [
            p["currency"]
            for p in portfolio
            if p.get("currency") and float(p.get("balance", 0) or 0) > 0
        ]
    except Exception as e:
        print(f"Warning: could not fetch Coinbase portfolio: {e}")

    if not symbols:
        symbols = _fallback_symbols()

    if not symbols:
        raise SystemExit("No symbols available from portfolio or observation_list.json")

    context = build_context(symbols)
    decision = query_llm(context)
    print(json.dumps(decision, indent=2))
