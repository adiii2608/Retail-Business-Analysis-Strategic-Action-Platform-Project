import pickle
import pandas as pd

# Example: Load the model
with open(r"E:\c drive\project\models\churn_model.pkl", "rb") as file:
    churn_model = pickle.load(file)

# Load some test data
data = pd.DataFrame({
    'Recency': [10],
    'Frequency': [5],
    'Monetary': [200],
    # Add other features required by your model
})

# Make predictions
prediction = churn_model.predict(data)
print("Churn Prediction:", prediction)
