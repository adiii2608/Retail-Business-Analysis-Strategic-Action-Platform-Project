import pandas as pd
import streamlit as st

# Load data
DATA_PATH = r"E:\c drive\project\festival_top_products.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

# Streamlit Config
st.set_page_config(page_title="🎁 Festival Product Promotion Planner", layout="wide")
st.title("🎉 Festival-Based Product Promotion Planner")

# Festival Selection
festival_options = df['Festival'].unique().tolist()
selected_festival = st.selectbox("Select a Festival", festival_options)

# Promotion Period Info
promotion_month = ""
if selected_festival.lower() == "christmas":
    promotion_month = "🎄 1st December to 1st January"
elif selected_festival.lower() == "diwali":
    promotion_month = "🪔 1st October to 31st October"
else:
    promotion_month = "🗓️ 1st of previous month to the festival day"

st.markdown(f"📅 **Recommended Promotion Period for {selected_festival}:** `{promotion_month}`")

# Filter data for selected festival
filtered = df[df['Festival'] == selected_festival].copy()

st.subheader("🛍️ Set Promotion Discount (%) for Each Product")

# Let user set discount for each product
discount_inputs = {}
for idx, row in filtered.iterrows():
    product = row['Description']
    quantity = row['Quantity']
    default_discount = 10  # Default discount %
    discount = st.number_input(f"Discount for {product} (Sold: {quantity})", min_value=0, max_value=100, value=default_discount, step=1)
    discount_inputs[product] = discount

# Add new Discount column based on user input
filtered['Promotion_Discount (%)'] = filtered['Description'].map(discount_inputs)

# Show final promotion table
st.subheader("📋 Promotion Plan Table")
st.dataframe(filtered[['Description', 'Quantity', 'Promotion_Discount (%)']], use_container_width=True)

# Download button
st.download_button(
    "📥 Download Festival Promotion Plan CSV",
    filtered.to_csv(index=False),
    file_name=f"{selected_festival.lower()}_promotion_plan.csv",
    mime="text/csv"
)
