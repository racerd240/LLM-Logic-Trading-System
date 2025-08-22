import base64
import hmac
import json
import time
from hashlib import sha256

def sign_cb_request(secret_b64: str, timestamp: str, method: str, request_path: str, body: dict | None):
    """
    Coinbase Exchange HMAC SHA256 signature (base64 secret).
    method: "GET" | "POST" | "DELETE"
    request_path: e.g. "/orders" (leading slash, no host)
    body: dict or None
    """
    body_str = "" if body is None else json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    prehash = f"{timestamp}{method.upper()}{request_path}{body_str}"
    secret = base64.b64decode(secret_b64)
    signature = hmac.new(secret, prehash.encode("utf-8"), sha256).digest()
    return base64.b64encode(signature).decode("utf-8")

def now_ts_str() -> str:
    return str(int(time.time()))