from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from services.google_sheets import fetch_worksheet_data, write_row_by_headers, update_data
from utils.calculations import calculate_zen_revenue
from utils.pricing import get_buying_price, get_selling_price

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
    settings_df = pd.DataFrame([
        ["Default_Low_Stock_Threshold", str(low_stock_threshold)],
        ["Currency", str(currency)]
    ], columns=["Key", "Value"])

    s_success = update_data("Settings", settings_df)

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
        found_cols = ", ".join(products_df.columns.tolist()) if not products_df.empty else "(sheet is empty)"
        st.error(
            f"Products sheet is missing a 'Product_ID' column. Columns found: {found_cols}. "
            "Make sure cell A1 of the Products tab says exactly 'Product_ID'."
        )
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

    Profit is computed as (Selling Price - Buying Price) x Quantity when a
    buying price exists. Consignment items with no buying price still fall
    back to the product's commission so those sales are not treated as 100%
    profit.
    """
    now = datetime.now(TIMEZONE)
    date_only = now.strftime("%Y-%m-%d")
    sale_id = now.strftime("S-%Y%m%d%H%M%S")

    calc_total = float(total_amount) if total_amount > 0 else float(quantity) * float(unit_price)

    calc_cogs, profit = compute_line_cost_and_profit(product_id, quantity, calc_total)
    if calc_cogs == 0.0 and profit == calc_total and cost_of_goods > 0:
        calc_cogs = float(cost_of_goods)
        profit = calc_total - calc_cogs
    elif calc_cogs == 0.0 and profit == calc_total and buying_price > 0:
        calc_cogs = float(quantity) * float(buying_price)
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


def get_product_cost_lookup() -> dict:
    """
    Returns {Product_ID: {cost_price, commission_type, commission_value, selling_price}}
    from the Products sheet.
      - If the product has a real buying price, profit = (Selling - Buying) x Qty.
      - If buying price is 0 (consignment), Zen earns a commission instead.
    """
    products_df = fetch_worksheet_data("Products")
    lookup = {}
    if products_df.empty or "Product_ID" not in products_df.columns:
        return lookup
    for _, p in products_df.iterrows():
        pid = str(p.get("Product_ID", "")).strip()
        if not pid:
            continue
        lookup[pid] = {
            "cost_price": get_buying_price(p),
            "selling_price": get_selling_price(p),
            "commission_type": p.get("Commission_Type", "Percentage") or "Percentage",
            "commission_value": pd.to_numeric(p.get("Commission_Value", 0), errors="coerce") or 0.0,
        }
    return lookup


def compute_line_cost_and_profit(product_id: str, quantity: float, total_sale: float, cost_lookup: dict = None):
    """
    Computes (cost_of_goods, profit) for a single sale line.
    Preferred formula when a buying price exists:
        Profit = (Selling Price - Buying Price) x Quantity
    """
    if cost_lookup is None:
        cost_lookup = get_product_cost_lookup()

    info = cost_lookup.get(str(product_id).strip())
    if not info:
        return 0.0, float(total_sale)

    buying = float(info.get("cost_price") or 0.0)
    qty = float(quantity)
    sale = float(total_sale)

    if buying > 0:
        cogs = buying * qty
        return cogs, sale - cogs

    profit = calculate_zen_revenue(
        gross_sale=sale,
        quantity=qty,
        commission_type=info["commission_type"],
        commission_value=info["commission_value"],
    )
    return sale - profit, profit


def get_profit_summary() -> dict:
    """
    Computes revenue, cost of goods, profit and margin across all sales.
    Profit is always recomputed fresh from the Products sheet.
    """
    df = get_sales()
    if df.empty:
        return {"revenue": 0.0, "cogs": 0.0, "profit": 0.0, "margin": 0.0, "df": df}

    df = df.copy()
    df["Total_Sale"] = pd.to_numeric(df.get("Total_Sale", 0), errors="coerce").fillna(0)
    df["Quantity"] = pd.to_numeric(df.get("Quantity", 0), errors="coerce").fillna(0)
    if "Product_ID" not in df.columns:
        df["Product_ID"] = "-"

    cost_lookup = get_product_cost_lookup()

    def _line(row):
        return compute_line_cost_and_profit(row["Product_ID"], row["Quantity"], row["Total_Sale"], cost_lookup)

    results = df.apply(_line, axis=1, result_type="expand")
    results.columns = ["Cost_of_Goods", "Profit"]
    df["Cost_of_Goods"] = results["Cost_of_Goods"]
    df["Profit"] = results["Profit"]
    df["Profit_Margin_%"] = df.apply(
        lambda r: round(r["Profit"] / r["Total_Sale"] * 100.0, 1) if r["Total_Sale"] > 0 else 0.0,
        axis=1
    )

    revenue = float(df["Total_Sale"].sum())
    cogs = float(df["Cost_of_Goods"].sum())
    profit = float(df["Profit"].sum())
    margin = (profit / revenue * 100.0) if revenue > 0 else 0.0

    return {"revenue": revenue, "cogs": cogs, "profit": profit, "margin": margin, "df": df}


def get_products_with_margin() -> pd.DataFrame:
    """
    Returns the full Products sheet enriched with Profit_Margin_% and
    Est_Profit_Per_Unit, using Buying price when present and commission
    when the item is consignment.
    """
    df = fetch_worksheet_data("Products")
    if df.empty:
        return df
    df = df.copy()
    for col in ["Cost_Price", "Buying price", "Buying_Price", "Selling_Price", "Commission_Value", "Current_Stock"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    def _margin_and_profit(row):
        selling = get_selling_price(row)
        cost = get_buying_price(row)
        if selling <= 0:
            return 0.0, 0.0
        if cost > 0:
            profit = selling - cost
        else:
            profit = calculate_zen_revenue(
                gross_sale=selling,
                quantity=1,
                commission_type=row.get("Commission_Type", "Percentage") or "Percentage",
                commission_value=row.get("Commission_Value", 0),
            )
        margin_pct = round(profit / selling * 100.0, 1)
        return margin_pct, round(profit, 2)

    margins = df.apply(_margin_and_profit, axis=1, result_type="expand")
    margins.columns = ["Profit_Margin_%", "Est_Profit_Per_Unit"]
    df["Profit_Margin_%"] = margins["Profit_Margin_%"]
    df["Est_Profit_Per_Unit"] = margins["Est_Profit_Per_Unit"]
    return df
