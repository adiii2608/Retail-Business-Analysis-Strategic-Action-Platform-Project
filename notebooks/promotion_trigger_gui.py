# promotion_trigger_gui.py
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

DATA_FILE = r"E:\c drive\project\notebooks\promotion_hourly_triggers.csv"

st.set_page_config(page_title="Promotion Hourly Triggers", layout="wide")
st.title("⏰ Customer Promotion Trigger Planner")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)

    # Map A/B/C/D to Top/High/Medium/Low
    segment_map = {
        'A': 'Top',
        'B': 'High',
        'C': 'Medium',
        'D': 'Low'
    }
    if 'CLTV_Segment_Label' in df.columns:
        df['CLTV_Segment_Label'] = df['CLTV_Segment_Label'].replace(segment_map)
    elif 'CLTV_Segment' in df.columns:
        df['CLTV_Segment_Label'] = df['CLTV_Segment'].map(segment_map)
    else:
        st.warning("CLTV_Segment or CLTV_Segment_Label column not found in the dataset!")
    
    return df

df = load_data()

segments = df['CLTV_Segment_Label'].dropna().unique()
selected_segment = st.selectbox("Select CLTV Segment", segments)

segment_data = df[df['CLTV_Segment_Label'] == selected_segment]

# Show best hours
best_hours = segment_data[segment_data['Trigger_Class'] == "HOT_HOUR"]['Hour'].tolist()
st.success(f"**Best Promotion Hours for {selected_segment}:** {best_hours}")

# Plot hourly activity
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(segment_data['Hour'], segment_data['Total_Orders'], color='skyblue')
for idx, row in segment_data.iterrows():
    if row['Trigger_Class'] == "HOT_HOUR":
        ax.text(row['Hour'], row['Total_Orders'] + 0.5, '🔥', ha='center')
ax.set_xlabel("Hour of Day")
ax.set_ylabel("Total Orders")
ax.set_title(f"Hourly Orders - {selected_segment}")
st.pyplot(fig)

# Download option
st.download_button(
    "Download Full Trigger Plan CSV",
    df.to_csv(index=False),
    file_name="promotion_hourly_triggers.csv"
)
