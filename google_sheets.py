import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from google.oauth2.service_account import Credentials

def get_google_client():
    """Authenticates and returns the gspread client using Streamlit secrets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    return client

def get_sheet():
    client = get_google_client()
    sheet_id = st.secrets["app"]["spreadsheet_id"]
    return client.open_by_key(sheet_id)

@st.cache_data(ttl=60)
def fetch_worksheet_data(worksheet_name):
    """Fetches data and caches it for 60 seconds unless manually cleared."""
    sheet = get_sheet().worksheet(worksheet_name)
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def write_row(worksheet_name, row_data):
    sheet = get_sheet().worksheet(worksheet_name)
    sheet.append_row(row_data)
    st.cache_data.clear() # Clear cache to refresh dashboard

def update_cell(worksheet_name, row_idx, col_idx, val):
    sheet = get_sheet().worksheet(worksheet_name)
    sheet.update_cell(row_idx, col_idx, val)
    st.cache_data.clear()
    
def update_dataframe(worksheet_name, df):
    """Overwrites the worksheet with a new DataFrame (useful for full re-syncs)."""
    sheet = get_sheet().worksheet(worksheet_name)
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    st.cache_data.clear()