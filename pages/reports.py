import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from services.data_service import get_sales

st.title("📊 Sales & Inventory Reports")

TIMEZONE = ZoneInfo("Africa/Addis_Ababa")
today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
current_month_str = datetime.now(TIMEZONE).strftime("%Y-%m")

# Fetch sales data
df = get_sales()

if df.empty:
    st.info("No sales data available yet.")
else:
    try:
        # Clean and convert numeric columns safely
        df["Total_Sale"] = pd.to_numeric(df["Total_Sale"], errors="coerce").fillna(0)
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
        
        # Isolate just the YYYY-MM-DD string from the date column
        df["Date_Str"] = df["Date"].astype(str).str.slice(0, 10)

        # Calculate metrics for today
        today_df = df[df["Date_Str"] == today_str]
        total_sales_today = today_df["Total_Sale"].sum()
        items_sold_today = today_df["Quantity"].sum()

        # Calculate metrics for the current month
        month_df = df[df["Date_Str"].str.startswith(current_month_str)]
        total_revenue_month = month_df["Total_Sale"].sum()

        # Display Top Metrics Cards
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales Today", f"{total_sales_today:,.2f} ETB")
        col2.metric("Items Sold Today", int(items_sold_today))
        col3.metric("Total Revenue (Month)", f"{total_revenue_month:,.2f} ETB")

        st.markdown("---")

        # Display Breakdown Sections & Charts
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
