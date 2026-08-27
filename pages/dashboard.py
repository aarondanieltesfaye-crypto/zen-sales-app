import streamlit as st
import pandas as pd
from services.data_service import get_sales

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
        col1, col2, col3 = st.columns(3)
        col1.metric("Gross Sales", "0.00 ETB")
        col2.metric("Total Orders", 0)
        col3.metric("Total Units Sold", 0)
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
