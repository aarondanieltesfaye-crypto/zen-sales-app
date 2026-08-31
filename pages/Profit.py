import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from services.data_service import get_profit_summary

st.set_page_config(page_title="Profit & Revenue", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #2E6F40;
    }
    div[data-testid="stMetric"] {
        background-color: #87AE73;
        padding: 18px;
        border-radius: 12px;
        border: 2px solid #1D4729;
    }
    div[data-testid="stMetric"] * {
        color: #0D1B12 !important;
    }
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

st.title("💰 Profit & Revenue")

TIMEZONE = ZoneInfo("Africa/Addis_Ababa")

summary = get_profit_summary()
df = summary["df"]

if df.empty:
    st.info("No sales data available yet. Profit and revenue will appear here once sales are recorded.")
else:
    df = df.copy()
    df["Date_Str"] = df["Date"].astype(str).str.slice(0, 10)

    # --- Optional date range filter ---
    valid_dates = pd.to_datetime(df["Date_Str"], errors="coerce").dropna()
    if not valid_dates.empty:
        min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
        with col_f2:
            end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

        mask = (pd.to_datetime(df["Date_Str"], errors="coerce").dt.date >= start_date) & \
               (pd.to_datetime(df["Date_Str"], errors="coerce").dt.date <= end_date)
        df = df[mask]

    if df.empty:
        st.warning("No sales in the selected date range.")
    else:
        revenue = float(df["Total_Sale"].sum())
        cogs = float(df["Cost_of_Goods"].sum())
        profit = float(df["Profit"].sum())
        margin = (profit / revenue * 100.0) if revenue > 0 else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"{revenue:,.2f} ETB")
        col2.metric("Cost of Goods Sold", f"{cogs:,.2f} ETB")
        col3.metric("Net Profit", f"{profit:,.2f} ETB")
        col4.metric("Profit Margin", f"{margin:,.1f}%")

        st.markdown("---")

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("📈 Revenue & Profit by Company")
            if "Company" in df.columns:
                by_company = df.groupby("Company")[["Total_Sale", "Profit"]].sum()
                by_company.columns = ["Revenue", "Profit"]
                if not by_company.empty:
                    st.bar_chart(by_company)
                else:
                    st.info("No company data available.")
            else:
                st.info("No company data available.")

        with c2:
            st.subheader("🏆 Most Profitable Products")
            if "Product_Name" in df.columns:
                by_product = df.groupby("Product_Name")["Profit"].sum().sort_values(ascending=False).head(10)
                if not by_product.empty:
                    st.bar_chart(by_product)
                else:
                    st.info("No product data available.")
            else:
                st.info("No product data available.")

        st.markdown("---")
        st.subheader("📅 Revenue & Profit Over Time")
        by_day = df.groupby("Date_Str")[["Total_Sale", "Profit"]].sum().sort_index()
        by_day.columns = ["Revenue", "Profit"]
        if not by_day.empty:
            st.line_chart(by_day)
        else:
            st.info("Not enough data to chart a trend yet.")

        st.markdown("---")
        st.subheader("📋 Sale-by-Sale Breakdown")
        display_cols = [c for c in [
            "Sale_ID", "Date", "Company", "Product_Name", "Quantity",
            "Unit_Price", "Total_Sale", "Cost_of_Goods", "Profit", "Profit_Margin_%",
            "Payment_Method", "Receptionist"
        ] if c in df.columns]
        st.dataframe(df[display_cols].sort_values("Date", ascending=False), use_container_width=True)
