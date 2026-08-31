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

def _get_or_create_worksheet(worksheet_name: str, headers: list = None):
    """Returns the worksheet, creating it (with a header row) if it doesn't exist yet."""
    sh = client.open(SPREADSHEET_NAME)
    try:
        return sh.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        cols = max(10, len(headers or []))
        ws = sh.add_worksheet(title=worksheet_name, rows=1000, cols=cols)
        if headers:
            ws.append_row(headers)
        return ws

def ensure_headers(worksheet_name: str, required_headers: list) -> bool:
    """
    Ensures the worksheet exists and its header row (row 1) contains every
    column in required_headers, appending any that are missing. This is what
    keeps a tab like 'Inventory_Transactions' self-healing/connected even if
    it was created empty or with a different column set.
    """
    try:
        if not client:
            return False
        ws = _get_or_create_worksheet(worksheet_name, headers=required_headers)
        existing = ws.row_values(1)
        if not existing:
            ws.append_row(required_headers)
            return True
        missing = [h for h in required_headers if h not in existing]
        if missing:
            ws.update("A1", [existing + missing])
        return True
    except Exception as e:
        st.error(f"Error ensuring headers for '{worksheet_name}': {e}")
        return False

def write_row_by_headers(worksheet_name: str, row_dict: dict, required_headers: list = None) -> bool:
    """
    Appends a row built from a dict, aligned to the worksheet's ACTUAL header
    order (read live from row 1) rather than assuming a fixed column position.
    Any column in required_headers/row_dict that the sheet doesn't have yet is
    added automatically. This is what keeps writers (Sales, Inventory_Transactions)
    reliably 'connected' regardless of how the sheet's columns are ordered.
    """
    try:
        if not client:
            return False
        headers_needed = required_headers or list(row_dict.keys())
        ensure_headers(worksheet_name, headers_needed)
        ws = _get_or_create_worksheet(worksheet_name, headers=headers_needed)
        headers = ws.row_values(1)
        row = [str(row_dict.get(h, "")) for h in headers]
        ws.append_row(row)
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
