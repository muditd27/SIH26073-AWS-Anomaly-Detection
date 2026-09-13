# simulate_stream.py
"""
Simulation & End-to-End Verification of "The Complete Loop":
  1. Live stream: 4 AWS readings at same timestamp
  2. Data validation
  3. Previous sensor health loaded from database
  4. Health-weighted spatial neighbour calculation
  5. Spatial + Temporal + Seasonal features
  6. Parallel Isolation Forest (if_score) + XGBoost Regressors (expected values & error diffs)
  7. XGBoost Classifier (anomaly_type + confidence + SHAP explainability)
  8. Update sensor health
  9. Display health (Frontend) & Store health (Database)
  10. Next timestamp: new weighted-neighbour calculation using updated health!
"""

import os
import sys
import time
import argparse
import pandas as pd
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from db_connector import DatabaseConnector
from stream_worker import StreamInferenceWorker

CANDIDATE_DATASETS = [
    Path(r"C:\Users\koush\OneDrive\Desktop\manual\anomalous_aws_data_3_months.csv"),
    Path(r"C:\Users\koush\OneDrive\Desktop\manual\clean_aws_data_3_months.csv"),
    Path(r"C:\Users\koush\.gemini\antigravity\scratch\isolation_forest\aws_weather_data.csv"),
]


def find_dataset() -> Path:
    for candidate in CANDIDATE_DATASETS:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find source dataset in: {[str(p) for p in CANDIDATE_DATASETS]}")


def run_simulation(steps: int = 3, batch_per_step: int = 4, delay: float = 0.5):
    dataset_path = find_dataset()
    print(f"\n=========================================================================")
    print(f"      VERIFYING 'THE COMPLETE LOOP' ARCHITECTURE (END-TO-END)           ")
    print(f"=========================================================================")
    print(f"Source Dataset: {dataset_path}")
    print(f"Simulation Intervals: {steps} steps (4 stations per step)")

    db = DatabaseConnector()
    db.seed_stations_if_empty()
    worker = StreamInferenceWorker(interval_seconds=300)

    df = pd.read_csv(dataset_path)
    total_available = len(df)
    print(f"Total readings available: {total_available:,}")

    if "relative_humidity" in df.columns and "humidity" not in df.columns:
        df["humidity"] = df["relative_humidity"]

    read_index = 0

    for step in range(1, steps + 1):
        print(f"\n" + "=" * 80)
        print(f"--- [TIMESTAMP STEP #{step}]: Live Stream of 4 Stations arriving at DB ---")
        print("=" * 80)

        # 1. LIVE STREAM (4 AWS readings at same timestamp)
        end_idx = min(read_index + batch_per_step, total_available)
        slice_df = df.iloc[read_index:end_idx].copy()
        read_index = end_idx

        # If step 2, inject a spike on AWS_01 to demonstrate health penalty and loop feedback!
        if step == 2:
            print("[Simulation Event] Injecting an anomaly spike on AWS_01 (Temp -> 53.0°C) to test health penalty loop...")
            slice_df.loc[slice_df["station_id"] == "AWS_01", "temperature"] = 53.0

        records_to_insert = slice_df[["station_id", "timestamp", "temperature", "humidity", "pressure"]].to_dict(orient="records")
        inserted_count = db.insert_telemetry_batch(records_to_insert)
        print(f"[1. Live Stream] Inserted {inserted_count} new raw rows into 'telemetry' table.")

        # Display previous health from DB before processing
        prev_health = db.get_latest_sensor_health(["AWS_01", "AWS_02", "AWS_03", "AWS_04"])
        print(f"[3. Previous Health (from DB)] {prev_health}")

        # Worker executes the complete loop
        print("[4-8. Pipeline Execution] Health-weighted spatial calc -> Features -> IF & Regressors -> Classifier & SHAP -> Health Update...")
        tick_result = worker.process_pending_stream()
        print(f"[9. Store & Display Health] Processed in {tick_result['duration_seconds']}s | {tick_result['anomalies_flagged']} anomalies detected.")

        # Display updated health in DB
        new_health = db.get_latest_sensor_health(["AWS_01", "AWS_02", "AWS_03", "AWS_04"])
        print(f"[9. Updated Health (in DB)]   {new_health}")
        print(f"[10. Feed Forward] These health scores will weight neighbor calculations for Step #{step + 1}!")

        time.sleep(delay)

    # Final DB Verification
    print("\n" + "=" * 135)
    print("FINAL DATABASE VERIFICATION: TELEMETRY + PREDICTIONS + SENSOR HEALTH + SHAP REASONS")
    print("=" * 135)

    conn = db.get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            t.telemetry_id,
            t.station_id,
            t.temperature AS act_temp,
            p.expected_temperature AS exp_temp,
            p.temperature_error AS temp_diff,
            p.anomaly_score AS if_score,
            p.anomaly_type,
            p.confidence,
            p.explanation
        FROM telemetry t
        LEFT JOIN predictions p ON t.telemetry_id = p.telemetry_id
        ORDER BY t.telemetry_id DESC
        LIMIT 8;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    header = (
        f"{'ID':<4} | {'Station':<7} | {'Act Temp':<8} | {'Exp Temp':<8} | {'Temp Diff':<9} | "
        f"{'IF Score':<9} | {'Classified Anomaly':<20} | {'Conf':<6} | {'SHAP-Generated Reason'}"
    )
    print(header)
    print("-" * 135)

    for r in rows:
        tid, st_id, at, et, dt, if_s, atype, conf, expl = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]
        at_s = f"{at:.2f}" if at is not None else "-"
        et_s = f"{et:.2f}" if et is not None else "-"
        dt_s = f"{dt:+.2f}" if dt is not None else "-"
        if_str = f"{if_s:+.4f}" if if_s is not None else "-"
        atype_str = str(atype) if atype else "NORMAL"
        conf_str = f"{conf*100:.1f}%" if conf is not None else "-"
        expl_str = str(expl)[:52] + "..." if expl and len(str(expl)) > 52 else str(expl or "-")

        print(
            f"{tid:<4} | {st_id:<7} | {at_s:<8} | {et_s:<8} | {dt_s:<9} | "
            f"{if_str:<9} | {atype_str:<20} | {conf_str:<6} | {expl_str}"
        )

    stats = db.get_summary_stats()
    print("\n" + "=" * 45)
    print("FINAL DATABASE TOTALS & SENSOR HEALTH:")
    print(f"Total Telemetry:      {stats['total_telemetry']}")
    print(f"Processed Rows:       {stats['processed_telemetry']}")
    print(f"Predictions Stored:   {stats['total_predictions']}")
    print(f"Anomalies Stored:     {stats['total_anomalies']}")
    print(f"Current Sensor Health:{stats.get('latest_sensor_health', {})}")
    print("=" * 45)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify The Complete Loop architecture")
    parser.add_argument("--steps", type=int, default=3, help="Number of simulation steps to run")
    parser.add_argument("--batch", type=int, default=4, help="Number of readings per step (4 stations)")
    args = parser.parse_args()

    run_simulation(steps=args.steps, batch_per_step=args.batch)
