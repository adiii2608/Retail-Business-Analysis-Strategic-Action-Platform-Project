# train_promotion_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report
import joblib

DATA_FILE = "promotion_dataset.csv"
MODEL_FILE = "models/promotion_model.pkl"

df = pd.read_csv(DATA_FILE)

feature_cols = ['CLTV','Frequency','Recency','Churn_Prob','Value_Tier','At_Risk']
# Ensure features exist
for col in feature_cols:
    if col not in df.columns:
        raise ValueError(f"Missing feature: {col}")

X = df[feature_cols].copy()
y = df['Promotion_Class']

# Encode Value_Tier
enc = OrdinalEncoder()
X[['Value_Tier']] = enc.fit_transform(X[['Value_Tier']])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, test_size=0.2, random_state=42
)

clf = DecisionTreeClassifier(max_depth=5, min_samples_leaf=20, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model + encoder
joblib.dump({'model': clf, 'encoder': enc, 'features': feature_cols}, MODEL_FILE)
print("Saved model to:", MODEL_FILE)
