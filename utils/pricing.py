"""Canonical product price helpers.

The Products sheet is the source of truth. Selling / unit price and buying
price can appear under several historical column names; these helpers resolve
them in one place so dashboard, sales, profit and reports stay in sync.
"""

import pandas as pd


SELLING_PRICE_COLUMNS = (
    "Selling_Price",
    "Unit_Price",
    "Unit_Selling_Price",
    "Price",
    "Zen_Price",
)

BUYING_PRICE_COLUMNS = (
    "Buying price",  # exact field added to zenproducts.xlsx
    "Buying_Price",
    "Cost_Price",
    "Cost",
)


def _to_float(value, default=0.0) -> float:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return float(default)
    return float(number)


def get_selling_price(row) -> float:
    """Customer-facing unit price for a product row."""
    for column in SELLING_PRICE_COLUMNS:
        if column in getattr(row, "index", []) or column in row:
            try:
                value = row[column]
            except Exception:
                value = row.get(column) if hasattr(row, "get") else None
            if value is None or (isinstance(value, float) and pd.isna(value)):
                continue
            price = _to_float(value, default=-1)
            if price >= 0:
                return price
    return 0.0


def get_buying_price(row) -> float:
    """What Zen paid (or 0 when the item is consignment / unknown)."""
    for column in BUYING_PRICE_COLUMNS:
        if column in getattr(row, "index", []) or column in row:
            try:
                value = row[column]
            except Exception:
                value = row.get(column) if hasattr(row, "get") else None
            if value is None or (isinstance(value, float) and pd.isna(value)):
                continue
            price = _to_float(value, default=-1)
            if price >= 0:
                return price
    return 0.0


def unit_profit(selling_price: float, buying_price: float) -> float:
    """Profit per unit = Selling Price - Buying Price."""
    return float(selling_price) - float(buying_price)


def line_profit(selling_price: float, buying_price: float, quantity: float) -> float:
    """Total profit = (Selling Price - Buying Price) x Quantity Sold."""
    return unit_profit(selling_price, buying_price) * float(quantity)
