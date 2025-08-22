from execution import coinbase_client as cb

def open_position(symbol, size, price=None, order_type="limit"):
    return cb.place_order(f"{symbol}-USD", "buy", size, price, order_type=order_type)

def close_position(symbol, size, price=None, order_type="limit"):
    return cb.place_order(f"{symbol}-USD", "sell", size, price, order_type=order_type)
