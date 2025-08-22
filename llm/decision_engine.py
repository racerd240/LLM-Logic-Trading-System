import os
import re
import json
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_SYSTEM_PROMPT = (
    "You are a trading decision engine. Given compact JSON market context, "
    "respond ONLY with a JSON array named decisions. Each item must be an object with: "
    "symbol (string), action (BUY|SELL|HOLD), confidence (0..1), reason (short string). "
    "Do not include any text outside the JSON."
)

LLM_ENDPOINT_URL = os.getenv("LLM_ENDPOINT_URL", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
HTTP_TIMEOUT = float(os.getenv("LLM_HTTP_TIMEOUT", "30"))

def _extract_json_block(text: str) -> Optional[str]:
    """Best-effort extraction of the first top-level JSON object or array from text."""
    # Try fenced code block first
    fence = re.search(r"```(?:json)?\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        candidate = fence.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    # Fallback: find first {...} or [...] balanced block
    stack = []
    start = None
    for i, ch in enumerate(text):
        if ch in "[{":
            if not stack:
                start = i
            stack.append(ch)
        elif ch in "]}":
            if not stack:
                continue
            opening = stack.pop()
            if not stack and start is not None:
                candidate = text[start : i + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    pass
    return None

essential_schema_hint = {
    "decisions": [
        {
            "symbol": "BTC-USD",
            "action": "HOLD",
            "confidence": 0.5,
            "reason": "short rationale"
        }
    ]
}

def decide(context_json: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Call the LLM (if configured) to produce structured trade decisions.

    Returns a dict: {
      "decisions": List[Dict[str, Any]],
      "raw": Optional[str],
      "used_endpoint": bool,
      "error": Optional[str]
    }
    """
    system = system_prompt or DEFAULT_SYSTEM_PROMPT

    # If no endpoint configured, return a safe HOLD decision for discoverability.
    if not LLM_ENDPOINT_URL:
        try:
            ctx = json.loads(context_json)
            symbols = list(ctx.keys())
        except Exception:
            symbols = []
        return {
            "decisions": [
                {
                    "symbol": s,
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reason": "LLM endpoint not configured (LLM_ENDPOINT_URL)"
                }
                for s in symbols
            ],
            "raw": None,
            "used_endpoint": False,
            "error": None,
        }

    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    "Market context (JSON):\n" + context_json +
                    "\n\nReturn only valid JSON matching this Python dict schema hint: "
                    + json.dumps(essential_schema_hint, separators=(",", ":"))
                ),
            },
        ],
        "temperature": 0.2,
        # If your endpoint honors response_format, you can uncomment:
        # "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(LLM_ENDPOINT_URL.rstrip("/") + "/v1/chat/completions",
                             headers=headers, json=payload, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return {
            "decisions": [],
            "raw": None,
            "used_endpoint": True,
            "error": f"llm_request_failed: {e}",
        }

    # Try to parse strict JSON; otherwise extract best-effort
    parsed: Optional[Dict[str, Any]] = None
    try:
        parsed = json.loads(content)
    except Exception:
        block = _extract_json_block(content) or content
        try:
            parsed = json.loads(block)
        except Exception:
            parsed = None

    decisions: List[Dict[str, Any]] = []
    if isinstance(parsed, dict) and isinstance(parsed.get("decisions"), list):
        for item in parsed["decisions"]:
            if not isinstance(item, dict):
                continue
            symbol = str(item.get("symbol", "")).upper()
            action = str(item.get("action", "HOLD")).upper()
            if action not in {"BUY", "SELL", "HOLD"}:
                action = "HOLD"
            try:
                confidence = float(item.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            reason = str(item.get("reason", ""))
            if symbol:
                decisions.append({
                    "symbol": symbol,
                    "action": action,
                    "confidence": max(0.0, min(1.0, confidence)),
                    "reason": reason,
                })

    return {
        "decisions": decisions,
        "raw": content,
        "used_endpoint": True,
        "error": None,
    }