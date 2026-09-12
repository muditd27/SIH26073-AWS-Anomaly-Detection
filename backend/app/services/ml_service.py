import joblib

from app.services.feature_extraction import extract_features


MODEL_PATH = "../ml/isolation_forest_model.joblib"

FEATURE_COLUMNS = [
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


model = joblib.load(MODEL_PATH)


def predict_anomaly(rows):
    """
    Generate an anomaly prediction from recent telemetry readings.
    """

    features_df = extract_features(rows)

    if features_df.empty:
        return None

    features = features_df[
        FEATURE_COLUMNS
    ].fillna(0)

    latest = features.iloc[-1:]

    prediction = model.predict(latest)[0]
    score = model.decision_function(latest)[0]

    is_anomaly = prediction == -1

    return {
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": float(score)
    }