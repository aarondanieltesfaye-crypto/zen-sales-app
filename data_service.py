import pandas as pd
import uuid
from datetime import datetime
from services.google_sheets import fetch_worksheet_data, write_row, update_dataframe
from utils.calculations import calculate_zen_revenue

def get_products():
    df = fetch_worksheet_data("Products")
    return df[df['Active'] == 'TRUE'] if not df.empty else df

def get_sales():
    return fetch_worksheet_data("Sales")

def get_inventory_transactions():
    return fetch_worksheet_data("Inventory_Transactions")

def get_settings():
    return fetch_worksheet_data("Settings")

def record_sale(product_id, company, product_name, qty, unit_price, payment_method, buyer, receptionist, notes):
    products = get_products()
    product = products[products['Product_ID'] == product_id].iloc[0]
    
    # Calculate revenue
    gross_sale = qty * unit_price
    comm_type = product['Commission_Type']
    comm_val = product['Commission_Value']
    zen_revenue = calculate_zen_revenue(gross_sale, qty, comm_type, comm_val)
    
    sale_id = f"SALE-{uuid.uuid4().hex[:8].upper()}"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Write Sale
    sale_row = [sale_id, date_str, product_id, company, product_name, qty, unit_price, 
                gross_sale, zen_revenue, payment_method, buyer, receptionist, notes, "Active", date_str]
    write_row("Sales", sale_row)
    
    # 2. Record Inventory Transaction
    trans_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    txn_row = [trans_id, date_str, product_id, company, product_name, "Sale", -qty, f"Sale {sale_id}", receptionist, date_str]
    write_row("Inventory_Transactions", txn_row)
    
    # 3. Update Current Stock in Products sheet
    update_product_stock(product_id, -qty)
    return sale_id

def update_product_stock(product_id, qty_change):
    products_df = fetch_worksheet_data("Products")
    row_idx = products_df.index[products_df['Product_ID'] == product_id].tolist()[0]
    new_stock = int(products_df.at[row_idx, 'Current_Stock']) + qty_change
    products_df.at[row_idx, 'Current_Stock'] = new_stock
    update_dataframe("Products", products_df)

def adjust_inventory(product_id, qty_change, reason, receptionist, notes):
    products = get_products()
    product = products[products['Product_ID'] == product_id].iloc[0]
    
    trans_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    txn_row = [trans_id, date_str, product_id, product['Company'], product['Product_Name'], 
               reason, qty_change, notes, receptionist, date_str]
    write_row("Inventory_Transactions", txn_row)
    update_product_stock(product_id, qty_change)