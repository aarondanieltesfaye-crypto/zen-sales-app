import streamlit as st

st.set_page_config(page_title="Zen Apartments - Shop", layout="wide")

# Simple Role Selection for Prototype
if 'role' not in st.session_state:
    st.session_state['role'] = 'Receptionist'

with st.sidebar:
    st.title("Zen Shop Manager")
    role = st.selectbox("Current User Role:", ["Receptionist", "Admin"])
    st.session_state['role'] = role
    st.write("---")

    pages = {
        "Dashboard": "pages/dashboard.py",
        "Record Sale": "pages/sales.py",
        "Inventory": "pages/inventory.py",
        "Products": "pages/products.py",
        "Profit & Revenue": "pages/Profit.py",
        "Reports": "pages/reports.py",
        "Settings": "pages/settings.py"
    }

    selection = st.radio("Navigation", list(pages.keys()))

# Load the selected page
page_file = pages[selection]
with open(page_file, encoding="utf-8") as f:
    exec(f.read())
