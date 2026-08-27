import streamlit as st
import pandas as pd
from services.data_service import get_sales

st.title("📊 Management Dashboard")

try:
    df = get_sales()

    if df.empty:
        st.metric("Gross Sales (ETB)", "0.00")
        st.info("No sales data available yet.")
    else:
        # Safely convert Total_Sale column to numeric values
        if "Total_Sale" in df.columns:
            df["Total_Sale"] = pd.to_numeric(df["Total_Sale"], errors="coerce").fillna(0)
            gross_sales = df["Total_Sale"].sum()
        else:
            gross_sales = 0.0

        st.metric("Gross Sales (ETB)", f"{gross_sales:,.2f}")

        # Summary breakdown
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Orders", len(df))
        with col2:
            if "Quantity" in df.columns:
                total_qty = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0).sum()
                st.metric("Total Units Sold", int(total_qty))

        st.markdown("---")
        st.subheader("Recent Transactions")
        st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
