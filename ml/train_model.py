import joblib
from app.services.feature_extraction import extract_features
import pandas as pd
import psycopg2

from anomaly_detector import train_model


DB_NAME = "sih26073"


connection = psycopg2.connect(
    dbname=DB_NAME
)

query = """
SELECT
    timestamp,
    station_id,
    temperature,
    humidity,
    pressure
FROM training_data
WHERE dataset_type = 'clean'
ORDER BY station_id, timestamp
"""

df = pd.read_sql(query, connection)

all_features = []

for station_id, station_df in df.groupby("station_id"):
    rows = station_df[
        ["timestamp", "temperature", "humidity", "pressure"]
    ].values.tolist()

    station_features = extract_features(rows)

    all_features.append(station_features)

features_df = pd.concat(all_features, ignore_index=True)

print("Feature rows:", len(features_df))
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

training_data = features_df[feature_columns].fillna(0)

model = train_model(training_data)
joblib.dump(model, "../ml/isolation_forest_model.joblib")

print("Isolation Forest model saved successfully")

print("Isolation Forest trained with temporal features successfully")