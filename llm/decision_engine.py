import os
from common.http import SESSION as http

HTTP_TIMEOUT = 20

def query_llm(context_json: str):
    """
    Sends context to LLM endpoint. Expects JSON response.
    """
    endpoint = os.getenv("LLM_ENDPOINT_URL")
    if not endpoint:
        raise RuntimeError("LLM_ENDPOINT_URL not set in environment.")
    
    # Ensure compatibility with LM Studio endpoint
    r = http.post(
        endpoint, 
        json={"prompt": context_json},  # LM Studio expects "prompt" key
        timeout=HTTP_TIMEOUT
    )
    
    # Handle response
    r.raise_for_status()
    return r.json()