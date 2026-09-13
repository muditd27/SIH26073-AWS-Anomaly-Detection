# xgboost_regressor.py
"""
XGBoost Multi-Sensor Regression & Error Analysis Module.
Predicts expected weather values (temperature, pressure, relative humidity)
using historical lags, rolling means, rolling standard deviations, and spatial features.
Computes residuals/differences between actual and predicted values for:
  1. Frontend dashboard visualizations (actual vs expected, error trajectories).
  2. Downstream XGBoost classifier input features.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger("ml_pipeline.xgboost")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

SEARCH_MODEL_DIRS = [
    Path("models"),
    Path(__file__).resolve().parent / "models",
    Path(r"C:\Users\koush\OneDrive\Desktop\manual\models"),
    Path(r"C:\Users\koush\OneDrive\Desktop\manual\SIH26073-AWS-Anomaly-Detection\backend\app\ml_pipeline\models"),
    Path(r"C:\Users\koush\.gemini\antigravity\scratch\isolation_forest\ml_pipeline\models"),
]


class XGBoostWeatherRegressor:
    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = self._resolve_models_dir(models_dir)
        logger.info(f"Loading XGBoost models from: {self.models_dir}")

        self.temp_model = joblib.load(self.models_dir / "temperature_model.pkl")
        self.pres_model = joblib.load(self.models_dir / "pressure_model.pkl")
        self.rh_model = joblib.load(self.models_dir / "rh_model.pkl")
        self.feature_names = joblib.load(self.models_dir / "feature_list.pkl")

        logger.info(f"Loaded 3 XGBoost regressors (Temp, Pres, RH) with {len(self.feature_names)} features.")

    def _resolve_models_dir(self, custom_dir: Optional[str]) -> Path:
        if custom_dir and os.path.exists(custom_dir):
            return Path(custom_dir)
        for candidate in SEARCH_MODEL_DIRS:
            if candidate.exists() and (candidate / "temperature_model.pkl").exists():
                return candidate
        raise FileNotFoundError(f"Could not find XGBoost models in candidate paths: {[str(d) for d in SEARCH_MODEL_DIRS]}")

    def compute_features(self, df_input: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates historical lags, rolling stats (mean, std, min, max),
        cyclical temporal features, and spatial neighbor consensus.
        """
        df = df_input.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        if "humidity" in df.columns and "relative_humidity" not in df.columns:
            df["relative_humidity"] = df["humidity"]
        elif "relative_humidity" in df.columns and "humidity" not in df.columns:
            df["humidity"] = df["relative_humidity"]

        # Ensure sorted chronologically per station
        df = df.sort_values(["station_id", "timestamp"]).reset_index(drop=True)

        for col in ["temperature", "pressure", "relative_humidity"]:
            # 1. Direct Historical Lags (Safe)
            df[f"{col}_lag1"] = df.groupby("station_id")[col].shift(1)
            df[f"{col}_lag2"] = df.groupby("station_id")[col].shift(2)
            df[f"{col}_lag3"] = df.groupby("station_id")[col].shift(3)
            df[f"{col}_lag24"] = df.groupby("station_id")[col].shift(24)

            # Cold start fallback: if early history lacks 24 lags, backfill with closest lag
            df[f"{col}_lag1"] = df[f"{col}_lag1"].bfill().ffill().fillna(df[col])
            df[f"{col}_lag2"] = df[f"{col}_lag2"].bfill().ffill().fillna(df[f"{col}_lag1"])
            df[f"{col}_lag3"] = df[f"{col}_lag3"].bfill().ffill().fillna(df[f"{col}_lag2"])
            df[f"{col}_lag24"] = df[f"{col}_lag24"].bfill().ffill().fillna(df[f"{col}_lag3"])

            # 2. Lagged Deltas / Momentum
            df[f"{col}_momentum_1h"] = df[f"{col}_lag1"] - df[f"{col}_lag2"]
            df[f"{col}_momentum_24h"] = df[f"{col}_lag1"] - df[f"{col}_lag24"]

            # 3. Lagged Rolling Statistics (mean, std, max, min)
            for window in [3, 6, 24]:
                rolling_obj = df.groupby("station_id")[f"{col}_lag1"].rolling(window=window, min_periods=1)
                df[f"{col}_rolling_{window}h_mean"] = rolling_obj.mean().reset_index(level=0, drop=True)
                df[f"{col}_rolling_{window}h_std"] = rolling_obj.std().reset_index(level=0, drop=True).fillna(0.0)
                df[f"{col}_rolling_{window}h_max"] = rolling_obj.max().reset_index(level=0, drop=True)
                df[f"{col}_rolling_{window}h_min"] = rolling_obj.min().reset_index(level=0, drop=True)

        # 4. Cyclical Temporal Features
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_year"] = df["timestamp"].dt.dayofyear

        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
        df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.0)
        df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.0)

        # 5. Lagged Spatial Features
        for col in ["temperature", "pressure", "relative_humidity"]:
            lag1_col = f"{col}_lag1"
            total_lag1 = df.groupby("timestamp")[lag1_col].transform("sum")
            count_lag1 = df.groupby("timestamp")[lag1_col].transform("count")

            denom = count_lag1.replace(1, np.nan) - 1
            df[f"neighbor_mean_{col}_lag1"] = (total_lag1 - df[lag1_col]) / denom
            df[f"neighbor_mean_{col}_lag1"] = df[f"neighbor_mean_{col}_lag1"].fillna(df[lag1_col])
            df[f"{col}_neighbor_diff_lag1"] = df[lag1_col] - df[f"neighbor_mean_{col}_lag1"]

        # 6. Interactions
        df["temp_rh_interaction_lag1"] = df["temperature_lag1"] * df["relative_humidity_lag1"]

        return df

    def predict_readings(
        self,
        new_records: List[Dict[str, Any]],
        historical_buffer: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes regression inference on incoming readings with historical context.
        Returns prediction results containing:
          - expected_temperature, expected_pressure, expected_humidity
          - temperature_error, pressure_error, humidity_error
          - absolute & percentage errors
          - classifier feature vector ready for downstream XGBoost Classifier
        """
        if not new_records:
            return []

        df_new = pd.DataFrame(new_records)
        target_ids = set()
        if "telemetry_id" in df_new.columns:
            target_ids = set(df_new["telemetry_id"].tolist())

        # Concatenate historical buffer with new records for rolling feature calculation
        if historical_buffer:
            df_hist = pd.DataFrame(historical_buffer)
            df_combined = pd.concat([df_hist, df_new], ignore_index=True)
        else:
            df_combined = df_new

        # Compute lags, rolling stats (mean, std, etc.)
        df_featured = self.compute_features(df_combined)

        # Filter to only the new incoming records
        if target_ids:
            df_target = df_featured[df_featured["telemetry_id"].isin(target_ids)].copy()
        else:
            df_target = df_featured.tail(len(new_records)).copy()

        # Extract features required by XGBoost models
        X_reg = df_target[self.feature_names].fillna(0.0)

        # Predict expected physical values
        pred_temp = self.temp_model.predict(X_reg)
        pred_pres = self.pres_model.predict(X_reg)
        pred_rh = self.rh_model.predict(X_reg)

        results = []
        for idx, (_, row) in enumerate(df_target.iterrows()):
            act_temp = float(row["temperature"])
            act_pres = float(row["pressure"])
            act_rh = float(row.get("relative_humidity", row.get("humidity", 0.0)))

            exp_temp = float(pred_temp[idx])
            exp_pres = float(pred_pres[idx])
            exp_rh = float(pred_rh[idx])

            # Compute residuals / differences: (actual - expected)
            diff_temp = act_temp - exp_temp
            diff_pres = act_pres - exp_pres
            diff_rh = act_rh - exp_rh

            tid = row.get("telemetry_id")
            station = row.get("station_id", "UNKNOWN")
            ts = str(row.get("timestamp"))

            # Package output for Frontend and Downstream Classifier
            res = {
                "telemetry_id": int(tid) if tid is not None else None,
                "station_id": station,
                "timestamp": ts,

                # Actual values
                "actual_temperature": round(act_temp, 2),
                "actual_pressure": round(act_pres, 2),
                "actual_humidity": round(act_rh, 2),

                # Predicted values (for Frontend)
                "expected_temperature": round(exp_temp, 2),
                "expected_pressure": round(exp_pres, 2),
                "expected_humidity": round(exp_rh, 2),

                # Differences / Residual errors (for Downstream XGBoost Classifier & Frontend)
                "temperature_error": round(diff_temp, 4),
                "pressure_error": round(diff_pres, 4),
                "humidity_error": round(diff_rh, 4),
                "abs_temperature_error": round(abs(diff_temp), 4),
                "abs_pressure_error": round(abs(diff_pres), 4),
                "abs_humidity_error": round(abs(diff_rh), 4),

                # Classifier input feature dictionary ready for future classification model
                "classifier_features": {
                    "temperature_error": round(diff_temp, 4),
                    "pressure_error": round(diff_pres, 4),
                    "humidity_error": round(diff_rh, 4),
                    "abs_temperature_error": round(abs(diff_temp), 4),
                    "abs_pressure_error": round(abs(diff_pres), 4),
                    "abs_humidity_error": round(abs(diff_rh), 4),
                    "temp_rolling_3h_std": round(float(row.get("temperature_rolling_3h_std", 0.0)), 4),
                    "pres_rolling_3h_std": round(float(row.get("pressure_rolling_3h_std", 0.0)), 4),
                    "rh_rolling_3h_std": round(float(row.get("relative_humidity_rolling_3h_std", 0.0)), 4),
                }
            }
            results.append(res)

        return results
