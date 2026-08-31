from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from services.google_sheets import fetch_worksheet_data, write_row_by_headers, update_data

TIMEZONE = ZoneInfo("Africa/Addis_Ababa")

# Canonical column sets. write_row_by_headers will create these on the sheet
# if they don't exist yet, and will always write to the sheet's real header
# order rather than assuming a fixed position.
SALES_HEADERS = [
    "Sale_ID", "Date", "Product_ID", "Company", "Product_Name",
    "Quantity", "Unit_Price", "Total_Sale",
    "Buying_Price", "Cost_of_Goods", "Profit", "Profit_Margin_%",
    "Payment_Method", "Buyer_Name", "Receptionist", "Notes"
]

INVENTORY_HEADERS = [
    "Transaction_ID", "Date", "Product_ID", "Company", "Product_Name",
    "Transaction_Type", "Quantity_Change", "Reason", "Receptionist", "Timestamp"
]

def get_products() -> pd.DataFrame:
    """Fetches active products from the Google Sheet."""
    df = fetch_worksheet_data("Products")
    if not df.empty and "Status" in df.columns:
        return df[df["Status"] == "Active"]
    elif not df.empty and "Active" in df.columns:
        return df[df["Active"].astype(str).str.upper() == "TRUE"]
    return df

def get_settings() -> dict:
    """Reads key-value settings from the Settings sheet."""
    defaults = {
        "Default_Low_Stock_Threshold": "5",
        "Currency": "ETB"
    }
    try:
        df = fetch_worksheet_data("Settings")
        if not df.empty:
            for _, row in df.iterrows():
                if len(row) >= 2:
                    k = str(row.iloc[0]).strip()
                    v = str(row.iloc[1]).strip()
                    if k:
                        defaults[k] = v
    except Exception as e:
        st.warning(f"Error loading settings: {e}")
    return defaults

def save_settings(currency: str, low_stock_threshold: int) -> bool:
    """
    Overwrites key-value settings in Settings tab and updates 
    Low_Stock_Threshold column for all products in Products tab.
    """
    # 1. Update Settings tab
    settings_df = pd.DataFrame([
        ["Default_Low_Stock_Threshold", str(low_stock_threshold)],
        ["Currency", str(currency)]
    ], columns=["Key", "Value"])
    
    s_success = update_data("Settings", settings_df)

    # 2. Bulk update Low_Stock_Threshold in Products tab
    try:
        products_df = fetch_worksheet_data("Products")
        if not products_df.empty and "Low_Stock_Threshold" in products_df.columns:
            products_df["Low_Stock_Threshold"] = str(low_stock_threshold)
            update_data("Products", products_df)
    except Exception as e:
        st.warning(f"Settings saved, but updating Products sheet failed: {e}")

    st.cache_data.clear()
    return s_success

def adjust_stock(
    product_id: str,
    quantity_change: int,
    transaction_type: str = "Restock",
    receptionist: str = "-",
    reason: str = "-"
) -> bool:
    """Updates stock levels in Products sheet and logs to Inventory_Transactions."""
    now = datetime.now(TIMEZONE)
    date_only = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    txn_id = now.strftime("TXN-%Y%m%d%H%M%S")

    products_df = fetch_worksheet_data("Products")
    if products_df.empty or "Product_ID" not in products_df.columns:
        st.error("Products sheet is empty or missing Product_ID column.")
        return False

    match_idx = products_df.index[products_df["Product_ID"].astype(str).str.strip() == str(product_id).strip()].tolist()
    if not match_idx:
        st.error(f"Product ID '{product_id}' not found in Google Sheet.")
        return False

    row_i = match_idx[0]
    company = str(products_df.loc[row_i, "Company"]) if "Company" in products_df.columns else "-"
    product_name = str(products_df.loc[row_i, "Product_Name"]) if "Product_Name" in products_df.columns else "-"

    qty_change = int(quantity_change)
    if transaction_type in ["Damage", "Waste", "Personal Use", "Deduction", "Sale"] and qty_change > 0:
        qty_change = -qty_change

    current_val = pd.to_numeric(products_df.loc[row_i, "Current_Stock"], errors="coerce")
    current_val = 0 if pd.isna(current_val) else int(current_val)
    new_stock = max(0, current_val + qty_change)

    products_df.loc[row_i, "Current_Stock"] = new_stock
    prod_success = update_data("Products", products_df)

    inv_row = {
        "Transaction_ID": txn_id,
        "Date": date_only,
        "Product_ID": product_id,
        "Company": company,
        "Product_Name": product_name,
        "Transaction_Type": transaction_type,
        "Quantity_Change": qty_change,
        "Reason": reason if reason else "-",
        "Receptionist": receptionist if receptionist else "-",
        "Timestamp": timestamp_str,
    }
    try:
        write_row_by_headers("Inventory_Transactions", inv_row, required_headers=INVENTORY_HEADERS)
    except Exception as e:
        st.warning(f"Stock updated, but transaction logging failed: {e}")

    st.cache_data.clear()
    return prod_success

