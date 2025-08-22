import base64
import hashlib
import hmac
import json
import os
import time
import requests

BASE_URL = "https://api.exchange.coinbase.com"
USER_AGENT = "LLM-Logic-Trading-System/1.0"

def _cb_sign(secret_b64: str, timestamp: str, method: str, request_path: str, body: str) -> str:
    key = base64.b64decode(secret_b64)
    prehash = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(key, prehash.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(signature).decode("utf-8")

def _headers(method: str, request_path: str, body_json: str = "") -> dict:
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    passphrase = os.getenv("COINBASE_API_PASSPHRASE")
    if not api_key or not api_secret or not passphrase:
        raise ValueError("Missing Coinbase API credentials: ensure COINBASE_API_KEY, COINBASE_API_SECRET, and COINBASE_API_PASSPHRASE are set")
    ts = str(int(time.time()))
    sign = _cb_sign(api_secret, ts, method.upper(), request_path, body_json or "")
    return {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": sign,
        "CB-ACCESS-TIMESTAMP": ts,
        "CB-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

def place_order(product_id, side, size, price=None, order_type="limit"):
    """
    Places an order on Coinbase Exchange.
    order_type: "limit" or "market"
    For market, omit price.
    """
    method = "POST"
    path = "/orders"
    order = {
        "product_id": product_id,
        "side": side,
        "size": str(size),
        "type": order_type,
    }
    if price is not None and order_type == "limit":
        order["price"] = str(price)

    body_json = json.dumps(order, separators=(",", ":"))
    headers = _headers(method, path, body_json)
    r = requests.post(f"{BASE_URL}{path}", headers=headers, data=body_json, timeout=20)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    pass
