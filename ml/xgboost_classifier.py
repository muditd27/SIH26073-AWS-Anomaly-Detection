# xgboost_classifier.py
"""
XGBoost Anomaly Multi-Class Classifier with SHAP Explainability & Reason Generator.
Takes:
  - 42 features combining raw sensor inputs, lags, rolling stats, spatial health-weighted consensus,
    Isolation Forest anomaly scores, and XGBoost regression prediction errors.
Outputs:
  - Anomaly classification: NORMAL, SENSOR_SPIKE, SENSOR_DRIFT, FROZEN_SENSOR,
    OUT_OF_BOUNDS_RAIL, GENUINE_WEATHER_FRONT.
  - Prediction confidence probability.
  - SHAP feature attributions for the predicted class.
  - Human-readable reason & explanation for frontend consumption.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd
import joblib
import shap

logger = logging.getLogger("ml_pipeline.classifier")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

SEARCH_MODEL_DIRS = [
    Path("models"),
    Path(__file__).resolve().parent / "models",
    Path(r"C:\Users\koush\OneDrive\Desktop\manual\models"),
    Path(r"C:\Users\koush\OneDrive\Desktop\manual"),
    Path(r"C:\Users\koush\OneDrive\Desktop\manual\SIH26073-AWS-Anomaly-Detection\backend\app\ml_pipeline\models"),
    Path(r"C:\Users\koush\.gemini\antigravity\scratch\isolation_forest\ml_pipeline\models"),
]

# Friendly labels for the 42 technical features
FEATURE_LABEL_MAP = {
    "temperature": "Current Temperature",
    "pressure": "Current Pressure",
    "relative_humidity": "Current Relative Humidity",
    "temperature_lag1": "Temperature 15-min Lag",
    "temperature_lag2": "Temperature 30-min Lag",
    "temperature_lag3": "Temperature 45-min Lag",
    "temperature_lag24": "Temperature 6-hour Lag",
    "temperature_change": "Temperature Sudden Delta",
    "pressure_lag1": "Pressure 15-min Lag",
    "pressure_lag2": "Pressure 30-min Lag",
    "pressure_lag3": "Pressure 45-min Lag",
    "pressure_lag24": "Pressure 6-hour Lag",
    "pressure_change": "Pressure Sudden Delta",
    "relative_humidity_lag1": "Humidity 15-min Lag",
    "relative_humidity_lag2": "Humidity 30-min Lag",
    "relative_humidity_lag3": "Humidity 45-min Lag",
    "relative_humidity_lag24": "Humidity 6-hour Lag",
    "relative_humidity_change": "Humidity Sudden Delta",
    "temperature_rolling_mean": "Temperature 3-Step Rolling Mean",
    "temperature_rolling_std": "Temperature 3-Step Rolling Variance",
    "pressure_rolling_mean": "Pressure 3-Step Rolling Mean",
    "pressure_rolling_std": "Pressure 3-Step Rolling Variance",
    "relative_humidity_rolling_mean": "Humidity 3-Step Rolling Mean",
    "relative_humidity_rolling_std": "Humidity 3-Step Rolling Variance",
    "hour_sin": "Time of Day Cycle",
    "hour_cos": "Time of Day Cycle",
    "day_of_year_sin": "Seasonal Day of Year",
    "day_of_year_cos": "Seasonal Day of Year",
    "weighted_neighbor_temperature": "Neighbor Consensus Temperature",
    "weighted_neighbor_pressure": "Neighbor Consensus Pressure",
    "weighted_neighbor_relative_humidity": "Neighbor Consensus Humidity",
    "temperature_neighbor_difference": "Temperature Divergence from Neighbors",
    "pressure_neighbor_difference": "Pressure Divergence from Neighbors",
    "relative_humidity_neighbor_difference": "Humidity Divergence from Neighbors",
    "if_score": "Isolation Forest Outlier Score",
    "temperature_prediction_error": "Temperature Prediction Residual Error",
    "pressure_prediction_error": "Pressure Prediction Residual Error",
    "humidity_prediction_error": "Humidity Prediction Residual Error",
    "temperature_abs_error": "Absolute Temperature Prediction Error",
    "pressure_abs_error": "Absolute Pressure Prediction Error",
    "humidity_abs_error": "Absolute Humidity Prediction Error",
    "sensor_health": "Historical Sensor Health Score",
}


def update_sensor_health(old_health: float, anomaly_type: str, confidence: float = 1.0) -> float:
    """
    Updates sensor health score (0-100) based on classified anomaly type.
    Normal readings slowly recover health; fault detections penalize health.
    """
    conf = np.clip(float(confidence), 0.0, 1.0)
    health = np.clip(float(old_health), 0.0, 100.0)
    atype = str(anomaly_type).strip().upper()

    if atype == "NORMAL":
        health = health + 0.05 * conf * (100.0 - health)
    elif atype in ["GENUINE_WEATHER_FRONT", "GENUINE_WEATHER_EVENT"]:
        health = health + 0.02 * conf * (100.0 - health)
    elif atype in ["SENSOR_SPIKE", "SPIKE"]:
        health = health - 15.0 * conf
    elif atype in ["FROZEN_SENSOR", "FREEZE"]:
        health = health - 20.0 * conf
    elif atype in ["SENSOR_DRIFT", "DRIFT"]:
        health = health - 5.0 * conf
    elif atype in ["OUT_OF_BOUNDS_RAIL", "DATA_CORRUPTION"]:
        health = health - 15.0 * conf
    elif atype in ["COMMUNICATION_ERROR"]:
        health = health - 12.0 * conf

    return round(float(np.clip(health, 0.0, 100.0)), 2)


class XGBoostAnomalyClassifier:
    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = self._resolve_models_dir(models_dir)
        logger.info(f"Loading XGBoost Classifier artifacts from: {self.models_dir}")

        self.classifier = joblib.load(self._find_file("xgb_anomaly_classifier.pkl"))
        self.label_encoder = joblib.load(self._find_file("anomaly_label_encoder.pkl"))
        self.feature_names = joblib.load(self._find_file("xgb_classifier_features.pkl"))
        self.classes = list(self.label_encoder.classes_)

        logger.info(f"Loaded XGBoost Classifier with {len(self.classes)} classes: {self.classes}")
        logger.info(f"Feature count: {len(self.feature_names)} features.")

        # Initialize SHAP TreeExplainer on the XGBoost classifier
        logger.info("Initializing SHAP TreeExplainer for XGBoost Classifier...")
        self.explainer = shap.TreeExplainer(self.classifier)
        logger.info("SHAP TreeExplainer for XGBoost Classifier initialized successfully.")

        # Dynamic station health tracking state
        self.station_health: Dict[str, float] = {}

    def _resolve_models_dir(self, custom_dir: Optional[str]) -> Path:
        if custom_dir and os.path.exists(custom_dir):
            return Path(custom_dir)
        for candidate in SEARCH_MODEL_DIRS:
            if candidate.exists() and (candidate / "xgb_anomaly_classifier.pkl").exists():
                return candidate
        raise FileNotFoundError(f"Could not find classifier in paths: {[str(d) for d in SEARCH_MODEL_DIRS]}")

    def _find_file(self, filename: str) -> Path:
        direct = self.models_dir / filename
        if direct.exists():
            return direct
        for d in SEARCH_MODEL_DIRS:
            candidate = d / filename
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"Missing file '{filename}'. Searched: {[str(d) for d in SEARCH_MODEL_DIRS]}")

    def get_station_health(self, station_id: str) -> float:
        return self.station_health.get(station_id, 100.0)

    def set_station_health(self, station_id: str, health: float):
        self.station_health[station_id] = round(float(np.clip(health, 0.0, 100.0)), 2)

    def build_features(
        self,
        df_new: pd.DataFrame,
        df_history: Optional[pd.DataFrame] = None,
        if_scores: Optional[Dict[Any, float]] = None,
        reg_preds: Optional[Dict[Any, Dict[str, float]]] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Builds the complete 42 features required by the XGBoost classifier:
        - raw physical features
        - lags (1, 2, 3, 24)
        - deltas (change from previous)
        - rolling mean and std
        - cyclical seasonal features
        - health-weighted spatial neighbor consensus
        - Isolation Forest anomaly score
        - regression prediction errors (signed and absolute)
        - dynamic sensor health
        """
        if df_history is not None and not df_history.empty:
            df_combined = pd.concat([df_history, df_new], ignore_index=True)
        else:
            df_combined = df_new.copy()

        df = df_combined.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        if "humidity" in df.columns and "relative_humidity" not in df.columns:
            df["relative_humidity"] = df["humidity"]
        elif "relative_humidity" in df.columns and "humidity" not in df.columns:
            df["humidity"] = df["relative_humidity"]

        df = df.sort_values(["station_id", "timestamp"]).reset_index(drop=True)

        # 1. Temporal Lags & Deltas
        for col in ["temperature", "pressure", "relative_humidity"]:
            df[f"{col}_lag1"] = df.groupby("station_id")[col].shift(1)
            df[f"{col}_lag2"] = df.groupby("station_id")[col].shift(2)
            df[f"{col}_lag3"] = df.groupby("station_id")[col].shift(3)
            df[f"{col}_lag24"] = df.groupby("station_id")[col].shift(24)

            # Cold start fallback
            df[f"{col}_lag1"] = df[f"{col}_lag1"].bfill().ffill().fillna(df[col])
            df[f"{col}_lag2"] = df[f"{col}_lag2"].bfill().ffill().fillna(df[f"{col}_lag1"])
            df[f"{col}_lag3"] = df[f"{col}_lag3"].bfill().ffill().fillna(df[f"{col}_lag2"])
            df[f"{col}_lag24"] = df[f"{col}_lag24"].bfill().ffill().fillna(df[f"{col}_lag3"])

            # Change from lag1
            df[f"{col}_change"] = df[col] - df[f"{col}_lag1"]

            # 2. Rolling mean and std on previous readings (lag1)
            rolling_obj = df.groupby("station_id")[f"{col}_lag1"].rolling(window=3, min_periods=1)
            df[f"{col}_rolling_mean"] = rolling_obj.mean().reset_index(level=0, drop=True)
            df[f"{col}_rolling_std"] = rolling_obj.std().reset_index(level=0, drop=True).fillna(0.0)

        # 3. Cyclical Time Features
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_year"] = df["timestamp"].dt.dayofyear
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
        df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.0)
        df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.0)

        # 4. Sensor Health
        df["sensor_health"] = df["station_id"].apply(self.get_station_health)
        df["h_norm"] = (df["sensor_health"] / 100.0).clip(lower=0.01)

        # 5. Health-Weighted Spatial Neighbor Consensus
        for col in ["temperature", "pressure", "relative_humidity"]:
            df[f"w_{col}"] = df[col] * df["h_norm"]
            total_w = df.groupby("timestamp")[f"w_{col}"].transform("sum")
            total_h = df.groupby("timestamp")["h_norm"].transform("sum")

            other_w = total_w - df[f"w_{col}"]
            other_h = total_h - df["h_norm"]

            fallback = (df.groupby("timestamp")[col].transform("sum") - df[col]) / 3.0
            denom = np.where(other_h > 0.01, other_h, 1.0)
            df[f"weighted_neighbor_{col}"] = np.where(other_h > 0.01, other_w / denom, fallback)
            df[f"{col}_neighbor_difference"] = df[col] - df[f"weighted_neighbor_{col}"]

        # 6. Isolation Forest Score Injection
        if if_scores:
            df["if_score"] = df["telemetry_id"].map(if_scores).fillna(0.0)
        else:
            df["if_score"] = df.get("if_score", 0.0)

        # 7. Regression Errors Injection
        if reg_preds:
            df["predicted_temperature"] = df["telemetry_id"].map(lambda tid: reg_preds.get(tid, {}).get("expected_temperature", np.nan))
            df["predicted_pressure"] = df["telemetry_id"].map(lambda tid: reg_preds.get(tid, {}).get("expected_pressure", np.nan))
            df["predicted_humidity"] = df["telemetry_id"].map(lambda tid: reg_preds.get(tid, {}).get("expected_humidity", np.nan))

            df["temperature_prediction_error"] = df["temperature"] - df["predicted_temperature"]
            df["pressure_prediction_error"] = df["pressure"] - df["predicted_pressure"]
            df["humidity_prediction_error"] = df["relative_humidity"] - df["predicted_humidity"]
        else:
            df["temperature_prediction_error"] = df.get("temperature_error", 0.0)
            df["pressure_prediction_error"] = df.get("pressure_error", 0.0)
            df["humidity_prediction_error"] = df.get("humidity_error", 0.0)

        df["temperature_prediction_error"] = df["temperature_prediction_error"].fillna(0.0)
        df["pressure_prediction_error"] = df["pressure_prediction_error"].fillna(0.0)
        df["humidity_prediction_error"] = df["humidity_prediction_error"].fillna(0.0)

        df["temperature_abs_error"] = df["temperature_prediction_error"].abs()
        df["pressure_abs_error"] = df["pressure_prediction_error"].abs()
        df["humidity_abs_error"] = df["humidity_prediction_error"].abs()

        # Slice only the target new records
        target_tids = set(df_new["telemetry_id"].tolist()) if "telemetry_id" in df_new.columns else None
        if target_tids:
            df_target = df[df["telemetry_id"].isin(target_tids)].copy()
        else:
            df_target = df.tail(len(df_new)).copy()

        # Extract strictly the 42 features
        X_mat = df_target[self.feature_names].fillna(0.0)

        return df_target, X_mat

    def shap_to_reason(
        self,
        class_name: str,
        confidence: float,
        row_features: Dict[str, Any],
        shap_attributions: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        SHAP Explanation-to-Reason Converter for Frontend.
        Translates raw SHAP attributions into domain-specific, actionable explanations.
        """
        # Sort features by positive attribution (features pushing towards the predicted class)
        positive_drivers = [
            (feat, float(val))
            for feat, val in shap_attributions.items()
            if val > 0.0
        ]
        positive_drivers.sort(key=lambda x: x[1], reverse=True)

        total_pos_impact = sum(v for _, v in positive_drivers) if positive_drivers else 1.0

        # Build top driver items
        top_drivers = []
        for feat, val in positive_drivers[:3]:
            friendly_name = FEATURE_LABEL_MAP.get(feat, feat.replace("_", " ").title())
            actual_val = row_features.get(feat, "N/A")
            if isinstance(actual_val, float):
                val_str = f"{actual_val:+.2f}"
            else:
                val_str = str(actual_val)

            top_drivers.append({
                "feature": feat,
                "label": friendly_name,
                "current_value": val_str,
                "shap_impact": round(val, 4),
                "contribution_percent": round((val / total_pos_impact) * 100.0, 1),
            })

        # Generate primary reason and actionable recommendation based on class
        temp_err = float(row_features.get("temperature_prediction_error", 0.0))
        pres_err = float(row_features.get("pressure_prediction_error", 0.0))
        rh_err = float(row_features.get("humidity_prediction_error", 0.0))
        top_feat = top_drivers[0]["label"] if top_drivers else "Sensor Consensus"

        if class_name == "NORMAL":
            severity = "NORMAL"
            affected_sensors = "None"
            primary_reason = "Sensor operating normally: measurements align with physical expectations and regional consensus."
            recommended_action = "No action required. Sensor health is optimal."

        elif class_name == "SENSOR_SPIKE":
            severity = "HIGH"
            # Identify which sensor spiked
            if abs(temp_err) >= max(abs(pres_err), abs(rh_err)):
                affected_sensors = "temperature"
                primary_reason = f"Sudden abnormal spike detected: temperature deviated by {temp_err:+.2f}°C from expected trajectory (driven by {top_feat})."
            elif abs(pres_err) >= max(abs(temp_err), abs(rh_err)):
                affected_sensors = "pressure"
                primary_reason = f"Sudden barometric spike: pressure jumped by {pres_err:+.2f} hPa unexpectedly (driven by {top_feat})."
            else:
                affected_sensors = "relative_humidity"
                primary_reason = f"Sudden humidity jump of {rh_err:+.2f}% detected (driven by {top_feat})."
            recommended_action = f"Check electrical connections and transient interference on {affected_sensors} sensor probe."

        elif class_name == "FROZEN_SENSOR":
            severity = "CRITICAL"
            rh_std = float(row_features.get("relative_humidity_rolling_std", 0.0))
            if rh_std < 0.05:
                affected_sensors = "relative_humidity"
                primary_reason = f"Sensor frozen flatline: humidity variance collapsed to {rh_std:.2f}% while neighbor stations show natural weather dynamics."
            else:
                affected_sensors = "multivariate_sensor"
                primary_reason = f"Frozen sensor state identified: consecutive values remain stationary despite changing regional conditions."
            recommended_action = f"Inspect {affected_sensors} transducer for mechanical sticking or moisture/ice accumulation."

        elif class_name == "SENSOR_DRIFT":
            severity = "MEDIUM"
            if abs(temp_err) >= max(abs(pres_err), abs(rh_err)):
                affected_sensors = "temperature"
                primary_reason = f"Gradual calibration drift: temperature shows consistent bias of {temp_err:+.2f}°C relative to neighbor stations."
            elif abs(pres_err) >= max(abs(temp_err), abs(rh_err)):
                affected_sensors = "pressure"
                primary_reason = f"Pressure calibration drift: steady offset of {pres_err:+.2f} hPa from regional consensus."
            else:
                affected_sensors = "relative_humidity"
                primary_reason = f"Humidity sensor degradation: persistent divergence of {rh_err:+.2f}%."
            recommended_action = f"Schedule routine recalibration and zero-point alignment for {affected_sensors} sensor."

        elif class_name == "OUT_OF_BOUNDS_RAIL":
            severity = "CRITICAL"
            affected_sensors = "electrical_rail"
            primary_reason = f"Sensor reading pinned against electrical limits/rails (driven by {top_feat})."
            recommended_action = "Replace sensor unit; likely ADC saturation or open circuit fault."

        elif class_name == "GENUINE_WEATHER_FRONT":
            severity = "LOW"
            affected_sensors = "weather_network"
            primary_reason = "Correlated regional atmospheric change: sharp weather variation confirmed across neighbor stations (not a sensor fault)."
            recommended_action = "Atmospheric event verified across stations. Suppress fault alarms; record as meteorological event."

        else:
            severity = "MEDIUM"
            affected_sensors = "unknown"
            primary_reason = f"Anomaly pattern matched: {class_name} with confidence {confidence * 100:.1f}%."
            recommended_action = "Review diagnostics and check sensor telemetry history."

        return {
            "primary_reason": primary_reason,
            "severity": severity,
            "affected_sensors": affected_sensors,
            "recommended_action": recommended_action,
            "top_drivers": top_drivers,
        }

    def predict_and_explain(
        self,
        df_target: pd.DataFrame,
        X_mat: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Runs XGBoost classification, computes SHAP attributions, converts SHAP to human reasons,
        and dynamically updates sensor health.
        """
        if X_mat.empty:
            return []

        # Predict class indices and probability distributions
        pred_indices = self.classifier.predict(X_mat)
        proba_matrix = self.classifier.predict_proba(X_mat)

        # Compute SHAP values for the 6-class XGBoost model
        # Shape: (N, 42, 6)
        shap_matrix = self.explainer.shap_values(X_mat)

        results = []
        for i in range(len(df_target)):
            row = df_target.iloc[i]
            class_idx = int(pred_indices[i])
            class_name = self.classes[class_idx]
            confidence = float(proba_matrix[i, class_idx])

            # Extract SHAP values specifically for the predicted class
            class_shap_vector = shap_matrix[i, :, class_idx]
            shap_dict = {
                feat: round(float(class_shap_vector[f_idx]), 5)
                for f_idx, feat in enumerate(self.feature_names)
            }

            # Convert row features to dict
            row_feat_dict = X_mat.iloc[i].to_dict()

            # Generate human-readable reason for frontend
            reason_info = self.shap_to_reason(class_name, confidence, row_feat_dict, shap_dict)

            # Update dynamic sensor health
            st = str(row.get("station_id", "UNKNOWN"))
            old_h = self.get_station_health(st)
            new_h = update_sensor_health(old_h, class_name, confidence)
            self.set_station_health(st, new_h)

            tid = row.get("telemetry_id")
            is_anomaly = (class_name != "NORMAL")

            res_item = {
                "telemetry_id": int(tid) if tid is not None else None,
                "station_id": st,
                "timestamp": str(row.get("timestamp")),
                "anomaly_type": class_name,
                "is_anomaly": is_anomaly,
                "confidence": round(confidence, 4),
                "severity": reason_info["severity"],
                "affected_sensors": reason_info["affected_sensors"],
                "primary_reason": reason_info["primary_reason"],
                "explanation": reason_info["primary_reason"],
                "recommended_action": reason_info["recommended_action"],
                "top_drivers": reason_info["top_drivers"],
                "classifier_shap": json.dumps(shap_dict),
                "sensor_health": new_h,
            }
            results.append(res_item)

        return results