def record_sale(
    product_id: str = "-",
    company: str = "-",
    product_name: str = "-",
    quantity: int = 1,
    unit_price: float = 0.0,
    total_amount: float = 0.0,
    buying_price: float = 0.0,
    cost_of_goods: float = 0.0,
    payment_method: str = "Cash",
    buyer_name: str = "-",
    receptionist: str = "-",
    notes: str = "-",
    *args,
    **kwargs
) -> bool:
    """
    Appends a sale record (including cost/profit) and reduces stock count.

    Previously buying_price/cost_of_goods were accepted by callers but were
    silently swallowed by **kwargs and never written to the Sales sheet,
    which is why profit could never be reliably calculated. They're now
    captured, used to compute Profit, and persisted.
    """
    now = datetime.now(TIMEZONE)
    date_only = now.strftime("%Y-%m-%d")
    sale_id = now.strftime("S-%Y%m%d%H%M%S")

    calc_total = float(total_amount) if total_amount > 0 else float(quantity) * float(unit_price)
    calc_cogs = float(cost_of_goods) if cost_of_goods > 0 else float(quantity) * float(buying_price)
    profit = calc_total - calc_cogs
    profit_margin = (profit / calc_total * 100.0) if calc_total > 0 else 0.0

    sales_row = {
        "Sale_ID": sale_id,
        "Date": date_only,
        "Product_ID": product_id,
        "Company": company,
        "Product_Name": product_name,
        "Quantity": int(quantity),
        "Unit_Price": float(unit_price),
        "Total_Sale": calc_total,
        "Buying_Price": float(buying_price),
        "Cost_of_Goods": calc_cogs,
        "Profit": profit,
        "Profit_Margin_%": round(profit_margin, 2),
        "Payment_Method": payment_method,
        "Buyer_Name": buyer_name if buyer_name else "-",
        "Receptionist": receptionist if receptionist else "-",
        "Notes": notes if notes else "-",
    }
    sales_success = write_row_by_headers("Sales", sales_row, required_headers=SALES_HEADERS)

    adjust_stock(
        product_id=product_id,
        quantity_change=-int(quantity),
        transaction_type="Sale",
        receptionist=receptionist if receptionist else "-",
        reason=f"Sale ({sale_id})"
    )

    st.cache_data.clear()
    return sales_success

def get_sales() -> pd.DataFrame:
    """Fetches all recorded sales from the Google Sheet."""
    return fetch_worksheet_data("Sales")

def get_profit_summary() -> dict:
    """
    Computes revenue, cost of goods, profit and margin across all sales.
    Prefers the Profit/Cost_of_Goods columns recorded at sale time; for
    older rows recorded before that fix, falls back to joining against the
    Products sheet's Cost_Price so historical data still shows correctly.
    Returns a dict with the summary totals plus the enriched sales DataFrame.
    """
    df = get_sales()
    if df.empty:
        return {"revenue": 0.0, "cogs": 0.0, "profit": 0.0, "margin": 0.0, "df": df}

    df = df.copy()
    df["Total_Sale"] = pd.to_numeric(df.get("Total_Sale", 0), errors="coerce").fillna(0)
    df["Quantity"] = pd.to_numeric(df.get("Quantity", 0), errors="coerce").fillna(0)

    if "Cost_of_Goods" in df.columns:
        df["Cost_of_Goods"] = pd.to_numeric(df["Cost_of_Goods"], errors="coerce").fillna(0)
    else:
        df["Cost_of_Goods"] = 0.0

    # Fallback for legacy rows (Cost_of_Goods missing/0): join Products on Product_ID.
    needs_fallback = df["Cost_of_Goods"] <= 0
    if needs_fallback.any() and "Product_ID" in df.columns:
        products_df = fetch_worksheet_data("Products")
        if not products_df.empty and "Product_ID" in products_df.columns and "Cost_Price" in products_df.columns:
            cost_map = dict(zip(
                products_df["Product_ID"].astype(str).str.strip(),
                pd.to_numeric(products_df["Cost_Price"], errors="coerce").fillna(0)
            ))
            fallback_cost = df.loc[needs_fallback, "Product_ID"].astype(str).str.strip().map(cost_map).fillna(0)
            df.loc[needs_fallback, "Cost_of_Goods"] = fallback_cost * df.loc[needs_fallback, "Quantity"]

    if "Profit" in df.columns:
        df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)
        df.loc[needs_fallback, "Profit"] = df.loc[needs_fallback, "Total_Sale"] - df.loc[needs_fallback, "Cost_of_Goods"]
    else:
        df["Profit"] = df["Total_Sale"] - df["Cost_of_Goods"]

    revenue = float(df["Total_Sale"].sum())
    cogs = float(df["Cost_of_Goods"].sum())
    profit = float(df["Profit"].sum())
    margin = (profit / revenue * 100.0) if revenue > 0 else 0.0

    return {"revenue": revenue, "cogs": cogs, "profit": profit, "margin": margin, "df": df}
