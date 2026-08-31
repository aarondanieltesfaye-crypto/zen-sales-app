import streamlit as st
from services.data_service import get_products_with_margin

st.title("📦 Product Management")

st.subheader("Add New Product")
with st.form("add_product_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Product Name")
        company = st.selectbox(
            "Company",
            ["Sabahar", "Phone Cases", "Leyu", "Hanfala Leather", "Elegance & Mela Studio"]
        )
        category = st.text_input("Category")
    with col2:
        price = st.number_input("Selling Price (ETB)", min_value=0.0, step=10.0)
        stock = st.number_input("Initial Stock", min_value=0, step=1)
        comm_val = st.number_input("Commission Value (%)", min_value=0.0, value=20.0)
    
    submit = st.form_submit_button("Save Product")
    if submit:
        if not name:
            st.error("Please enter a product name.")
        else:
            st.success(f"Product '{name}' added successfully!")

st.divider()
st.subheader("Product Catalog")

products_df = get_products_with_margin()

if products_df.empty:
    st.info("No products found in Google Sheets yet.")
else:
    display_cols = [c for c in [
        "Product_ID", "Company", "Product_Name", "Category",
        "Selling_Price", "Cost_Price", "Profit_Margin_%", "Est_Profit_Per_Unit",
        "Current_Stock", "Active"
    ] if c in products_df.columns]

    rename_map = {
        "Selling_Price": "Unit Price (ETB)",
        "Cost_Price": "Cost Price (ETB)",
        "Profit_Margin_%": "Profit Margin (%)",
        "Est_Profit_Per_Unit": "Est. Profit/Unit (ETB)",
        "Current_Stock": "Stock",
    }

    company_filter = st.multiselect(
        "Filter by Company",
        sorted(products_df["Company"].dropna().unique().tolist()) if "Company" in products_df.columns else []
    )
    view_df = products_df[display_cols].rename(columns=rename_map)
    if company_filter and "Company" in products_df.columns:
        view_df = view_df[products_df["Company"].isin(company_filter)]

    st.dataframe(view_df, use_container_width=True, hide_index=True)
    st.caption(
        "Profit Margin is Selling Price vs. Cost Price for products Zen owns (e.g. Phone Cases, "
        "Hanfala Leather), or the item's commission % for consignment products with no cost price "
        "(e.g. Sabahar, Leyu, Elegance & Mela Studio)."
    )
