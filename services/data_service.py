# services/data_service.py
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
from datetime import datetime
import json
import re
import os

# Hardcoded fallback spreadsheet ID (in case secrets don't load)
FALLBACK_SPREADSHEET_ID = "1Auhm-mnKHgr2YkvUfM0MebHgJ1GROrhXt1rVn3NjJs0"

def get_gs_client():
    """Get Google Sheets client using credentials from secrets.toml"""
    try:
        # Check if secrets are available
        if not hasattr(st, 'secrets'):
            st.error("Streamlit secrets not available. Please check your configuration.")
            return None
        
        # Check if gcp_service_account section exists
        if "gcp_service_account" not in st.secrets:
            st.error("'gcp_service_account' not found in secrets.toml. Please add it.")
            return None
        
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # Create credentials from the secrets dict
        creds_dict = {
            "type": st.secrets["gcp_service_account"]["type"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"],
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
            "token_uri": st.secrets["gcp_service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
            "universe_domain": st.secrets["gcp_service_account"].get("universe_domain", "googleapis.com")
        }
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def get_spreadsheet_id():
    """Get spreadsheet ID from secrets or use fallback"""
    try:
        # First try to get from secrets
        if "app" in st.secrets and "spreadsheet_id" in st.secrets["app"]:
            return st.secrets["app"]["spreadsheet_id"]
        else:
            # Use fallback
            st.warning(f"Using fallback spreadsheet ID: {FALLBACK_SPREADSHEET_ID}")
            return FALLBACK_SPREADSHEET_ID
    except Exception as e:
        st.warning(f"Error reading spreadsheet ID from secrets, using fallback: {e}")
        return FALLBACK_SPREADSHEET_ID

def get_sales():
    """Fetch sales data from Google Sheets"""
    try:
        client = get_gs_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet_id = get_spreadsheet_id()
        if spreadsheet_id is None:
            return pd.DataFrame()
        
        sheet = client.open_by_key(spreadsheet_id)
        
        # Try to get the Sales sheet
        try:
            worksheet = sheet.worksheet("Sales")
        except:
            # If Sales sheet doesn't exist, create it
            worksheet = sheet.add_worksheet(title="Sales", rows="1000", cols="20")
            headers = ["Sale_ID", "Date", "Product_ID", "Company", "Product_Name", 
                      "Quantity", "Unit_Selling_Price", "Zen_Revenue", "Cost_of_Goods",
                      "Profit", "Payment_Method", "Buyer", "Receptionist", "Notes"]
            worksheet.append_row(headers)
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Ensure numeric columns are properly typed
        for col in ["Quantity", "Unit_Selling_Price", "Zen_Revenue", "Cost_of_Goods", "Profit"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error fetching sales: {e}")
        return pd.DataFrame()

def get_products():
    """Fetch products from Google Sheets - uses the Zen Shop Excel data structure"""
    try:
        client = get_gs_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet_id = get_spreadsheet_id()
        if spreadsheet_id is None:
            return pd.DataFrame()
        
        sheet = client.open_by_key(spreadsheet_id)
        
        # Get all sheets and combine product data
        all_products = []
        
        # List of sheets that contain product data
        product_sheets = ["Sabahar", "Phone Case", "Leyu", "Hanfala Leather", 
                         "Elegance & Mela Studio", "Elisabeth Oil & Soap", 
                         "More Coffee & Ethio JAZZ", "Tilla Product", "Kalon Scarf",
                         "Nishan Honey", "Kuncho Leather", "Araya", "TruLove Granola",
                         "Afropian", "Yohannnes wood"]
        
        for sheet_name in product_sheets:
            try:
                worksheet = sheet.worksheet(sheet_name)
                data = worksheet.get_all_records()
                
                # Try to identify columns
                if data:
                    headers = data[0].keys() if data else []
                    
                    # Find relevant columns
                    id_col = None
                    desc_col = None
                    qty_col = None
                    price_col = None
                    buying_col = None
                    
                    for h in headers:
                        h_lower = h.lower()
                        if "id" in h_lower or "code" in h_lower or "nb" in h_lower:
                            id_col = h
                        if "description" in h_lower or "describ" in h_lower or "product" in h_lower:
                            desc_col = h
                        if "qty" in h_lower or "quantity" in h_lower:
                            qty_col = h
                        if "selling" in h_lower or "zen price" in h_lower or "price" in h_lower:
                            price_col = h
                        if "buying" in h_lower or "unit price" in h_lower or "cost" in h_lower:
                            buying_col = h
                    
                    # Extract products
                    for row in data:
                        # Check if quantity exists and is greater than 0
                        qty_val = row.get(qty_col, 0)
                        try:
                            qty_val = float(qty_val) if qty_val else 0
                        except:
                            qty_val = 0
                            
                        if qty_val > 0:
                            # Get product name, clean it up
                            product_name = str(row.get(desc_col, "")).strip()
                            if product_name and product_name not in ["", "None", "nan", "NaN"]:
                                # Get price values
                                price_val = row.get(price_col, 0)
                                try:
                                    price_val = float(price_val) if price_val else 0
                                except:
                                    price_val = 0
                                    
                                buying_val = row.get(buying_col, 0)
                                try:
                                    buying_val = float(buying_val) if buying_val else 0
                                except:
                                    buying_val = 0
                                
                                product = {
                                    "Company": sheet_name,
                                    "Product_ID": str(row.get(id_col, "")).strip(),
                                    "Product_Name": product_name,
                                    "Quantity": qty_val,
                                    "Unit_Selling_Price": price_val,
                                    "Buying_Price": buying_val,
                                    "Zen_Price": price_val
                                }
                                all_products.append(product)
            except Exception as e:
                # Skip sheets that don't exist or can't be read
                continue
        
        df = pd.DataFrame(all_products)
        
        # Clean up - remove products with missing names
        if not df.empty:
            df = df[df["Product_Name"].notna() & (df["Product_Name"] != "")]
            df = df[df["Product_Name"].str.strip() != ""]
            df = df.reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return pd.DataFrame()

def record_sale(product_id, company, product_name, quantity, unit_price, buying_price, 
               zen_revenue, total_amount, cost_of_goods, payment_method, 
               buyer_name, receptionist, notes):
    """Record a sale in Google Sheets"""
    try:
        client = get_gs_client()
        if client is None:
            return False
        
        spreadsheet_id = get_spreadsheet_id()
        if spreadsheet_id is None:
            return False
        
        sheet = client.open_by_key(spreadsheet_id)
        
        # Get or create Sales sheet
        try:
            worksheet = sheet.worksheet("Sales")
        except:
            worksheet = sheet.add_worksheet(title="Sales", rows="1000", cols="20")
            headers = ["Sale_ID", "Date", "Product_ID", "Company", "Product_Name", 
                      "Quantity", "Unit_Selling_Price", "Zen_Revenue", "Cost_of_Goods",
                      "Profit", "Payment_Method", "Buyer", "Receptionist", "Notes"]
            worksheet.append_row(headers)
        
        # Generate Sale ID
        sale_id = f"SALE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        profit = zen_revenue - cost_of_goods
        
        # Prepare row
        row = [
            sale_id,
            date,
            str(product_id),
            str(company),
            str(product_name),
            float(quantity),
            float(unit_price),
            float(zen_revenue),
            float(cost_of_goods),
            float(profit),
            str(payment_method),
            str(buyer_name) if buyer_name else "",
            str(receptionist) if receptionist else "",
            str(notes) if notes else ""
        ]
        
        # Append to sheet
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error recording sale: {e}")
        return False
