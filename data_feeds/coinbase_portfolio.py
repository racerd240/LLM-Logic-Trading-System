import os
from common.http import SESSION as http
from execution.coinbase_auth import sign_cb_request, now_ts_str

HTTP_TIMEOUT = 10

def _base_url() -> str:
    target = os.getenv("COINBASE_API_TARGET", "exchange").lower()
    if target != "exchange":
        # Only Exchange supported in this drop.
        raise RuntimeError("Set COINBASE_API_TARGET=exchange (Advanced Trade not enabled in this build).")
    return "https://api.exchange.coinbase.com"

def get_coinbase_portfolio():
    """
    Returns list of accounts (balances) from Coinbase Exchange.
    Requires API key/secret/passphrase with 'view' permission.
    """
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")  # base64
    api_passphrase = os.getenv("COINBASE_API_PASSPHRASE")
    if not (api_key and api_secret and api_passphrase):
        raise RuntimeError("Missing Coinbase API credentials in environment.")

    method = "GET"
    request_path = "/accounts"
    ts = now_ts_str()
    sig = sign_cb_request(api_secret, ts, method, request_path, None)

    headers = {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": sig,
        "CB-ACCESS-TIMESTAMP": ts,
        "CB-ACCESS-PASSPHRASE": api_passphrase,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    r = http.get(f"{_base_url()}{request_path}", headers=headers, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    import json
    try:
        portfolio = get_coinbase_portfolio()
        print(json.dumps(portfolio, indent=2))
    except Exception as e:
        print(f"Portfolio fetch failed: {e}")