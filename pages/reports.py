import streamlit as st

st.title("📊 Sales & Inventory Reports")

# Top Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales Today", "0 ETB")
col2.metric("Items Sold Today", "0")
col3.metric("Total Revenue (Month)", "0 ETB")

st.divider()

# Visualization Columns
col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    st.subheader("Sales by Company")
    st.info("Sales breakdowns will display here.")

with col_chart2:
    st.subheader("Top Selling Products")
    st.info("Top performing inventory items will display here.")
