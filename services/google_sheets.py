import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SPREADSHEET_NAME = "zenproducts"

@st.cache_resource
def get_gspread_client():
    """Authenticates and returns a gspread client instance using Streamlit secrets."""
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        elif "textkey" in st.secrets:
            creds_dict = dict(st.secrets["textkey"])
        elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds_dict = dict(st.secrets["connections"]["gsheets"])
        else:
            creds_dict = dict(st.secrets)

        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Failed to authenticate with Google Sheets: {e}")
        return None

client = get_gspread_client()

def fetch_worksheet_data(worksheet_name: str) -> pd.DataFrame:
    """Safely fetches worksheet data using raw matrix values to prevent header duplication errors."""
    try:
        if not client:
            return pd.DataFrame()

        ws = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)
        data = ws.get_all_values()

        if not data:
            return pd.DataFrame()

        headers = data[0]
        clean_headers = []
        seen = {}

        for i, h in enumerate(headers):
            h_str = str(h).strip()
            if not h_str:
                h_str = f"Col_{i+1}"
            if h_str in seen:
                seen[h_str] += 1
                h_str = f"{h_str}_{seen[h_str]}"
            else:
                seen[h_str] = 0
            clean_headers.append(h_str)

        return pd.DataFrame(data[1:], columns=clean_headers)
    except Exception as e:
        st.error(f"Error fetching sheet '{worksheet_name}': {e}")
        return pd.DataFrame()

def write_row(worksheet_name: str, row_data: list) -> bool:
    """Appends a single row to the target worksheet."""
    try:
        if not client:
            return False
        ws = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)
        ws.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Error appending row to '{worksheet_name}': {e}")
        return False

def update_data(worksheet_name: str, df: pd.DataFrame) -> bool:
    """Clears and rewrites a worksheet with the updated DataFrame."""
    try:
        if not client:
            return False
        ws = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)
        ws.clear()

        updated_data = [df.columns.tolist()] + df.astype(str).values.tolist()
        ws.update("A1", updated_data)
        return True
    except Exception as e:
        st.error(f"Error updating sheet '{worksheet_name}': {e}")
        return False
