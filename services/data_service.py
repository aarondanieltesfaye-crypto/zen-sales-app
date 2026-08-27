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
    Appends a new sale record exactly aligned with the Google Sheets columns.
    """
    timestamp = get_current_timestamp()
    # Generates a unique ID like S-20260827103137
    sale_id = datetime.now(TIMEZONE).strftime("S-%Y%m%d%H%M%S") 
    
    # This list now perfectly matches columns A through L in your sheet
    row_data = [
        sale_id,             # Column A: Sale_ID
        timestamp,           # Column B: Date
        "",                  # Column C: Product_ID (Leaving blank if not provided)
        company,             # Column D: Company
        product_name,        # Column E: Product_Name
        quantity,            # Column F: Quantity
        unit_price,          # Column G: Unit_Selling_Price
        total_amount,        # Column H: Total_Sale
        "",                  # Column I: Zen_Revenue (Leave blank for sheet formulas)
        "",                  # Column J: Payment_Method 
        buyer_name,          # Column K: Buyer
        notes                # Column L: Notes/Receipt
    ]
    
    return write_row("Sales", row_data)

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")
