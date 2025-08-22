import json
from data_feeds import multi_source_price_guard
from data_feeds import sentiment_monitor

def build_context(symbols):
    """
    Builds a JSON string with current price and optional sentiment for each symbol.
    """
    context = {}
    for sym in symbols:
        avg_price = multi_source_price_guard.verify_prices(sym)
        sentiment = sentiment_monitor.get_sentiment(sym)
        payload = {"price": avg_price}
        if sentiment is not None:
            payload["sentiment"] = sentiment
        context[sym] = payload
    return json.dumps(context)
