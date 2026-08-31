import pandas as pd
import uuid

# Make sure this matches your Excel file name exactly
file_path = "Zen Shop- Products Sales -report.xlsx"
xls = pd.ExcelFile(file_path)

products = []

def clean_val(val, default=0):
    try:
        if pd.isna(val): return default
        val_str = str(val).replace(',', '').strip()
        return float(val_str)
    except:
        return default

def looks_like_header(name):
    if not isinstance(name, str):
        return True
    lowered = name.strip().lower()
    return (
        len(lowered) <= 1
        or "description" in lowered
        or "describtion" in lowered
        or lowered in {"total", "inventory", "nb", "id"}
        or lowered.startswith("new arrivals")
        or lowered.startswith("febrary")
        or lowered.startswith("oct ")
    )

# 1. Sabahar
# Different Sabahar blocks use different column layouts. Prefer a column
# whose header is Price / Unit Price / Selling Price rather than Quantity.
try:
    df_sab_raw = pd.read_excel(xls, sheet_name="Sabahar", header=None)
    current_headers = None
    for _, row in df_sab_raw.iterrows():
        values = [row.iloc[i] if i < len(row) else None for i in range(len(row))]
        texts = [str(v).strip().lower() if pd.notna(v) else "" for v in values]
        if "description" in texts or "describtion" in texts:
            current_headers = texts
            continue
        if current_headers is None:
            continue
        name = values[3] if len(values) > 3 else None
        if looks_like_header(name):
            continue

        qty = 0.0
        price = 0.0
        buying = 0.0
        for idx, header in enumerate(current_headers):
            if header in {"qty", "quantity"} and qty == 0:
                qty = clean_val(values[idx] if idx < len(values) else None)
            if header in {"unit price", "buying price"} and buying == 0:
                buying = clean_val(values[idx] if idx < len(values) else None)
            if header in {"price", "unit price", "selling price", "selling price "} and price == 0:
                candidate = clean_val(values[idx] if idx < len(values) else None)
                if "selling" in header:
                    price = candidate
                elif price == 0:
                    price = candidate
        for idx, header in enumerate(current_headers):
            if "selling" in header:
                candidate = clean_val(values[idx] if idx < len(values) else None)
                if candidate > 0:
                    price = candidate
        if price == 0:
            price = clean_val(values[7] if len(values) > 7 else None)
            if 0 < price <= 20 and len(values) > 8:
                maybe_unit = clean_val(values[8])
                if maybe_unit > price:
                    price = maybe_unit

        products.append({
            "Product_ID": f"SAB-{uuid.uuid4().hex[:5].upper()}",
            "Company": "Sabahar",
            "Product_Name": str(name).strip(),
            "Category": "Textiles",
            "Initial_Stock": int(qty),
            "Current_Stock": int(qty),
            "Cost_Price": buying,
            "Buying price": buying,
            "Selling_Price": price,
            "Commission_Type": "Percentage",
            "Commission_Value": 20,
            "Active": "TRUE",
            "Low_Stock_Threshold": 5
        })
except Exception as e:
    print(f"Sabahar error: {e}")

# 2. Phone Case
try:
    df_pc = pd.read_excel(xls, sheet_name='Phone Case')
    for idx, row in df_pc.iterrows():
        name = row.iloc[2] if len(row) > 2 else None
        if pd.notna(name) and isinstance(name, str) and "description" not in name.lower():
            qty = clean_val(row.iloc[3])
            unit_price = clean_val(row.iloc[4])
            selling_price = clean_val(row.iloc[6], default=unit_price)
            products.append({
                "Product_ID": f"PHN-{uuid.uuid4().hex[:5].upper()}",
                "Company": "Phone Cases",
                "Product_Name": name.strip(),
                "Category": "Accessories",
                "Initial_Stock": int(qty),
                "Current_Stock": int(qty),
                "Cost_Price": unit_price,
                "Buying price": unit_price,
                "Selling_Price": selling_price if selling_price > 0 else unit_price,
                "Commission_Type": "Percentage",
                "Commission_Value": 20,
                "Active": "TRUE",
                "Low_Stock_Threshold": 5
            })
except Exception as e:
    print(f"Phone Case error: {e}")

# 3. Leyu
try:
    df_leyu = pd.read_excel(xls, sheet_name='Leyu')
    for idx, row in df_leyu.iterrows():
        name = row.iloc[2] if len(row) > 2 else None
        if pd.notna(name) and isinstance(name, str) and "description" not in name.lower() and name.strip().lower() != "inventory":
            qty = clean_val(row.iloc[3])
            price = clean_val(row.iloc[4])
            products.append({
                "Product_ID": f"LEY-{uuid.uuid4().hex[:5].upper()}",
                "Company": "Leyu",
                "Product_Name": name.strip(),
                "Category": "Textiles",
                "Initial_Stock": int(qty),
                "Current_Stock": int(qty),
                "Cost_Price": 0,
                "Buying price": 0,
                "Selling_Price": price,
                "Commission_Type": "Percentage",
                "Commission_Value": 20,
                "Active": "TRUE",
                "Low_Stock_Threshold": 5
            })
except Exception as e:
    print(f"Leyu error: {e}")

# 4. Hanfala Leather
try:
    df_han = pd.read_excel(xls, sheet_name='Hanfala Leather', skiprows=1)
    for idx, row in df_han.iterrows():
        name = row.iloc[1] if len(row) > 1 else None
        if pd.notna(name) and isinstance(name, str) and name.strip() != "" and "inventory" not in name.lower() and "new arrivals" not in name.lower():
            qty = clean_val(row.iloc[2])
            cost = clean_val(row.iloc[4])
            price = clean_val(row.iloc[6])
            products.append({
                "Product_ID": f"HAN-{uuid.uuid4().hex[:5].upper()}",
                "Company": "Hanfala Leather",
                "Product_Name": name.strip(),
                "Category": "Leather Goods",
                "Initial_Stock": int(qty),
                "Current_Stock": int(qty),
                "Cost_Price": cost,
                "Buying price": cost,
                "Selling_Price": price,
                "Commission_Type": "Percentage",
                "Commission_Value": 20,
                "Active": "TRUE",
                "Low_Stock_Threshold": 5
            })
except Exception as e:
    print(f"Hanfala Leather error: {e}")

# 5. Elegance & Mela Studio
try:
    df_ele = pd.read_excel(xls, sheet_name='Elegance & Mela Studio', skiprows=1)
    for idx, row in df_ele.iterrows():
        name = row.iloc[1] if len(row) > 1 else None
        if pd.notna(name) and isinstance(name, str) and name.strip() != "":
            qty = clean_val(row.iloc[2])
            cost = clean_val(row.iloc[3])
            price = clean_val(row.iloc[4])
            products.append({
                "Product_ID": f"ELE-{uuid.uuid4().hex[:5].upper()}",
                "Company": "Elegance & Mela Studio",
                "Product_Name": name.strip(),
                "Category": "Bags & Leather",
                "Initial_Stock": int(qty),
                "Current_Stock": int(qty),
                "Cost_Price": cost,
                "Buying price": cost,
                "Selling_Price": price,
                "Commission_Type": "Percentage",
                "Commission_Value": 20,
                "Active": "TRUE",
                "Low_Stock_Threshold": 5
            })
except Exception as e:
    print(f"Elegance error: {e}")

df_out = pd.DataFrame(products)
df_out.to_csv("Normalized_Products.csv", index=False)
print(f"Migration complete! Generated Normalized_Products.csv with {len(df_out)} products.")
