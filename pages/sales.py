import streamlit as st
from services.data_service import get_products, record_sale

st.title("🛒 Record a Sale")

# Fetch products dataframe
products_df = get_products()

if products_df.empty:
    st.warning("No active products found in inventory. Please add products first.")
else:
    # 1. Company Selection
    if "Company" in products_df.columns:
        companies = sorted(products_df["Company"].dropna().unique().tolist())
        selected_company = st.selectbox("Company", companies)
        
        # Filter products strictly by the selected company
        filtered_products = products_df[products_df["Company"] == selected_company]
    else:
        selected_company = "-"
        filtered_products = products_df

    # 2. Product Selection (now filtered)
    if not filtered_products.empty and "Product_Name" in filtered_products.columns:
        product_names = filtered_products["Product_Name"].tolist()
        selected_product_name = st.selectbox("Product", product_names)
        
        # Get details for the selected product row
        product_row = filtered_products[filtered_products["Product_Name"] == selected_product_name].iloc[0]
        
        # Automatically pull unit price and available stock if columns exist
        unit_price = float(product_row.get("Price", product_row.get("Unit_Price", 0.0)))
    else:
        st.error("No products found for this company.")
        selected_product_name = ""
        unit_price = 0.0

    # Rest of your sales form inputs...
    quantity = st.number_input("Quantity", min_value=1, value=1)
    payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Credit"])
    buyer_name = st.text_input("Buyer Name (Optional)")
    notes = st.text_input("Notes (Optional)")

    # Calculate gross total
    gross_total = quantity * unit_price
    st.info(f"Gross Total: ETB {gross_total:,.2f}")

    if st.button("Complete Sale"):
        success = record_sale(
            product_name=selected_product_name,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=gross_total,
            company=selected_company,
            buyer_name=buyer_name,
            notes=notes
        )
        if success:
            st.success("Sale recorded successfully!")
        else:
            st.error("Error saving to database. Ensure connection is stable.")
