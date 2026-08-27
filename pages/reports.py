import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from services.data_service import get_sales

st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")

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

st.title("📈 Sales & Inventory Reports")

TIMEZONE = ZoneInfo("Africa/Addis_Ababa")
today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
current_month_str = datetime.now(TIMEZONE).strftime("%Y-%m")

df = get_sales()

if df.empty:
    st.info("No sales data available yet.")
else:
    try:
        df["Total_Sale"] = pd.to_numeric(df["Total_Sale"], errors="coerce").fillna(0)
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
        df["Date_Str"] = df["Date"].astype(str).str.slice(0, 10)

        today_df = df[df["Date_Str"] == today_str]
        total_sales_today = today_df["Total_Sale"].sum()
        items_sold_today = today_df["Quantity"].sum()

        month_df = df[df["Date_Str"].str.startswith(current_month_str)]
        total_revenue_month = month_df["Total_Sale"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales Today", f"{total_sales_today:,.2f} ETB")
        col2.metric("Items Sold Today", int(items_sold_today))
        col3.metric("Total Revenue (Month)", f"{total_revenue_month:,.2f} ETB")

        st.markdown("---")

        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Sales by Company")
            if "Company" in df.columns and not df.empty:
                company_df = df.groupby("Company")["Total_Sale"].sum().reset_index()
                if not company_df.empty and company_df["Total_Sale"].sum() > 0:
                    st.bar_chart(company_df.set_index("Company"))
                else:
                    st.info("Sales breakdowns will display here.")
            else:
                st.info("Sales breakdowns will display here.")

        with c2:
            st.subheader("Top Selling Products")
            if "Product_Name" in df.columns and not df.empty:
                prod_df = df.groupby("Product_Name")["Quantity"].sum().reset_index()
                if not prod_df.empty and prod_df["Quantity"].sum() > 0:
                    st.bar_chart(prod_df.set_index("Product_Name"))
                else:
                    st.info("Top performing inventory items will display here.")
            else:
                st.info("Top performing inventory items will display here.")

    except Exception as e:
        st.error(f"Error loading reports: {e}")
