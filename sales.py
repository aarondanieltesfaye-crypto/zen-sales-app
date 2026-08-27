import streamlit as st
from services.data_service import get_products, record_sale
from utils.validation import validate_sale_input

st.title("🛒 Record a Sale")

products_df = get_products()
if products_df.empty:
    st.warning("No active products found. Add products first.")
else:
    with st.form("sale_form"):
        col1, col2 = st.columns(2)
        with col1:
            company = st.selectbox("Company", products_df['Company'].unique())
            company_prods = products_df[products_df['Company'] == company]
            
            # Format product display: Name (Stock: X - Price: Y)
            prod_options = company_prods.apply(lambda row: f"{row['Product_Name']} (Stock: {row['Current_Stock']})", axis=1).tolist()
            selected_prod_str = st.selectbox("Product", prod_options)
            
            # Extract real product details
            idx = prod_options.index(selected_prod_str)
            selected_product = company_prods.iloc[idx]
            
            qty = st.number_input("Quantity", min_value=1, step=1)
            
        with col2:
            price = st.number_input("Selling Price (ETB)", value=float(selected_product['Selling_Price']))
            payment_method = st.selectbox("Payment Method", ["Cash", "CBE Transfer", "POS", "Gift", "Other"])
            buyer = st.text_input("Buyer Name (Optional)")
            notes = st.text_input("Notes (Optional)")
            
        st.info(f"Gross Total: ETB {qty * price:,.2f}")
        
        submitted = st.form_submit_button("Complete Sale", type="primary")
        
        if submitted:
            valid, msg = validate_sale_input(qty, int(selected_product['Current_Stock']), price)
            if not valid:
                st.error(msg)
            else:
                try:
                    record_sale(
                        product_id=selected_product['Product_ID'],
                        company=company,
                        product_name=selected_product['Product_Name'],
                        qty=qty,
                        unit_price=price,
                        payment_method=payment_method,
                        buyer=buyer,
                        receptionist=st.session_state.get("role", "Unknown"),
                        notes=notes
                    )
                    st.success("Sale recorded successfully!")
                except Exception as e:
                    st.error(f"Error saving to database. Ensure connection is stable.")