import pandas as pd
import psycopg2
import joblib

from app.services.feature_extraction import extract_features
from shap_explanation import explain_prediction


# Connect to PostgreSQL
connection = psycopg2.connect(
    dbname="sih26073"
)


# Get 97 chronological readings from one station
query = """
SELECT
    timestamp,
    station_id,
    temperature,
    humidity,
    pressure
FROM training_data
WHERE dataset_type = 'anomaly_injected'
  AND station_id = 'AWS_01'
ORDER BY timestamp ASC
LIMIT 97
"""

df = pd.read_sql(query, connection)

connection.close()


print("Testing rows:", len(df))
print("Station:", df["station_id"].iloc[0])


# Create temporal features
rows = df[
    ["timestamp", "temperature", "humidity", "pressure"]
].values.tolist()

features_df = extract_features(rows)


# Features used by the Isolation Forest
feature_columns = [
    "temperature",
    "humidity",
    "pressure",
    "temperature_lag1",
    "humidity_lag1",
    "pressure_lag1",
    "temperature_change",
    "humidity_change",
    "pressure_change",
    "temperature_rolling_mean",
    "humidity_rolling_mean",
    "pressure_rolling_mean",
    "temperature_rolling_std",
    "humidity_rolling_std",
    "pressure_rolling_std"
]


# Replace missing values from the first row
features = features_df[
    feature_columns
].fillna(0)


# Load the trained Isolation Forest
model = joblib.load(
    "../ml/isolation_forest_model.joblib"
)


# Test the latest reading
latest = features.iloc[-1:]


# Detect anomaly
prediction = model.predict(latest)
score = model.decision_function(latest)


print("Model prediction:", prediction[0])
print("Anomaly score:", score[0])


# SHAP explanation
explanations = explain_prediction(
    model,
    latest,
    feature_columns
)


print("\nTop SHAP contributors:")

for item in explanations[:5]:
    print(
        item["feature"],
        "→",
        item["shap_value"]
    )