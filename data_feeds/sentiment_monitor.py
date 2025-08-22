import json
import os
import time
from pathlib import Path
from common.http import SESSION as http

HTTP_TIMEOUT = 10
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "sentiment_cache.json"

def fetch_lunarcrush_sentiment(symbol: str, api_key: str | None):
    """
    Returns a float 'galaxy_score' if available, else None.
    Works defensively against schema changes.
    """
    if not api_key:
        return None
    url = f"https://api.lunarcrush.com/v2?data=assets&symbol={symbol.upper()}&key={api_key}"
    r = http.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    try:
        items = data.get("data") or data.get("results") or data.get("assets") or []
        if not items:
            return None
        first = items[0]
        score = first.get("galaxy_score") or first.get("galaxyScore") or first.get("score")
        return float(score) if score is not None else None
    except Exception:
        return None

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
    cache[symbol.upper()] = {"score": score, "ts": int(time.time())}
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def get_sentiment(symbol: str) -> float | None:
    """
    Returns sentiment score for symbol.
    Attempts live fetch if LUNARCRUSH_API_KEY is set; otherwise falls back to cache.
    """
    api_key = os.getenv("LUNARCRUSH_API_KEY", "")
    score = None
    if api_key:
        try:
            score = fetch_lunarcrush_sentiment(symbol, api_key)
            if score is not None:
                cache_sentiment(symbol, score)
                return score
        except Exception:
            pass
    cache = _read_cache()
    entry = cache.get(symbol.upper())
    if entry:
        return entry.get("score")
    return None

if __name__ == "__main__":
    for sym in ["BTC", "ETH"]:
        try:
            s = get_sentiment(sym)
            print(sym, s)
        except Exception as e:
            print(f"{sym} sentiment error: {e}")