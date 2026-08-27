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
    elif not df.empty and "Active" in df.columns:
        return df[df["Active"].astype(str).str.upper() == "TRUE"]
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
    1. Appends sale to Sales sheet.
    2. Logs change to Inventory_Transactions sheet.
    3. Updates Current_Stock in Products sheet.
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

    # 1. Save to Sales sheet
    sales_row = [
        sale_id, date_only, p_id, comp, prod,
        int(quantity), float(unit_price), calc_total,
        "-", pay, buyer, "-", note
    ]
    sales_success = write_row("Sales", sales_row)

    # 2. Save to Inventory_Transactions sheet
    inv_row = [
        txn_id, date_only, p_id, comp, prod,
        "Sale", -int(quantity), f"Sale ({sale_id})",
        "-", timestamp_str
    ]
    try:
        write_row("Inventory_Transactions", inv_row)
    except Exception as e:
        st.warning(f"Sale recorded, but inventory transaction log failed: {e}")

    # 3. Deduct stock from Products sheet
    try:
        products_df = fetch_worksheet_data("Products")
        if not products_df.empty and "Product_ID" in products_df.columns and "Current_Stock" in products_df.columns:
            match_idx = products_df.index[products_df["Product_ID"] == p_id].tolist()
            if match_idx:
                row_i = match_idx[0]
                current_val = pd.to_numeric(products_df.loc[row_i, "Current_Stock"], errors="coerce")
                current_val = 0 if pd.isna(current_val) else int(current_val)
                
                products_df.loc[row_i, "Current_Stock"] = max(0, current_val - int(quantity))
                update_data("Products", products_df)
    except Exception as e:
        st.warning(f"Sale recorded, but stock level update in Products sheet failed: {e}")

    return sales_success

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")
