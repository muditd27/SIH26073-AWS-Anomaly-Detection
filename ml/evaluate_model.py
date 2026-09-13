import pandas as pd
import psycopg2
import joblib

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from app.services.feature_extraction import extract_features


# Connect to PostgreSQL
connection = psycopg2.connect(
    dbname="sih26073"
)


# Load anomaly-injected dataset
query = """
SELECT
    timestamp,
    station_id,
    temperature,
    humidity,
    pressure,
    is_anomaly
FROM training_data
WHERE dataset_type = 'anomaly_injected'
ORDER BY station_id, timestamp
"""

df = pd.read_sql(query, connection)

connection.close()


print("Total rows:", len(df))
print("Stations:", df["station_id"].nunique())


# Feature columns used by the model
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


# Extract temporal features separately for each station
all_features = []

for station_id, station_df in df.groupby("station_id"):

    station_df = station_df.sort_values("timestamp")

    rows = station_df[
        ["timestamp", "temperature", "humidity", "pressure"]
    ].values.tolist()

    station_features = extract_features(rows)

    station_features["is_anomaly"] = (
        station_df["is_anomaly"].values
    )

    all_features.append(station_features)


# Combine all stations
features_df = pd.concat(
    all_features,
    ignore_index=True
)


# Prepare model input
X = features_df[
    feature_columns
].fillna(0)

y_true = features_df["is_anomaly"].astype(int)


# Load trained Isolation Forest
model = joblib.load(
    "../ml/isolation_forest_model.joblib"
)


# Make predictions
predictions = model.predict(X)


# Isolation Forest:
# -1 = anomaly
#  1 = normal
y_pred = (predictions == -1).astype(int)


# Evaluation
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(
    y_true,
    y_pred,
    zero_division=0
)
recall = recall_score(
    y_true,
    y_pred,
    zero_division=0
)
f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0
)


print("\n========== MODEL EVALUATION ==========")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")


print("\n========== CONFUSION MATRIX ==========")

cm = confusion_matrix(
    y_true,
    y_pred
)

print(cm)


print("\n========== CLASSIFICATION REPORT ==========")

print(
    classification_report(
        y_true,
        y_pred,
        target_names=["Normal", "Anomaly"],
        zero_division=0
    )
)