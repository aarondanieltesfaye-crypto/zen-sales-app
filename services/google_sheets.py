import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Define Google Sheets API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gspread_client():
    """Authenticates with Google Sheets API using Streamlit Secrets."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(credentials)

def get_spreadsheet():
    """Opens the target spreadsheet using the ID stored in secrets."""
    client = get_gspread_client()
    spreadsheet_id = st.secrets["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id)

@st.cache_data(ttl=600)
def fetch_worksheet_data(worksheet_name: str) -> pd.DataFrame:
    """
    Fetches data from a specific tab and caches it in memory for 10 minutes (600s).
    This prevents continuous API calls and stops CPU throttling errors.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching sheet '{worksheet_name}': {e}")
        return pd.DataFrame()

def write_row(worksheet_name: str, row_data: list) -> bool:
    """
    Appends a new row to the specified tab and clears the cache
    so the app displays the new data immediately.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet(worksheet_name)
        worksheet.append_row(row_data)
        # Clear cache so subsequent reads fetch fresh data
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error writing to sheet '{worksheet_name}': {e}")
        return False
