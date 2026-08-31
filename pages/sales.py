import streamlit as st
import pandas as pd
from services.data_service import get_products, record_sale, compute_line_cost_and_profit
from utils.pricing import get_buying_price, get_selling_price
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
                product_id = str(product_row.get("Product_ID", "-"))
                unit_price = get_selling_price(product_row)
                buying_price = get_buying_price(product_row)
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

    # Calculate totals from the Products sheet prices
    zen_revenue = quantity * unit_price
    cost_of_goods, profit = compute_line_cost_and_profit(product_id, quantity, zen_revenue)
    margin_pct = (profit / zen_revenue * 100.0) if zen_revenue > 0 else 0.0

    # Display metrics
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Zen Revenue", f"{zen_revenue:,.2f} ETB", delta=f"Unit Price: {unit_price:,.2f} ETB")
    col_b.metric("Cost of Goods / Payout", f"{cost_of_goods:,.2f} ETB", delta=f"Buying price: {buying_price:,.2f} ETB")
    col_c.metric("💰 Profit", f"{profit:,.2f} ETB", delta=f"Margin: {margin_pct:.1f}%" if zen_revenue > 0 else "0%")

    if st.button("Complete Sale", type="primary"):
        if not receptionist:
            st.warning("⚠️ Please enter the receptionist name.")
        else:
            success = record_sale(
                product_id=product_id,
                company=selected_company,
                product_name=selected_product_name,
                quantity=quantity,
                unit_price=unit_price,
                buying_price=buying_price,
                zen_revenue=zen_revenue,
                total_amount=zen_revenue,
                cost_of_goods=cost_of_goods,
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
