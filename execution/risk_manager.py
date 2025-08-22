MAX_RISK_PER_TRADE = 0.02  # 2%

def position_size(account_balance: float, stop_loss_distance: float, price: float):
    """
    account_balance: total account value in quote currency (e.g., USD)
    stop_loss_distance: fraction from entry to stop (e.g., 0.01 for 1%)
    price: current price level
    """
    if stop_loss_distance <= 0 or price <= 0 or account_balance <= 0:
        raise ValueError("Inputs must be positive")
    risk_amount = account_balance * MAX_RISK_PER_TRADE
    qty = risk_amount / (stop_loss_distance * price)
    return qty

if __name__ == "__main__":
    print(position_size(10000, 0.01, 20000))
