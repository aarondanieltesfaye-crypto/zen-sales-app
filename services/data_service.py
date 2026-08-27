from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from services.google_sheets import fetch_worksheet_data, write_row, update_data

TIMEZONE = ZoneInfo("Africa/Addis_Ababa")

def get_products() -> pd.DataFrame:
    """Fetches active products from the Google Sheet."""
    df = fetch_worksheet_data("Products")
    if not df.empty and "Status" in df.columns:
        return df[df["Status"] == "Active"]
    return df

def record_sale(
    product_name: str = "-",
    quantity: int = 1,
    unit_price: float = 0.0,
    total_amount: float = 0.0,
    company: str = "-",
    buyer_name: str = "-",
    notes: str = "-",
    *args,
    **kwargs
) -> bool:
    """
    Appends a new sale record, auto-calculating total amount and 
    formatting the date properly for the reports page.
    """
    now = datetime.now(TIMEZONE)
    date_only = now.strftime("%Y-%m-%d")         # Clean date for reports matching
    sale_id = now.strftime("S-%Y%m%d%H%M%S")     # Unique ID
    
    # Auto-calculate total if it passed as 0 or empty
    calc_total = float(total_amount) if total_amount > 0 else float(quantity) * float(unit_price)

    company_val = company if company else "-"
    buyer_val = buyer_name if buyer_name else "-"
    notes_val = notes if notes else "-"

    row_data = [
        sale_id,             # Column A: Sale_ID
        date_only,           # Column B: Date (YYYY-MM-DD)
        "-",                 # Column C: Product_ID
        company_val,         # Column D: Company
        product_name,        # Column E: Product_Name
        int(quantity),       # Column F: Quantity
        float(unit_price),   # Column G: Unit_Selling_Price
        calc_total,          # Column H: Total_Sale (Guaranteed correct math)
        "-",                 # Column I: Zen_Revenue 
        "-",                 # Column J: Payment_Method 
        buyer_val,           # Column K: Buyer
        notes_val            # Column L: Notes
    ]
    
    return write_row("Sales", row_data)

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")
