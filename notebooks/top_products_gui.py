import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the forecast action plan
forecast_file = r"E:\c drive\project\notebooks\outputs_top_items_forecast\top10_forecast_action_plan.csv"
df = pd.read_csv(forecast_file)

st.set_page_config(page_title="Top Products Planning", layout="wide")
st.title("📦 Top Products Forecast & Planning")

# Dropdown for product selection
product_list = df['Description'].tolist()
selected_product = st.selectbox("Select a Product:", product_list)

# Get product details
product_data = df[df['Description'] == selected_product].iloc[0]

# Show key metrics
col1, col2, col3 = st.columns(3)
col1.metric("Forecast Qty (Next Month)", round(product_data['Forecast_Quantity'], 2))
col2.metric("Suggested Stock", round(product_data['Suggested_Stock'], 2))
col3.metric("Promo Month", product_data['Promo_Preparation_Month_Name'])

st.write("---")

# Load monthly history to plot trend
monthly_file = r"E:\c drive\project\notebooks\outputs_top_items\top10_products_monthly.csv"
df_monthly = pd.read_csv(monthly_file, parse_dates=['YearMonth'])

product_history = df_monthly[df_monthly['Description'] == selected_product]

st.subheader("📈 Monthly Sales Trend")
fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=product_history, x='YearMonth', y='Month_Quantity', marker='o', ax=ax)
plt.title(f"Monthly Quantity - {selected_product}")
plt.xlabel("Month")
plt.ylabel("Quantity Sold")
st.pyplot(fig)

