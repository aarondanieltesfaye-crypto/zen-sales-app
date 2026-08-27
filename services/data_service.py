from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from services.google_sheets import fetch_worksheet_data, write_row, update_data

# Local timezone setting (East Africa Time UTC+3)
TIMEZONE = ZoneInfo("Africa/Addis_Ababa")

def get_current_timestamp() -> str:
    """Returns the current timestamp formatted in local East Africa Time."""
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

def get_products() -> pd.DataFrame:
    """Fetches products from the Google Sheet."""
    df = fetch_worksheet_data("Products")
    if not df.empty and "Status" in df.columns:
        return df[df["Status"] == "Active"]
    return df

def record_sale(
    product_name: str = "",
    quantity: int = 1,
    unit_price: float = 0.0,
    total_amount: float = 0.0,
    company: str = "",
    buyer_name: str = "",
    notes: str = "",
    *args,
    **kwargs
) -> bool:
    """
    Appends a new sale record with timestamp and optional buyer details.
    Accepts arbitrary arguments (*args, **kwargs) to prevent parameter errors from sales.py.
    """
    timestamp = get_current_timestamp()
    
    # Matches sales log columns
    row_data = [
        timestamp,
        product_name,
        quantity,
        unit_price,
        total_amount,
        company,
        buyer_name,
        notes
    ]
    
    return write_row("Sales", row_data)

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")
