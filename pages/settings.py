import streamlit as st

st.title("⚙️ System Settings")

st.subheader("Global Configurations")
with st.form("settings_form"):
    currency = st.text_input("Default Currency", value="ETB")
    low_stock = st.number_input("Global Low Stock Threshold", min_value=1, value=5)
    
    submit = st.form_submit_button("Save Settings")
    if submit:
        st.success("Settings saved successfully!")
