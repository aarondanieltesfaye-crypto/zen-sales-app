import streamlit as st
from services.data_service import get_products, record_sale

st.title("🛒 Record a Sale")

products_df = get_products()

if products_df.empty:
    st.warning("No active products found in inventory. Please add products first.")
else:
    # 1. Company Selection
    if "Company" in products_df.columns:
        companies = sorted(products_df["Company"].dropna().unique().tolist())
        selected_company = st.selectbox("Company", companies)
        filtered_products = products_df[products_df["Company"] == selected_company]
    else:
        selected_company = "-"
        filtered_products = products_df

    # 2. Product Selection
    if not filtered_products.empty and "Product_Name" in filtered_products.columns:
        product_names = filtered_products["Product_Name"].tolist()
        selected_product_name = st.selectbox("Product", product_names)
        
        # Get exact row for selected product
        product_row = filtered_products[filtered_products["Product_Name"] == selected_product_name].iloc[0]
        
        # Safely extract Product ID if column exists
        product_id = str(product_row.get("Product_ID", product_row.get("ID", "-")))
        
        # Safely extract price trying multiple common column names
        unit_price = 0.0
        for col in ["Price", "Unit_Price", "Selling_Price", "Unit_Selling_Price"]:
            if col in product_row and pd.notna(product_row[col]):
                try:
                    unit_price = float(product_row[col])
                    break
                except ValueError:
                    continue
    else:
        st.error("No products found for this company.")
        selected_product_name = "-"
        product_id = "-"
        unit_price = 0.0

    # 3. Form Inputs
    quantity = st.number_input("Quantity", min_value=1, value=1)
    
    # Display the fetched unit price for clarity
    st.write(f"Unit Price: **{unit_price:,.2f} ETB**")

    payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Credit"])
    buyer_name = st.text_input("Buyer Name (Optional)")
    notes = st.text_input("Notes (Optional)")

    # Calculate gross total
    gross_total = quantity * unit_price
    st.info(f"Gross Total: ETB {gross_total:,.2f}")

    if st.button("Complete Sale"):
        success = record_sale(
            product_id=product_id,
            company=selected_company,
            product_name=selected_product_name,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=gross_total,
            payment_method=payment_method,
            buyer_name=buyer_name,
            notes=notes
        )
        if success:
            st.success("Sale recorded successfully!")
        else:
            st.error("Error saving to database. Ensure connection is stable.")
