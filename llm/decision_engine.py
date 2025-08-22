import os
import requests

def query_llm(context_json: str):
    endpoint = os.getenv("LLM_ENDPOINT_URL")
    if not endpoint:
        raise ValueError("LLM_ENDPOINT_URL is not set")
    r = requests.post(endpoint, json={"context": context_json}, timeout=30)
    r.raise_for_status()
    return r.json()
