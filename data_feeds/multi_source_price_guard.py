import os
import time
import math
from typing import Tuple
from common.http import SESSION as http

HTTP_TIMEOUT = 8
REL_TOL_DEFAULT = 0.005  # 0.5%

def _rel_tol() -> float:
    try:
        return float(os.getenv("PRICE_GUARD_TOLERANCE", REL_TOL_DEFAULT))
    except Exception:
        return REL_TOL_DEFAULT

def _binance_symbol(symbol: str) -> str:
    return f"{symbol.upper()}USDT"

def _coinbase_product(symbol: str) -> str:
    return f"{symbol.upper()}-USD"

def get_price_from_binance(symbol: str) -> float:
    sym = _binance_symbol(symbol)
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={sym}"
    r = http.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    price = data.get("price")
    if price is None:
        raise ValueError(f"Binance bad payload: {data}")
    return float(price)

def get_price_from_coinbase(symbol: str) -> float:
    product = _coinbase_product(symbol)
    url = f"https://api.exchange.coinbase.com/products/{product}/ticker"
    r = http.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    price = data.get("price")
    if price is None:
        raise ValueError(f"Coinbase bad payload: {data}")
    return float(price)

def verify_prices(symbol: str) -> Tuple[float, float, float]:
    """
    Returns (binance_price, coinbase_price, avg_price).
    Raises ValueError if divergence > tolerance or avg is invalid.
    """
    p1 = get_price_from_binance(symbol)
    p2 = get_price_from_coinbase(symbol)
    avg = (p1 + p2) / 2.0
    if avg == 0 or math.isinf(avg) or math.isnan(avg):
        raise ValueError(f"Invalid average price for {symbol}: {avg}")
    if abs(p1 - p2) / avg > _rel_tol():
        raise ValueError(f"Price mismatch for {symbol}: Binance={p1}, Coinbase={p2}")
    return p1, p2, avg

if __name__ == "__main__":
    symbols = ["BTC", "ETH"]
    while True:
        for s in symbols:
            try:
                b, c, avg = verify_prices(s)
                print(f"{s}: binance={b:.2f} coinbase={c:.2f} avg={avg:.2f}")
            except Exception as e:
                print(f"{s}: price verification failed: {e}")
        time.sleep(5)