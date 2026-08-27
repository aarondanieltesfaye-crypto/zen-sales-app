import streamlit as st

st.title("📋 Inventory Management")

st.subheader("Adjust Stock Levels")
with st.form("adjust_stock_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        prod_id = st.text_input("Product ID", placeholder="e.g., SAB-B4CA6")
        adj_type = st.selectbox("Transaction Type", ["Restock", "Damage", "Correction", "Return"])
    with col2:
        qty = st.number_input("Quantity Change", step=1, help="Use negative numbers for losses/damages")
        receptionist = st.text_input("Receptionist Name")
    
    reason = st.text_area("Reason / Notes")
    
    submit = st.form_submit_button("Update Stock")
    if submit:
        if not prod_id:
            st.error("Please enter a Product ID.")
        else:
            st.success(f"Inventory updated for product '{prod_id}'!")

st.divider()
st.subheader("Low Stock Alerts")
st.warning("Low stock monitoring active. Items under threshold will display here.")
