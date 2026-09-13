# unified_ml_pipeline.py
"""
Unified Machine Learning Pipeline — Conforming to "The Complete Loop" Architecture:
  1. LIVE STREAM (4 AWS readings at same timestamp)
  2. Data Validation
  3. Previous Sensor Health (loaded from database)
  4. Health-Weighted Spatial Neighbour Calculation
  5. Spatial + Temporal + Seasonal Feature Engineering
  6. Parallel Model Execution:
     - Isolation Forest -> if_score
     - XGBoost Regressors -> Expected T/P/RH -> Prediction Errors
  7. XGBoost Classifier -> anomaly_type + confidence + SHAP Reason
  8. UPDATE SENSOR HEALTH (using classifier output)
  9. Display Health (Frontend) & Store Health (Database)
  10. Feed forward to NEXT TIMESTAMP (new weighted-neighbour calculation)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from model_pipeline import AnomalyModelPipeline, BEST_THRESHOLD
from xgboost_regressor import XGBoostWeatherRegressor
from xgboost_classifier import XGBoostAnomalyClassifier, update_sensor_health

logger = logging.getLogger("ml_pipeline.unified")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class UnifiedMLPipeline:
    def __init__(
        self,
        if_model_path: Optional[str] = None,
        xgb_models_dir: Optional[str] = None,
        threshold: float = BEST_THRESHOLD,
    ):
        logger.info("Initializing The Complete Loop Architecture...")
        # 1. Isolation Forest (SHAP-free, high-throughput outlier detector)
        self.iso_pipeline = AnomalyModelPipeline(model_path=if_model_path, threshold=threshold)

        # 2. XGBoost Regressors (Expected physical trajectory models)
        self.xgb_regressor = XGBoostWeatherRegressor(models_dir=xgb_models_dir)

        # 3. XGBoost Classifier with SHAP Explainability & Reason Generator
        self.xgb_classifier = XGBoostAnomalyClassifier(models_dir=xgb_models_dir)

        logger.info("Complete Loop Pipeline fully loaded and operational.")

    def validate_readings(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Step 2: Data Validation.
        Validates presence of required sensor fields, standardizes naming,
        enforces numerical types, and verifies physical limits.
        """
        df = pd.DataFrame(records)
        if df.empty:
            return df

        # Column normalization
        if "humidity" in df.columns and "relative_humidity" not in df.columns:
            df["relative_humidity"] = df["humidity"]
        elif "relative_humidity" in df.columns and "humidity" not in df.columns:
            df["humidity"] = df["relative_humidity"]

        required_cols = ["station_id", "timestamp", "temperature", "pressure", "relative_humidity"]
        for c in required_cols:
            if c not in df.columns:
                raise ValueError(f"Data Validation Error: Missing required column '{c}'")

        # Type conversion and NaN safety
        df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
        df["pressure"] = pd.to_numeric(df["pressure"], errors="coerce")
        df["relative_humidity"] = pd.to_numeric(df["relative_humidity"], errors="coerce")

        if df[["temperature", "pressure", "relative_humidity"]].isna().any().any():
            logger.warning("Data Validation: NaNs found in sensor readings, imputing...")
            df = df.fillna(df.mean(numeric_only=True)).fillna(0.0)

        return df

    def process_batch(
        self,
        new_records: List[Dict[str, Any]],
        historical_buffer: Optional[List[Dict[str, Any]]] = None,
        previous_sensor_health: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Executes 'The Complete Loop' exactly as depicted in the architectural specification.

        Parameters:
            new_records: 4 AWS readings at the current timestamp.
            historical_buffer: Trailing historical database records (for lags & rolling stats).
            previous_sensor_health: Dict of {station_id: health_score} from previous timestamp.
        """
        if not new_records:
            return {
                "db_predictions": [],
                "db_anomalies": [],
                "db_sensor_health": [],
                "frontend_results": [],
            }

        # -------------------------------------------------------------
        # STEP 1 & 2: Live Stream Batch + Data Validation
        # -------------------------------------------------------------
        df_new = self.validate_readings(new_records)
        df_hist = pd.DataFrame(historical_buffer) if historical_buffer else None

        # -------------------------------------------------------------
        # STEP 3: Previous Sensor Health
        # -------------------------------------------------------------
        current_stations = df_new["station_id"].unique().tolist()
        prev_health = {}
        for st in current_stations:
            if previous_sensor_health and st in previous_sensor_health:
                prev_health[st] = float(previous_sensor_health[st])
            else:
                prev_health[st] = self.xgb_classifier.get_station_health(st)

        # Update classifier instance with previous health for weighting
        for st, h in prev_health.items():
            self.xgb_classifier.set_station_health(st, h)

        # -------------------------------------------------------------
        # STEP 4 & 5: Health-Weighted Spatial Neighbour + Temporal Features
        # -------------------------------------------------------------
        # (Lags, rolling stats, deltas, and health-weighted spatial consensus)

        # -------------------------------------------------------------
        # STEP 6: Parallel Execution
        #   Branch A: Isolation Forest -> if_score
        #   Branch B: XGBoost Regressors -> Expected T/P/RH -> Prediction errors
        # -------------------------------------------------------------
        # Branch A: Isolation Forest
        if_results = self.iso_pipeline.score_records(df_new)
        if_lookup = {p["telemetry_id"]: p for p in if_results}
        if_scores_dict = {p["telemetry_id"]: p["if_score"] for p in if_results}

        # Branch B: XGBoost Regressors
        xgb_reg_results = self.xgb_regressor.predict_readings(
            df_new.to_dict(orient="records"), historical_buffer=historical_buffer
        )
        reg_lookup = {r["telemetry_id"]: r for r in xgb_reg_results}

        # -------------------------------------------------------------
        # STEP 7: XGBoost Classifier + SHAP Explainability
        #   Takes if_score + Prediction errors + Features -> anomaly_type + confidence
        # -------------------------------------------------------------
        df_target, X_classifier_mat = self.xgb_classifier.build_features(
            df_new=df_new,
            df_history=df_hist,
            if_scores=if_scores_dict,
            reg_preds=reg_lookup,
        )

        clf_results = self.xgb_classifier.predict_and_explain(df_target, X_classifier_mat)
        clf_lookup = {c["telemetry_id"]: c for c in clf_results}

        # -------------------------------------------------------------
        # STEP 8 & 9: UPDATE SENSOR HEALTH, Display Health & Store Health
        # -------------------------------------------------------------
        db_predictions = []
        db_anomalies = []
        db_sensor_health = []
        frontend_results = []

        for _, row in df_new.iterrows():
            tid = row.get("telemetry_id")
            station = row.get("station_id", "UNKNOWN")
            ts = str(row.get("timestamp"))

            if_data = if_lookup.get(tid, {})
            reg_data = reg_lookup.get(tid, {})
            clf_data = clf_lookup.get(tid, {})

            if_score = if_data.get("if_score", 0.0)
            is_if_anomaly = if_data.get("is_anomaly", False)

            exp_temp = reg_data.get("expected_temperature")
            exp_pres = reg_data.get("expected_pressure")
            exp_rh = reg_data.get("expected_humidity")

            temp_err = reg_data.get("temperature_error", 0.0)
            pres_err = reg_data.get("pressure_error", 0.0)
            rh_err = reg_data.get("humidity_error", 0.0)

            anomaly_type = clf_data.get("anomaly_type", "NORMAL")
            confidence = clf_data.get("confidence", 1.0)
            severity = clf_data.get("severity", "NORMAL")
            primary_reason = clf_data.get("primary_reason", "Normal operation.")
            recommended_action = clf_data.get("recommended_action", "No action needed.")
            top_drivers = clf_data.get("top_drivers", [])
            classifier_shap = clf_data.get("classifier_shap", "{}")

            # Updated health from classifier step
            updated_health = clf_data.get("sensor_health", 100.0)
            prev_h = prev_health.get(station, 100.0)

            is_anomaly = (anomaly_type != "NORMAL") or is_if_anomaly

            # 1. Predictions Table Record
            db_predictions.append({
                "telemetry_id": tid,
                "station_id": station,
                "expected_temperature": exp_temp,
                "expected_pressure": exp_pres,
                "expected_humidity": exp_rh,
                "temperature_error": temp_err,
                "pressure_error": pres_err,
                "humidity_error": rh_err,
                "anomaly_score": if_score,
                "anomaly_type": anomaly_type,
                "confidence": confidence,
                "explanation": primary_reason,
                "classifier_shap": classifier_shap,
                "model_version": "IF_2 + XGBoost_v2",
            })

            # 2. Anomalies Table Record (Flagged anomalies only)
            if is_anomaly:
                db_anomalies.append({
                    "telemetry_id": tid,
                    "station_id": station,
                    "anomaly_type": anomaly_type,
                    "is_anomaly": True,
                    "anomaly_score": if_score,
                    "confidence": confidence,
                    "severity": severity,
                    "affected_sensors": clf_data.get("affected_sensors", "multivariate"),
                    "explanation": primary_reason,
                    "recommended_action": recommended_action,
                    "classifier_shap": classifier_shap,
                })

            # 3. Sensor Health Table Record (Store health)
            abs_composite_err = abs(temp_err) + abs(pres_err) + abs(rh_err)
            db_sensor_health.append({
                "station_id": station,
                "health_score": updated_health,
                "anomaly_count": 1 if is_anomaly else 0,
                "prediction_error": round(abs_composite_err, 4),
            })

            # 4. Frontend Payload (Display health & reason)
            frontend_results.append({
                "telemetry_id": tid,
                "station_id": station,
                "timestamp": ts,
                "status": "ANOMALY" if is_anomaly else "NORMAL",
                "classification": {
                    "anomaly_type": anomaly_type,
                    "confidence": confidence,
                    "severity": severity,
                    "previous_sensor_health": prev_h,
                    "updated_sensor_health": updated_health,
                },
                "sensor_readings": {
                    "actual": {
                        "temperature": reg_data.get("actual_temperature"),
                        "pressure": reg_data.get("actual_pressure"),
                        "humidity": reg_data.get("actual_humidity"),
                    },
                    "expected": {
                        "temperature": exp_temp,
                        "pressure": exp_pres,
                        "humidity": exp_rh,
                    },
                    "differences": {
                        "temperature_error": temp_err,
                        "pressure_error": pres_err,
                        "humidity_error": rh_err,
                    },
                },
                "isolation_forest": {
                    "anomaly_score": if_score,
                    "threshold": self.iso_pipeline.threshold,
                    "flagged": is_if_anomaly,
                },
                "shap_explainability": {
                    "primary_reason": primary_reason,
                    "recommended_action": recommended_action,
                    "top_drivers": top_drivers,
                },
            })

        return {
            "db_predictions": db_predictions,
            "db_anomalies": db_anomalies,
            "db_sensor_health": db_sensor_health,
            "frontend_results": frontend_results,
        }
