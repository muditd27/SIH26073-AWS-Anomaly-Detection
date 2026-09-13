import pandas as pd
from sklearn.ensemble import IsolationForest


def train_model(training_data):
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )

    model.fit(training_data)

    return model


def detect_anomaly(model, features):
    prediction = model.predict(features)
    score = model.decision_function(features)

    return prediction, score