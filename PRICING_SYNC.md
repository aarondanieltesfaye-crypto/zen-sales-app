# Pricing sync

The Streamlit app reads live product prices from the Google Sheet named `zenproducts` (Products tab), not from GitHub Excel files.

## What changed in this repo

- Added `utils/pricing.py` so every page resolves selling price and buying price from the same columns.
- Profit when a buying price exists: `(Selling Price - Buying Price) x Quantity`.
- Consignment items with buying price 0 still use the product commission.
- Products and Sales pages now display buying price.
- Migration script no longer treats Sabahar quantity as unit price.

## Catalog files

- Updated workbook with the `Buying price` column: upload `zenproducts.xlsx` from Drive (file also generated during this sync).
- Copy the `Buying price` column and corrected `Selling_Price` values into the live `zenproducts` Google Sheet so the running app picks them up.

Do not invent missing prices. Rows still missing a selling price are flagged in the sync notes (Danakil 45*200, some beach towels, table runner, timket shawl, Judith Shawl SAB-B088D, Bath Towel SAB-D405D, Glass Holder).
