import json
import os
from common.http import SESSION as http
from execution.coinbase_auth import sign_cb_request, now_ts_str

HTTP_TIMEOUT = 15

def _base_url() -> str:
    target = os.getenv("COINBASE_API_TARGET", "exchange").lower()
    if target != "exchange":
        # Only Exchange supported in this drop.
        raise RuntimeError("Set COINBASE_API_TARGET=exchange (Advanced Trade not enabled in this build).")
    return "https://api.exchange.coinbase.com"

def place_order(product_id: str, side: str, size: float, price: float | None = None, order_type: str = "limit"):
    """
    Places an order on Coinbase Exchange.
    order_type: "limit" | "market"
    For "market", omit price.
    """
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    api_passphrase = os.getenv("COINBASE_API_PASSPHRASE")
    if not (api_key and api_secret and api_passphrase):
        raise RuntimeError("Missing Coinbase API credentials in environment.")

    body = {
        "product_id": product_id,
        "side": side.lower(),
        "size": str(size),
        "type": order_type.lower(),
    }
    if order_type.lower() == "limit":
        if price is None:
            raise ValueError("Limit order requires price.")
        body["price"] = str(price)

    method = "POST"
    path = "/orders"

    # Serialize EXACTLY ONCE and sign the same bytes we send
    body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    ts = now_ts_str()
    sig = sign_cb_request(api_secret, ts, method, path, body)

    headers = {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": sig,
        "CB-ACCESS-TIMESTAMP": ts,
        "CB-ACCESS-PASSPHRASE": api_passphrase,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    r = http.post(f"{_base_url()}{path}", headers=headers, data=body_str, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()