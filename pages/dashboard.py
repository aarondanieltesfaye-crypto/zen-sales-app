import streamlit as st
import plotly.express as px
from services.data_service import get_sales, get_products
import pandas as pd

st.title("📊 Management Dashboard")

try:
    sales_df = get_sales()
    products_df = get_products()
    
    # Format dates
    if not sales_df.empty:
        sales_df['Date'] = pd.to_datetime(sales_df['Date'])
        active_sales = sales_df[sales_df['Status'] == 'Active']
        
        # KPI Metrics
        col1, col2, col3, col4 = st.columns(4)
        total_sales = active_sales['Total_Sale'].sum()
        total_revenue = active_sales['Zen_Revenue'].sum()
        units_sold = active_sales['Quantity'].sum()
        units_stock = products_df['Current_Stock'].sum() if not products_df.empty else 0
        
        col1.metric("Gross Sales (ETB)", f"{total_sales:,.2f}")
        col2.metric("Zen Revenue (ETB)", f"{total_revenue:,.2f}")
        col3.metric("Units Sold", f"{units_sold}")
        col4.metric("Total Stock", f"{units_stock}")
        
        st.write("---")
        
        # Charts
        c1, c2 = st.columns(2)
        with c1:
            sales_by_company = active_sales.groupby('Company')['Total_Sale'].sum().reset_index()
            fig1 = px.bar(sales_by_company, x='Company', y='Total_Sale', title="Gross Sales by Company", text_auto=True)
            st.plotly_chart(fig1, use_container_width=True)
            
        with c2:
            if not products_df.empty:
                stock_by_comp = products_df.groupby('Company')['Current_Stock'].sum().reset_index()
                fig2 = px.pie(stock_by_comp, names='Company', values='Current_Stock', title="Inventory Distribution")
                st.plotly_chart(fig2, use_container_width=True)

        # Low Stock Warnings
        st.subheader("⚠️ Low Stock Warnings")
        # Assume setting threshold is 5 for now
        low_stock = products_df[products_df['Current_Stock'] <= 5]
        if not low_stock.empty:
            st.dataframe(low_stock[['Company', 'Product_Name', 'Current_Stock']], hide_index=True)
        else:
            st.success("All products have sufficient stock.")

    else:
        st.info("No sales data available yet.")
        
except Exception as e:
    st.error("Error loading dashboard. Please check Google Sheets connection.")
