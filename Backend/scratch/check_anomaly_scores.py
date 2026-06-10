
import sys
import os
import joblib
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

models_dir = os.path.join("models")
model_path = os.path.join(models_dir, "anomaly_detector.pkl")
scaler_path = os.path.join(models_dir, "anomaly_scaler.pkl")

if not os.path.exists(model_path):
    print("Model not found. Running training script...")
    import subprocess
    subprocess.run(["python", "scripts/train_anomaly_model.py"])

model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

# Test cases
# Features: [hour, weekday, is_weekend, is_out_of_hours, tickets_today, tickets_week]
test_cases = {
    "Normal (Mon 10am, 1 ticket)": [10, 0, 0, 0, 1, 3],
    "Weekend (Sat 2pm, 1 ticket)": [14, 5, 1, 0, 1, 3],
    "Night (Wed 2am, 1 ticket)": [2, 2, 0, 1, 1, 3],
    "High Volume (Tue 11am, 10 tickets)": [11, 1, 0, 0, 10, 20],
}

print(f"{'Case':<40} | {'Predict':<10} | {'Decision Func':<15} | {'Score Samples':<15}")
print("-" * 90)

for name, features in test_cases.items():
    X = np.array([features])
    X_scaled = scaler.transform(X)
    pred = model.predict(X_scaled)[0]
    df = model.decision_function(X_scaled)[0]
    ss = model.score_samples(X_scaled)[0]
    print(f"{name:<40} | {pred:<10} | {df:<15.4f} | {ss:<15.4f}")
