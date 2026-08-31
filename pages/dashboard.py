import streamlit as st
import pandas as pd
from services.data_service import get_sales
import re

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
    /* Main Background: Forest Green */
    .stApp {
        background-color: #2E6F40;
    }
    
    /* Sage Green Metric Cards with Dark Contrast Text */
    div[data-testid="stMetric"] {
        background-color: #87AE73;
        padding: 18px;
        border-radius: 12px;
        border: 2px solid #1D4729;
    }
    div[data-testid="stMetric"] * {
        color: #0D1B12 !important;
    }

    /* High Contrast Alert Boxes (st.info, st.warning, etc.) */
    div[data-testid="stAlert"] {
        background-color: #1D4729 !important;
        border: 1px solid #87AE73 !important;
        border-radius: 10px;
    }
    div[data-testid="stAlert"] * {
        color: #FFFFFF !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Management Dashboard")

try:
    df = get_sales()

    if df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gross Sales", "0.00 ETB")
        col2.metric("Total Orders", 0)
        col3.metric("Total Units Sold", 0)
        col4.metric("Profit", "0.00 ETB")
        st.info("No sales data available yet.")
    else:
        # --- Calculate Gross Sales ---
        if "Total_Sale" in df.columns:
            df["Total_Sale"] = pd.to_numeric(df["Total_Sale"], errors="coerce").fillna(0)
            gross_sales = df["Total_Sale"].sum()
        else:
            gross_sales = 0.0

        # --- Calculate Cost of Goods Sold (COGS) and Profit ---
        # Try to find buying price columns
        cogs = 0.0
        
        # Look for buying price columns (various naming conventions)
        buying_cols = [col for col in df.columns if "buy" in col.lower() or "cost" in col.lower() or "unit price" in col.lower()]
        
        # Also check if there's a separate "Buying Price" column in the raw data
        if "Buying_Price" in df.columns:
            df["Buying_Price"] = pd.to_numeric(df["Buying_Price"], errors="coerce").fillna(0)
            # If we have quantity and buying price, calculate COGS
            if "Quantity" in df.columns:
                df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
                cogs = (df["Buying_Price"] * df["Quantity"]).sum()
            else:
                cogs = df["Buying_Price"].sum()
        elif "Cost" in df.columns:
            df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce").fillna(0)
            if "Quantity" in df.columns:
                df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
                cogs = (df["Cost"] * df["Quantity"]).sum()
            else:
                cogs = df["Cost"].sum()
        elif "Unit_Price" in df.columns and "Buying_Price" not in df.columns:
            # If we have "Buyer price" or similar, try to infer
            pass
        else:
            # Fallback: if we have price and quantity but no buying price,
            # we'll use a default margin or skip
            st.warning("⚠️ Buying price data not found. Profit calculation may be incomplete.")
        
        # Calculate Profit
        profit = gross_sales - cogs
        profit_margin = (profit / gross_sales * 100) if gross_sales > 0 else 0

        # --- Display Metrics ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gross Sales", f"{gross_sales:,.2f} ETB")
        col2.metric("Total Orders", len(df))
        
        if "Quantity" in df.columns:
            total_qty = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0).sum()
            col3.metric("Total Units Sold", int(total_qty))
        else:
            col3.metric("Total Units Sold", 0)
        
        col4.metric("💰 Profit", f"{profit:,.2f} ETB", 
                    delta=f"{profit_margin:.1f}% margin" if gross_sales > 0 else None)

        # --- Profit Breakdown Chart ---
        st.markdown("---")
        
        if cogs > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Revenue vs Cost")
                chart_data = pd.DataFrame({
                    "Category": ["Gross Sales", "Cost of Goods Sold", "Profit"],
                    "Amount": [gross_sales, cogs, profit]
                })
                st.bar_chart(chart_data.set_index("Category"))
            
            with col2:
                st.subheader("💰 Profit Breakdown")
                st.metric("Gross Sales", f"{gross_sales:,.2f} ETB")
                st.metric("Cost of Goods Sold", f"{cogs:,.2f} ETB", delta=f"-{cogs:,.2f} ETB")
                st.metric("Net Profit", f"{profit:,.2f} ETB", delta=f"{profit_margin:.1f}%")
        else:
            st.info("📊 Profit breakdown requires cost data. Please ensure 'Buying Price' or 'Cost' columns are available in your data.")

        # --- Recent Transactions ---
        st.markdown("---")
        st.subheader("📋 Recent Transactions")
        st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.exception(e)
