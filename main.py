import json
from pathlib import Path
from dotenv import load_dotenv

from data_feeds.coinbase_portfolio import get_coinbase_portfolio
from context.decision_context_builder import build_context

OBS_LIST_PATH = Path(__file__).resolve().parent / "data" / "observation_list.json"

def load_observation_symbols():
    if OBS_LIST_PATH.exists():
        with open(OBS_LIST_PATH, "r") as f:
            data = json.load(f)
            syms = data.get("symbols") or []
            return [s.upper() for s in syms if isinstance(s, str) and s.strip()]
    return ["BTC", "ETH"]

def portfolio_symbols_or_fallback():
    try:
        portfolio = get_coinbase_portfolio()
        symbols = []
        for p in portfolio:
            try:
                cur = p.get("currency")
                bal = float(p.get("balance", 0))
                if cur and bal > 0:
                    symbols.append(cur.upper())
            except Exception:
                continue
        # Keep majors if present; else fallback to observation list
        symbols = [s for s in symbols if s in {"BTC", "ETH"}] or load_observation_symbols()
        return symbols
    except Exception:
        return load_observation_symbols()

def main():
    # Load environment from .env (if present)
    load_dotenv(override=False)

    symbols = portfolio_symbols_or_fallback()
    context = build_context(symbols)
    print("Context:", context)

    # Optional: query LLM (safe to skip if endpoint unset)
    try:
        from llm.decision_engine import query_llm
        decision = query_llm(context)
        print("LLM Decision:")
        print(json.dumps(decision, indent=2))
    except Exception as e:
        print(f"LLM call failed: {e}")

if __name__ == "__main__":
    main()