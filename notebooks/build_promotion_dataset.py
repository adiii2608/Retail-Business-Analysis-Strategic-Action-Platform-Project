import pandas as pd
import numpy as np

# ---- Paths (adjust if needed) ----
CLTV_FILE = r"E:\c drive\amazon\notebooks\cltv_with_predictions.csv"
CHURN_FILE = r"E:\c drive\amazon\notebooks\cltv_with_churn_risk.csv"   # merge if separate; else skip
RAW_FILE  = r"E:\c drive\amazon\data\online_retail\online_retail_II.xlsx"

OUTPUT_FILE = "promotion_dataset.csv"

# ---- Load ----
cltv = pd.read_csv(CLTV_FILE)
try:
    churn = pd.read_csv(CHURN_FILE)
except FileNotFoundError:
    churn = pd.DataFrame()

# Standardize column names
cltv.columns = cltv.columns.str.strip().str.replace(' ', '_')
if not churn.empty:
    churn.columns = churn.columns.str.strip().str.replace(' ', '_')

# Merge churn prob if present
if not churn.empty and 'Churn_Prob' in churn.columns:
    if 'Customer_ID' not in churn.columns and 'CustomerId' in churn.columns:
        churn.rename(columns={'CustomerId':'Customer_ID'}, inplace=True)
    cltv = cltv.merge(churn[['Customer_ID','Churn_Prob']], on='Customer_ID', how='left')

# Fill missing churn prob with 0.3 baseline
if 'Churn_Prob' not in cltv.columns:
    cltv['Churn_Prob'] = 0.3
cltv['Churn_Prob'] = cltv['Churn_Prob'].fillna(0.3)

# ---- Last purchase extraction ----
raw = pd.read_excel(RAW_FILE, parse_dates=['InvoiceDate'])
raw = raw[raw['Quantity'] > 0]
raw = raw[raw['Price'] > 0]
raw = raw.dropna(subset=['Customer ID'])
raw.rename(columns={'Customer ID':'Customer_ID'}, inplace=True)

last_purchase = (
    raw.sort_values('InvoiceDate')
        .groupby('Customer_ID')
        .agg(Last_Purchase_Date=('InvoiceDate','max'),
             Last_Product=('Description','last'))
        .reset_index()
)

dataset = cltv.merge(last_purchase, on='Customer_ID', how='left')

# Days since last purchase relative to snapshot
snapshot_date = raw['InvoiceDate'].max() + pd.Timedelta(days=1)
dataset['Days_Since_Last_Purchase'] = (snapshot_date - dataset['Last_Purchase_Date']).dt.days

# Value tier mapping
def map_value(row):
    seg = str(row.get('CLTV_Segment') or row.get('CLTV_Segment_Label') or "").upper()
    # Accept variants
    if seg in ['A','TOP','HIGHVALUE','TOP_CUSTOMER']: return 'Top'
    if seg in ['B','HIGH']: return 'High'
    if seg in ['C','MEDIUM']: return 'Medium'
    return 'Low'

if 'CLTV_Segment_Label' not in dataset.columns and 'CLTV_Segment' in dataset.columns:
    dataset['CLTV_Segment_Label'] = dataset['CLTV_Segment']

dataset['Value_Tier'] = dataset.apply(map_value, axis=1)

# Fallback Recency field
if 'Recency' not in dataset.columns:
    dataset['Recency'] = dataset['Days_Since_Last_Purchase']

# Risk flag
dataset['At_Risk'] = (
    (dataset['Churn_Prob'] >= 0.5) |
    (dataset['Recency'] > 90)
).astype(int)

# ---- Rule-based Promotion Class ----
def assign_promo(row):
    tier = row['Value_Tier']
    churn = row['Churn_Prob']
    rec = row['Recency']
    at_risk = row['At_Risk']

    if tier == 'Top':
        return 'VIP_LOYALTY'
    if tier == 'High':
        return 'HIGH_VALUE_SAVE' if at_risk else 'UPSWING_UPSELL'
    if tier == 'Medium':
        return 'MID_SAVE' if at_risk else 'CROSS_SELL'
    if tier == 'Low':
        return 'WINBACK' if at_risk else 'LIGHT_NURTURE'
    return 'LIGHT_NURTURE'

dataset['Promotion_Class'] = dataset.apply(assign_promo, axis=1)

# Minimal optional recommendation placeholder (you could merge from item similarity)
dataset['Suggested_Offer_Text'] = dataset['Promotion_Class'].map({
    'VIP_LOYALTY': 'Early access + exclusive bundle',
    'UPSWING_UPSELL': 'Bundle offer on premium related item',
    'HIGH_VALUE_SAVE': 'Personalized 15% retention voucher',
    'CROSS_SELL': 'Add complementary product recommendation',
    'MID_SAVE': 'Limited 10% coupon + loyalty enrollment',
    'WINBACK': 'Reactivate: 20% comeback code',
    'LIGHT_NURTURE': 'Low-cost email drip series'
})

dataset.to_csv(OUTPUT_FILE, index=False)
print("Saved:", OUTPUT_FILE)
print(dataset.head())
