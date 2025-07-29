import pandas as pd

# Step 1: Load required columns only (faster)
use_cols = ['InvoiceDate', 'Description', 'Quantity']
df = pd.read_excel(
    r"E:\c drive\project\data\online_retail\online_retail_II.xlsx",
    sheet_name="Year 2009-2010",
    usecols=use_cols
)

# Step 2: Parse dates afterward (faster)
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')

# Step 3: Drop rows with missing dates or descriptions
df = df.dropna(subset=['InvoiceDate', 'Description'])

# Extract month/year
df['Month'] = df['InvoiceDate'].dt.month
df['Year'] = df['InvoiceDate'].dt.year

# Standardize description
df['Description'] = df['Description'].astype(str).str.upper()

# Step 4: Festival tagging logic
def assign_festival(row):
    desc = row['Description']
    month = row['Month']
    
    if any(x in desc for x in ['CHRISTMAS', 'XMAS']) and month == 12:
        return 'Christmas'
    elif month in [10, 11] and not any(x in desc for x in ['CHRISTMAS', 'XMAS']):
        return 'Diwali'
    else:
        return None

df['Festival'] = df.apply(assign_festival, axis=1)
festival_df = df[df['Festival'].notnull()]

# Step 5: Group and get top 10 per festival
top_products = (
    festival_df.groupby(['Festival', 'Description'])['Quantity']
    .sum()
    .reset_index()
    .sort_values(['Festival', 'Quantity'], ascending=[True, False])
)

top_n_per_festival = (
    top_products.groupby('Festival')
    .head(10)
    .reset_index(drop=True)
)

# Step 6: Save result
top_n_per_festival.to_csv("festival_top_products.csv", index=False)
print("✅ File saved: festival_top_products.csv")
