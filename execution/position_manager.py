from execution.coinbase_client import place_order

def open_position(symbol: str, size: float, price: float | None):
    product = f"{symbol.upper()}-USD"
    order_type = "market" if price is None else "limit"
    return place_order(product, "buy", size, price, order_type)

def close_position(symbol: str, size: float, price: float | None):
    product = f"{symbol.upper()}-USD"
    order_type = "market" if price is None else "limit"
    return place_order(product, "sell", size, price, order_type)