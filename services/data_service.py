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
    Appends a sale record to Sales (Columns A-M) and logs to Inventory_Transactions (Columns A-J).
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

    # Sales tab row (Columns A through M)
    sales_row = [
        sale_id, date_only, p_id, comp, prod,
        int(quantity), float(unit_price), calc_total,
        "-", pay, buyer, "-", note
    ]
    
    sales_success = write_row("Sales", sales_row)

    # Inventory_Transactions tab row (Columns A through J)
    inv_row = [
        txn_id, date_only, p_id, comp, prod,
        "Sale", -int(quantity), f"Sale ({sale_id})",
        "-", timestamp_str
    ]
    
    try:
        write_row("Inventory_Transactions", inv_row)
    except Exception as e:
        st.warning(f"Sale logged, but inventory transaction table update failed: {e}")

    return sales_success

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")
