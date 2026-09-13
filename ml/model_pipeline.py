# model_pipeline.py
"""
Isolation Forest Anomaly Detection Pipeline (SHAP-free for maximum throughput).
Loads the trained pipeline (StandardScaler + IsolationForest),
validates sensor inputs, and computes decision function scores using best_threshold = -0.10099999999999965.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger("ml_pipeline.isolation_forest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DEFAULT_MODEL_FILENAME = "isolation_forest_IF_2_pipeline.joblib"
MODEL_NAME = "IF_2"
BEST_THRESHOLD = -0.10099999999999965
REQUIRED_FEATURES = ["temperature", "pressure", "relative_humidity"]

SEARCH_DIRS = [
    Path("."),
    Path(__file__).resolve().parent,
    Path(r"C:\Users\koush\OneDrive\Desktop\manual"),
    Path(r"C:\Users\koush\OneDrive\Desktop\manual\SIH26073-AWS-Anomaly-Detection\backend\app\ml_pipeline"),
    Path(r"C:\Users\koush\.gemini\antigravity\scratch\isolation_forest\ml_pipeline"),
]


class AnomalyModelPipeline:
    def __init__(
        self,
        model_path: Optional[str] = None,
        threshold: float = BEST_THRESHOLD,
    ):
        self.model_name = MODEL_NAME
        self.threshold = threshold
        self.features = REQUIRED_FEATURES
        self.model_path = self._resolve_file(model_path, DEFAULT_MODEL_FILENAME)
        self.pipeline = self._load_model()

    def _resolve_file(self, custom_path: Optional[str], default_name: str) -> Path:
        if custom_path and os.path.exists(custom_path):
            return Path(custom_path)
        for directory in SEARCH_DIRS:
            candidate = directory / default_name
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"Could not locate '{default_name}'. Searched: {[str(d) for d in SEARCH_DIRS]}")

    def _load_model(self):
        logger.info(f"Loading IF_2 model pipeline from: {self.model_path}")
        pipeline = joblib.load(self.model_path)
        logger.info(f"Loaded Isolation Forest: {type(pipeline).__name__} | Threshold: {self.threshold}")
        return pipeline

    def prepare_dataframe(self, records: Union[List[Dict[str, Any]], pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Maps humidity columns and extracts required raw features."""
        if isinstance(records, pd.DataFrame):
            df = records.copy()
        else:
            df = pd.DataFrame(records)

        if df.empty:
            return df, pd.DataFrame()

        if "humidity" in df.columns and "relative_humidity" not in df.columns:
            df["relative_humidity"] = df["humidity"]
        elif "relative_humidity" in df.columns and "humidity" not in df.columns:
            df["humidity"] = df["relative_humidity"]

        for col in self.features:
            if col not in df.columns:
                raise ValueError(f"Missing required sensor feature: '{col}'")
            df[col] = pd.to_numeric(df[col], errors="coerce")

        feature_df = df[self.features].copy()
        if feature_df.isna().any().any():
            feature_df = feature_df.fillna(feature_df.mean()).fillna(0.0)

        return df, feature_df

    def score_records(
        self, records: Union[List[Dict[str, Any]], pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """
        Runs high-speed Isolation Forest inference on a batch of telemetry records.
        Returns:
            predictions_list: list of dicts with telemetry_id, station_id, if_score, is_anomaly.
        """
        if records is None or len(records) == 0:
            return []

        df, feature_df = self.prepare_dataframe(records)
        if feature_df.empty:
            return []

        # Scikit-learn Isolation Forest decision function
        # Negative values indicate outliers/anomalies
        if_scores = self.pipeline.decision_function(feature_df)

        predictions_list = []
        for i, row in df.iterrows():
            telemetry_id = row.get("telemetry_id") or row.get("id")
            station_id = row.get("station_id", "UNKNOWN")
            score = float(if_scores[i])
            is_anomaly = bool(score < self.threshold)

            pred_item = {
                "telemetry_id": int(telemetry_id) if telemetry_id is not None else None,
                "station_id": str(station_id),
                "if_score": round(score, 6),
                "anomaly_score": round(score, 6),
                "is_anomaly": is_anomaly,
                "model_version": self.model_name,
            }
            predictions_list.append(pred_item)

        return predictions_list
