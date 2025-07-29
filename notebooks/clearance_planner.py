# clearance_planner.py  (no chart version)
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

DATA_FILE = r"E:\c drive\project\notebooks\outputs_top_items\outputs_low_sellers\bottom10_products_monthly.csv"
OUT_DIR = Path(r"E:\c drive\project\notebooks\outputs_low_sellers")
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE = OUT_DIR / r"E:\c drive\project\notebooks\outputs_low_sellers\clearance_recommendations.csv"

BASE_MARGIN = 0.30
ELASTICITY = -1.2

def load_data(file_path):
    df = pd.read_csv(file_path)
    df['YearMonth'] = pd.to_datetime(df['YearMonth'], errors='coerce')
    df['Month_Quantity'] = df['Month_Quantity'].fillna(0)
    return df

full_df = load_data(DATA_FILE)

def build_features(df):
    feat = (
        df.groupby('Description')
        .agg(
            Avg_Monthly_Quantity=('Month_Quantity', 'mean'),
            Std_Monthly_Quantity=('Month_Quantity', 'std'),
            Total_Value=('Month_Value', 'sum'),
            Months_Active=('Month_Quantity', lambda x: (x > 0).sum())
        ).reset_index()
    )
    total_months = df['YearMonth'].nunique()
    zero_sales = (
        df.groupby('Description')['Month_Quantity']
        .apply(lambda x: (x == 0).sum() / len(x))
        .reset_index(name='Zero_Sales_Ratio')
    )
    feat = feat.merge(zero_sales, on='Description')
    last_sale = (
        df[df['Month_Quantity'] > 0]
        .groupby('Description')['YearMonth']
        .max()
        .reset_index(name='Last_Sale_Date')
    )
    max_month = df['YearMonth'].max()
    last_sale['Last_Sale_Months_Ago'] = ((max_month - last_sale['Last_Sale_Date']).dt.days // 30)
    feat = feat.merge(last_sale[['Description', 'Last_Sale_Months_Ago']], on='Description', how='left')
    feat['Last_Sale_Months_Ago'] = feat['Last_Sale_Months_Ago'].fillna(total_months)
    feat['CV_Monthly_Quantity'] = feat['Std_Monthly_Quantity'] / feat['Avg_Monthly_Quantity'].replace(0, np.nan)
    return feat

feat = build_features(full_df)

def discount_logic(row):
    if row['Zero_Sales_Ratio'] > 0.9:
        base_discount = 0.50
    elif row['Zero_Sales_Ratio'] > 0.7:
        base_discount = 0.40
    else:
        base_discount = 0.30
    adj = base_discount
    if row['Last_Sale_Months_Ago'] > 6:
        adj += 0.05
    if pd.notnull(row['CV_Monthly_Quantity']) and row['CV_Monthly_Quantity'] > 1.0:
        adj += 0.05
    return min(adj, 0.60)

feat['Adj_Discount'] = feat.apply(discount_logic, axis=1)

def compute_rev(row):
    avg_price_est = (row['Total_Value'] / max(row['Months_Active'], 1)) / max(row['Avg_Monthly_Quantity'], 1)
    discounted_price = avg_price_est * (1 - row['Adj_Discount'])
    demand_mult = 1 + abs(ELASTICITY) * row['Adj_Discount']
    projected_units = max(row['Avg_Monthly_Quantity'] * demand_mult,
                          row['Avg_Monthly_Quantity'] + 1)
    current_rev = row['Avg_Monthly_Quantity'] * avg_price_est
    proj_rev = projected_units * discounted_price
    current_gp = current_rev * BASE_MARGIN
    proj_gp = proj_rev * BASE_MARGIN
    return pd.Series({
        'Avg_Price_Est': round(avg_price_est, 2),
        'Discounted_Price': round(discounted_price, 2),
        'Projected_Units': round(projected_units, 2),
        'Current_Revenue': round(current_rev, 2),
        'Projected_Revenue': round(proj_rev, 2),
        'Revenue_Lift': round(proj_rev - current_rev, 2),
        'Current_Gross_Profit': round(current_gp, 2),
        'Projected_Gross_Profit': round(proj_gp, 2),
        'Gross_Profit_Delta': round(proj_gp - current_gp, 2)
    })

feat = pd.concat([feat, feat.apply(compute_rev, axis=1)], axis=1)

def strategy(row):
    if row['Zero_Sales_Ratio'] > 0.9 and row['Last_Sale_Months_Ago'] >= 9:
        return "Discontinue"
    if row['Revenue_Lift'] < 0 and row['Gross_Profit_Delta'] < 0:
        return "Bundle / Placement Test"
    return "Clearance Discount"

feat['Strategy'] = feat.apply(strategy, axis=1)
feat.to_csv(OUT_FILE, index=False)

# -------------- STREAMLIT UI --------------
st.set_page_config(page_title="Clearance Sale Planner", layout="wide")
st.title("🛒 Clearance Sale Planner ")

product = st.selectbox("Select a Product", feat['Description'].tolist())
row = feat[feat['Description'] == product].iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Discount", f"{row['Adj_Discount']*100:.0f}%")
col2.metric("Strategy", row['Strategy'])
col3.metric("Projected Rev", f"{row['Projected_Revenue']}")
col4.metric("Rev Lift", f"{row['Revenue_Lift']}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Avg Qty/mo", f"{row['Avg_Monthly_Quantity']:.2f}")
col6.metric("Zero-Sales %", f"{row['Zero_Sales_Ratio']*100:.0f}%")
col7.metric("Months Since Sale", f"{row['Last_Sale_Months_Ago']}")
col8.metric("Projected Units", f"{row['Projected_Units']}")

with st.expander("Show Full Clearance Table"):
    st.dataframe(feat.sort_values('Adj_Discount', ascending=False))

if st.button("Export CSV"):
    st.success(f"Saved: {OUT_FILE}")
#python -m streamlit run "notebooks/clearance_planner.py"
