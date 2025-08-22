import json
from typing import Sequence, Dict, Any
from data_feeds.multi_source_price_guard import verify_prices
from data_feeds.sentiment_monitor import get_sentiment  # uses cache fallback

def build_context(symbols: Sequence[str]) -> str:
    """
    Builds a compact JSON context with verified prices (Binance vs Coinbase)
    and optional sentiment (with cache fallback).
    """
    context: Dict[str, Dict[str, Any]] = {}
    for sym in symbols:
        entry: Dict[str, Any] = {}
        # Price verification
        try:
            b, c, avg = verify_prices(sym)
            entry.update({"price": avg, "binance": b, "coinbase": c})
        except Exception as e:
            entry.update({"price": None, "error": f"price_verification_failed: {e}"})
        # Optional sentiment
        try:
            score = get_sentiment(sym)
            if score is not None:
                entry["sentiment"] = {"lunarcrush_galaxy_score": score}
        except Exception as e:
            entry["sentiment_error"] = str(e)
        context[sym.upper()] = entry
    return json.dumps(context, separators=(",", ":"), ensure_ascii=False)