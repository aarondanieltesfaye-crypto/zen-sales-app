import streamlit as st
import pandas as pd
from services.data_service import get_sales

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #2E6F40;
        padding: 18px;
        border-radius: 12px;
        border: 2px solid #87AE73;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Management Dashboard")

try:
    df = get_sales()

    if df.empty:
        st.metric("Gross Sales (ETB)", "0.00")
        st.info("No sales data available yet.")
    else:
        if "Total_Sale" in df.columns:
            df["Total_Sale"] = pd.to_numeric(df["Total_Sale"], errors="coerce").fillna(0)
            gross_sales = df["Total_Sale"].sum()
        else:
            gross_sales = 0.0

        col1, col2, col3 = st.columns(3)
        col1.metric("Gross Sales", f"{gross_sales:,.2f} ETB")
        col2.metric("Total Orders", len(df))
        
        if "Quantity" in df.columns:
            total_qty = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0).sum()
            col3.metric("Total Units Sold", int(total_qty))
        else:
            col3.metric("Total Units Sold", 0)

        st.markdown("---")
        st.subheader("Recent Transactions")
        st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
