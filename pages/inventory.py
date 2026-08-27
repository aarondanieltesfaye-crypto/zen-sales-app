import streamlit as st
import pandas as pd
from services.data_service import get_products, adjust_stock

st.set_page_config(page_title="Adjust Stock", page_icon="📦", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #2E6F40;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1D4729;
        border-radius: 12px;
        border: 1px solid #87AE73;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        background-color: #87AE73;
        color: #0D1B12;
        border: none;
        padding: 0.61rem 1rem;
    }
    .stButton > button:hover {
        background-color: #A1C68E;
        color: #0D1B12;
    }
</style>
""", unsafe_allow_html=True)

st.title("📦 Adjust Stock Levels")

products_df = get_products()

if products_df.empty:
    st.warning("No products found in Google Sheets.")
else:
    product_options = {}
    for _, row in products_df.iterrows():
        p_id = str(row.get("Product_ID", ""))
        p_name = str(row.get("Product_Name", ""))
        curr_stock = str(row.get("Current_Stock", "0"))
        if p_id:
            product_options[f"{p_id} - {p_name} (Current Stock: {curr_stock})"] = p_id

    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            selected_label = st.selectbox("Product ID / Name", list(product_options.keys()))
            selected_pid = product_options[selected_label]
            transaction_type = st.selectbox("Transaction Type", ["Restock", "Damage", "Waste", "Personal Use", "Correction"])
            
        with col2:
            quantity_change = st.number_input("Quantity Change", min_value=1, value=1)
            receptionist = st.text_input("Receptionist Name", value="-")

        reason = st.text_area("Reason / Notes", value="")

        if st.button("Update Stock"):
            if adjust_stock(
                product_id=selected_pid,
                quantity_change=quantity_change,
                transaction_type=transaction_type,
                receptionist=receptionist,
                reason=reason
            ):
                st.success(f"Inventory successfully updated for product '{selected_pid}'!")
                st.rerun()
            else:
                st.error("Failed to update inventory. Please check connection.")
