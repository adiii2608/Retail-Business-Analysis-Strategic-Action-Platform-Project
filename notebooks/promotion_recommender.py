# promotion_recommender.py
import pandas as pd
import numpy as np
import streamlit as st
import joblib

PROMO_DATA = "promotion_dataset.csv"
MODEL_FILE = "models/promotion_model.pkl"

st.set_page_config(page_title="Promotion Recommender", layout="wide")
st.title("🎯 Customer Promotion Recommender")

@st.cache_data
def load_data():
    return pd.read_csv(PROMO_DATA)

@st.cache_resource
def load_model():
    bundle = joblib.load(MODEL_FILE)
    return bundle['model'], bundle['encoder'], bundle['features']

data = load_data()
model, encoder, features = load_model()

customer_ids = sorted(data['Customer_ID'].unique())
selected_id = st.selectbox("Select Customer ID", customer_ids)

cust = data[data['Customer_ID'] == selected_id].iloc[0]

st.subheader("Customer Snapshot")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("CLTV", f"{cust['CLTV']:.2f}")
c2.metric("Segment", cust['Value_Tier'])
c3.metric("Recency (days)", int(cust['Recency']))
c4.metric("Churn Prob", f"{cust['Churn_Prob']:.2f}")
c5.metric("At Risk?", "Yes" if cust['At_Risk'] else "No")

st.write(f"**Last Product Purchased:** {cust.get('Last_Product', 'N/A')}")

# Prepare row for model
X_row = cust[features].to_frame().T.copy()
# Encode Value_Tier
X_row[['Value_Tier']] = encoder.transform(X_row[['Value_Tier']])

pred_class = model.predict(X_row)[0]

st.subheader("🔮 Promotion Recommendation")
colA, colB = st.columns(2)
colA.markdown(f"**Model Prediction:** `{pred_class}`")
colB.markdown(f"**Rule-Based Class:** `{cust['Promotion_Class']}`")

if pred_class != cust['Promotion_Class']:
    st.warning("⚠️ Model and rule-based classification differ. Review suggested logic.")

st.write("**Suggested Offer Text:**", cust['Suggested_Offer_Text'])

# Simple explanation block
explanations = {
    'VIP_LOYALTY': "High lifetime value → reward exclusivity to prevent defection.",
    'UPSWING_UPSELL': "Healthy high-value customer → offer premium bundle to grow value.",
    'HIGH_VALUE_SAVE': "High value but at risk → targeted save incentive.",
    'CROSS_SELL': "Mid-value stable → encourage broader basket.",
    'MID_SAVE': "Mid-value drifting → small incentive + loyalty enrollment.",
    'WINBACK': "Low value & at risk → reactivation discount.",
    'LIGHT_NURTURE': "Low value & stable → low-cost automated engagement only."
}
st.info(explanations.get(pred_class, "Promotion logic applied."))

# Manual override
override = st.selectbox("Manual Override (optional)", ["--"] + list(sorted(data['Promotion_Class'].unique())))
if override != "--":
    st.success(f"Override selected: {override}")

# Export single row record
if st.button("Download This Recommendation"):
    out = cust.to_frame().T
    if override != "--":
        out['Manual_Override'] = override
    st.download_button("Save CSV", out.to_csv(index=False), file_name=f"promo_customer_{selected_id}.csv")

# Bulk export
if st.button("Export All Recommendations"):
    st.download_button("Download promotion_dataset.csv", data.to_csv(index=False), file_name="promotion_dataset.csv")
