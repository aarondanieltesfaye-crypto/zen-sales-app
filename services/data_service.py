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

def adjust_stock(
    product_id: str,
    quantity_change: int,
    transaction_type: str = "Restock",
    receptionist: str = "-",
    reason: str = "-"
) -> bool:
    """
    Updates stock levels in Products sheet, logs to Inventory_Transactions,
    and clears cache to reflect changes immediately.
    """
    now = datetime.now(TIMEZONE)
    date_only = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    txn_id = now.strftime("TXN-%Y%m%d%H%M%S")

    # Fetch fresh Products sheet
    products_df = fetch_worksheet_data("Products")
    if products_df.empty or "Product_ID" not in products_df.columns:
        st.error("Products sheet is empty or missing Product_ID column.")
        return False

    # Match exact Product ID
    match_idx = products_df.index[products_df["Product_ID"].astype(str).str.strip() == str(product_id).strip()].tolist()
    if not match_idx:
        st.error(f"Product ID '{product_id}' not found in Google Sheet.")
        return False

    row_i = match_idx[0]
    company = str(products_df.loc[row_i, "Company"]) if "Company" in products_df.columns else "-"
    product_name = str(products_df.loc[row_i, "Product_Name"]) if "Product_Name" in products_df.columns else "-"

    # Determine sign for quantity change
    qty_change = int(quantity_change)
    if transaction_type in ["Damage", "Waste", "Personal Use", "Deduction", "Sale"] and qty_change > 0:
        qty_change = -qty_change

    current_val = pd.to_numeric(products_df.loc[row_i, "Current_Stock"], errors="coerce")
    current_val = 0 if pd.isna(current_val) else int(current_val)
    new_stock = max(0, current_val + qty_change)

    # 1. Save updated stock back to Products tab
    products_df.loc[row_i, "Current_Stock"] = new_stock
    prod_success = update_data("Products", products_df)

    # 2. Append transaction record to Inventory_Transactions tab
    inv_row = [
        txn_id, date_only, product_id, company, product_name,
        transaction_type, qty_change, reason if reason else "-",
        receptionist if receptionist else "-", timestamp_str
    ]
    try:
        write_row("Inventory_Transactions", inv_row)
    except Exception as e:
        st.warning(f"Stock updated, but transaction logging failed: {e}")

    # 3. Clear cache so dashboard and inventory sync immediately
    st.cache_data.clear()
    return prod_success

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
    """Appends sale record and reduces stock count."""
    now = datetime.now(TIMEZONE)
    date_only = now.strftime("%Y-%m-%d")         
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    sale_id = now.strftime("S-%Y%m%d%H%M%S")     
    
    calc_total = float(total_amount) if total_amount > 0 else float(quantity) * float(unit_price)

    p_id = product_id if product_id else "-"
    comp = company if company else "-"
    prod = product_name if product_name else "-"
    pay = payment_method if payment_method else "Cash"
    buyer = buyer_name if buyer_name else "-"
    note = notes if notes else "-"

    sales_row = [
        sale_id, date_only, p_id, comp, prod,
        int(quantity), float(unit_price), calc_total,
        "-", pay, buyer, "-", note
    ]
    sales_success = write_row("Sales", sales_row)

    adjust_stock(
        product_id=p_id,
        quantity_change=-int(quantity),
        transaction_type="Sale",
        receptionist="-",
        reason=f"Sale ({sale_id})"
    )

    return sales_success

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")
