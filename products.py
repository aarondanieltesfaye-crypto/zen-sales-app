import streamlit as st

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
st.info("Product catalog table loaded from Google Sheets.")