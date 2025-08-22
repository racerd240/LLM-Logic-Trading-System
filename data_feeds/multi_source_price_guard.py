import os
import time
import requests

DEFAULT_TOLERANCE = 0.01  # 1%

def _retry_get(url, attempts=3, timeout=5):
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

def get_price_from_binance(symbol: str) -> float:
    # Binance quote is USDT
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    r = _retry_get(url)
    return float(r.json()["price"])

def get_price_from_coinbase(symbol: str) -> float:
    # Coinbase quote is USD
    url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/ticker"
    r = _retry_get(url)
    data = r.json()
    # Coinbase returns {"price": "xxxxx"} for ticker
    return float(data["price"])

def verify_prices(symbol: str, tolerance: float | None = None) -> float:
    tol = tolerance
    if tol is None:
        try:
            tol = float(os.getenv("PRICE_GUARD_TOLERANCE", DEFAULT_TOLERANCE))
        except Exception:
            tol = DEFAULT_TOLERANCE
    p1 = get_price_from_binance(symbol)
    p2 = get_price_from_coinbase(symbol)
    avg = (p1 + p2) / 2.0
    if avg == 0:
        raise ValueError(f"Zero average price for {symbol}")
    diff = abs(p1 - p2) / avg
    if diff > tol:
        raise ValueError(
            f"Price mismatch for {symbol}: Binance={p1}, Coinbase={p2}, diff={diff:.4%}, tol={tol:.2%}"
        )
    return avg

if __name__ == "__main__":
    symbols = ["BTC", "ETH"]
    while True:
        for s in symbols:
            try:
                print(s, verify_prices(s))
            except Exception as e:
                print(f"Error verifying prices for {s}: {e}")
        time.sleep(5)
