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

def get_coinbase_portfolio():
    method = "GET"
    path = "/accounts"
    url = f"{BASE_URL}{path}"
    headers = _headers(method, path, "")
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    # Local dev convenience: load .env if present
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass
    print(json.dumps(get_coinbase_portfolio(), indent=2))
