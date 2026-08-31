import streamlit as st
import pandas as pd
from services.data_service import get_products, record_sale
from datetime import datetime

st.set_page_config(page_title="Record Sale", page_icon="🛒", layout="wide")

st.markdown("""
<style>
    /* Forest Green Card Backgrounds with Sage Green Accent Borders */
    div[data-testid="stMetric"] {
        background-color: #2E6F40;
        padding: 18px;
        border-radius: 12px;
        border: 2px solid #87AE73;
    }
    
    /* Sage Green Interactive Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        background-color: #87AE73;
        color: #0D1B12;
        border: none;
        padding: 0.61rem 1rem;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #2E6F40;
        color: #FFFFFF;
        border: 1px solid #87AE73;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛒 Record a Sale")

products_df = get_products()

if products_df.empty:
    st.warning("No active products found in inventory. Please add products first.")
else:
    with st.container(border=True):
        st.subheader("📦 Item Selection")
        col1, col2 = st.columns(2)
        
        with col1:
            if "Company" in products_df.columns:
                companies = sorted(products_df["Company"].dropna().unique().tolist())
                selected_company = st.selectbox("Company", companies)
                filtered_products = products_df[products_df["Company"] == selected_company]
            else:
                selected_company = "-"
                filtered_products = products_df

        with col2:
            if not filtered_products.empty and "Product_Name" in filtered_products.columns:
                product_names = filtered_products["Product_Name"].tolist()
                selected_product_name = st.selectbox("Product", product_names)
                
                product_row = filtered_products[filtered_products["Product_Name"] == selected_product_name].iloc[0]
                product_id = str(product_row.get("Product_ID", product_row.get("ID", "-")))
                
                # Get Zen Revenue (Selling Price)
                unit_price = 0.0
                for col in ["Price", "Unit_Price", "Selling_Price", "Unit_Selling_Price", "Zen_Price"]:
                    if col in product_row and pd.notna(product_row[col]):
                        try:
                            unit_price = float(product_row[col])
                            break
                        except ValueError:
                            continue
                
                # Get Cost/Buying Price for profit calculation
                buying_price = 0.0
                for col in ["Buying_Price", "Unit_Price_Tilla", "Cost", "Abel_price"]:
                    if col in product_row and pd.notna(product_row[col]):
                        try:
                            buying_price = float(product_row[col])
                            break
                        except ValueError:
                            continue
            else:
                st.error("No products found for this company.")
                selected_product_name = "-"
                product_id = "-"
                unit_price = 0.0
                buying_price = 0.0

    with st.container(border=True):
        st.subheader("💳 Transaction Details")
        col3, col4 = st.columns(2)
        
        with col3:
            quantity = st.number_input("Quantity", min_value=1, value=1)
            payment_method = st.selectbox("Payment Method", ["Cash", "Card", "Bank Transfer", "Credit", "POS Hibret", "CBE Transfer", "Telebirr"])
        
        with col4:
            buyer_name = st.text_input("Buyer Name (Optional)")
            receptionist = st.text_input("Receptionist Name", placeholder="Enter your name")
            notes = st.text_input("Notes (Optional)")

    # Calculate totals
    zen_revenue = quantity * unit_price
    cost_of_goods = quantity * buying_price
    profit = zen_revenue - cost_of_goods
    
    # Display metrics
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Zen Revenue", f"{zen_revenue:,.2f} ETB", delta=f"Unit Price: {unit_price:,.2f} ETB")
    if buying_price > 0:
        col_b.metric("Cost of Goods", f"{cost_of_goods:,.2f} ETB", delta=f"Unit Cost: {buying_price:,.2f} ETB")
        col_c.metric("💰 Profit", f"{profit:,.2f} ETB", delta=f"Margin: {(profit/zen_revenue*100):.1f}%" if zen_revenue > 0 else "0%")
    else:
        col_b.metric("Cost of Goods", "N/A (Cost data not available)")
        col_c.metric("💰 Profit", "N/A (Cost data not available)")

    if st.button("Complete Sale", type="primary"):
        if not receptionist:
            st.warning("⚠️ Please enter the receptionist name.")
        else:
            success = record_sale(
                product_id=product_id,
                company=selected_company,
                product_name=selected_product_name,
                quantity=quantity,
                unit_price=unit_price,  # Zen Revenue per unit
                buying_price=buying_price,  # Cost per unit
                zen_revenue=zen_revenue,  # Total Zen Revenue
                total_amount=zen_revenue,  # Total amount (same as Zen Revenue)
                cost_of_goods=cost_of_goods,  # Total cost
                payment_method=payment_method,
                buyer_name=buyer_name,
                receptionist=receptionist,
                notes=notes
            )
            if success:
                st.success(f"✅ Sale recorded successfully! Zen Revenue: {zen_revenue:,.2f} ETB")
                st.balloons()
            else:
                st.error("❌ Error saving to database. Ensure connection is stable.")
