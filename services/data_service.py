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
    product_id: str = "-",
    company: str = "-",
    product_name: str = "-",
    quantity: int = 1,
    unit_price: float = 0.0,
    total_amount: float = 0.0,
    payment_method: str = "Cash",
    buyer_name: str = "-",
    notes: str = "-",
    *args,
    **kwargs
) -> bool:
    """
    Appends a new sale record to Sales sheet AND logs an inventory transaction.
    """
    now = datetime.now(TIMEZONE)
    date_only = now.strftime("%Y-%m-%d")         
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    sale_id = now.strftime("S-%Y%m%d%H%M%S")     
    txn_id = now.strftime("TXN-%Y%m%d%H%M%S")
    
    calc_total = float(total_amount) if total_amount > 0 else float(quantity) * float(unit_price)

    p_id = product_id if product_id else "-"
    comp = company if company else "-"
    prod = product_name if product_name else "-"
    pay = payment_method if payment_method else "Cash"
    buyer = buyer_name if buyer_name else "-"
    note = notes if notes else "-"

    # 1. Row for Sales Sheet (Columns A - M)
    sales_row = [
        sale_id,             # Column A: Sale_ID
        date_only,           # Column B: Date
        p_id,                # Column C: Product_ID
        comp,                # Column D: Company
        prod,                # Column E: Product_Name
        int(quantity),       # Column F: Quantity
        float(unit_price),   # Column G: Unit_Selling_Price
        calc_total,          # Column H: Total_Sale
        "-",                 # Column I: Zen_Revenue 
        pay,                 # Column J: Payment_Method 
        buyer,               # Column K: Buyer
        "-",                 # Column L: Receptionist
        note                 # Column M: Notes
    ]
    
    sales_success = write_row("Sales", sales_row)

    # 2. Row for Inventory_Transactions Sheet (Columns A - J)
    inv_row = [
        txn_id,              # Column A: Transaction_ID
        date_only,           # Column B: Date
        p_id,                # Column C: Product_ID
        comp,                # Column D: Company
        prod,                # Column E: Product_Name
        "Sale",              # Column F: Transaction_Type
        -int(quantity),      # Column G: Quantity_Change (negative reduction)
        f"Sale ({sale_id})", # Column H: Reason
        "-",                 # Column I: Receptionist
        timestamp_str        # Column J: Timestamp
    ]
    
    try:
        write_row("Inventory_Transactions", inv_row)
    except Exception as e:
        st.warning(f"Sale recorded, but inventory transaction log failed: {e}")

    return sales_success

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")
