import streamlit as st
from services.data_service import get_settings, save_settings

st.set_page_config(page_title="System Settings", page_icon="⚙️", layout="wide")

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
        border-radius: 8px;
        font-weight: 700;
        background-color: #87AE73;
        color: #0D1B12;
        border: none;
        padding: 0.61rem 1.2rem;
    }
    .stButton > button:hover {
        background-color: #A1C68E;
        color: #0D1B12;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ System Settings")

current_settings = get_settings()

try:
    default_threshold = int(current_settings.get("Default_Low_Stock_Threshold", 5))
except ValueError:
    default_threshold = 5

default_currency = current_settings.get("Currency", "ETB")

with st.container(border=True):
    st.subheader("Global Configurations")
    
    currency_input = st.text_input("Default Currency", value=default_currency)
    threshold_input = st.number_input("Global Low Stock Threshold", min_value=1, value=default_threshold)

    if st.button("Save Settings"):
        if save_settings(currency=currency_input, low_stock_threshold=threshold_input):
            st.success("Settings saved successfully!")
            st.rerun()
        else:
            st.error("Failed to save settings. Please try again.")
