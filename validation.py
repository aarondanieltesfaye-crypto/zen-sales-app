def validate_sale_input(qty, stock, price):
    if qty <= 0: return False, "Quantity must be greater than 0."
    if price < 0: return False, "Price cannot be negative."
    if qty > stock: return False, f"Insufficient stock. Only {stock} remaining."
    return True, ""