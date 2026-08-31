import streamlit as st
import pandas as pd
from services.data_service import get_sales, get_profit_summary
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
    summary = get_profit_summary()
    df = summary["df"]

    if df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gross Sales", "0.00 ETB")
        col2.metric("Total Orders", 0)
        col3.metric("Total Units Sold", 0)
        col4.metric("Profit", "0.00 ETB")
        st.info("No sales data available yet.")
    else:
        gross_sales = summary["revenue"]
        cogs = summary["cogs"]
        profit = summary["profit"]
        profit_margin = summary["margin"]

        # --- Display Metrics ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gross Sales", f"{gross_sales:,.2f} ETB")
        col2.metric("Total Orders", len(df))
        total_qty = df["Quantity"].sum()
        col3.metric("Total Units Sold", int(total_qty))
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
            st.info("📊 Profit breakdown requires cost data. Add a 'Cost_Price' on the Products sheet, or record new sales (which now capture cost automatically).")

        st.caption("For a deeper breakdown by company, product, and time period, see the 💰 Profit & Revenue page.")

        # --- Recent Transactions ---
        st.markdown("---")
        st.subheader("📋 Recent Transactions")
        st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.exception(e)
