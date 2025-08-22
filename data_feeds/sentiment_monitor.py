import json
import os
from pathlib import Path
import time
import requests

CACHE_FILE = Path(__file__).parent.parent / "data" / "sentiment_cache.json"

def _retry_get(url, attempts=3, timeout=10):
    last_err = None
    for i in range(attempts):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            if i < attempts - 1:
                time.sleep(0.5 * (2 ** i))
    raise last_err

def fetch_lunarcrush_sentiment(symbol: str, api_key: str | None):
    if not api_key:
        raise ValueError("LUNARCRUSH_API_KEY is not set")
    url = f"https://api.lunarcrush.com/v2?data=assets&symbol={symbol}&key={api_key}"
    r = _retry_get(url)
    data = r.json()
    assets = data.get("data") or []
    if not assets:
        return None
    return assets[0].get("galaxy_score")

def _read_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def cache_sentiment(symbol: str, score):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = _read_cache()
    cache[symbol] = {"score": score}
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_sentiment(symbol: str) -> float | None:
    """
    Returns sentiment score for symbol.
    Attempts live fetch if LUNARCRUSH_API_KEY is set; otherwise falls back to cache.
    """
    api_key = os.getenv("LUNARCRUSH_API_KEY", "")
    if api_key:
        try:
            score = fetch_lunarcrush_sentiment(symbol, api_key)
            if score is not None:
                cache_sentiment(symbol, score)
                return score
        except Exception:
            # Fall back to cache below
            pass
    # Fallback: cached value
    cache = _read_cache()
    entry = cache.get(symbol)
    if entry:
        return entry.get("score")
    return None

if __name__ == "__main__":
    for sym in ["BTC", "ETH"]:
        try:
            score = get_sentiment(sym)
            print(sym, score)
        except Exception as e:
            print(f"Error fetching sentiment for {sym}: {e}")
