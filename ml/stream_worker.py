# stream_worker.py
"""
5-Minute Streamlined Unified Inference Worker.
Executes "The Complete Loop" continuously:
  1. Live Stream: 4 AWS readings at same timestamp from DB.
  2. Data Validation.
  3. Previous Sensor Health (loaded from sensor_health table).
  4. Health-Weighted Spatial Neighbour Calculation.
  5. Spatial + Temporal + Seasonal Features.
  6. Parallel Isolation Forest + XGBoost Regressors.
  7. XGBoost Classifier + SHAP Explainability.
  8. Update Sensor Health.
  9. Store Health & Display Health.
  10. Feed forward to NEXT TIMESTAMP.
"""

import sys
import os
import time
import argparse
import signal
import logging
from datetime import datetime
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from unified_ml_pipeline import UnifiedMLPipeline
from db_connector import DatabaseConnector

logger = logging.getLogger("ml_pipeline.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class StreamInferenceWorker:
    def __init__(
        self,
        db_url: str = None,
        if_model_path: str = None,
        xgb_models_dir: str = None,
        chunk_size: int = 500,
        interval_seconds: int = 300,  # 5 minutes
    ):
        self.chunk_size = chunk_size
        self.interval_seconds = interval_seconds
        self.running = True

        logger.info("Initializing Database Connector...")
        self.db = DatabaseConnector(db_url=db_url)
        self.db.seed_stations_if_empty()

        logger.info("Initializing Unified ML Pipeline (Complete Loop)...")
        self.pipeline = UnifiedMLPipeline(
            if_model_path=if_model_path,
            xgb_models_dir=xgb_models_dir
        )

        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def _handle_exit(self, signum, frame):
        logger.info("\nReceived shutdown signal. Stopping worker cleanly...")
        self.running = False

    def process_pending_stream(self) -> dict:
        """
        Executes 'The Complete Loop' over all pending batches.
        """
        total_processed = 0
        total_anomalies = 0
        batches = 0
        start_time = time.time()

        for batch in self.db.stream_unprocessed_telemetry(chunk_size=self.chunk_size):
            if not batch:
                break

            batch_size = len(batch)
            telemetry_ids = [row["telemetry_id"] for row in batch]
            stations = list(set(row["station_id"] for row in batch))

            # Step 3: Fetch previous sensor health from database
            previous_sensor_health = self.db.get_latest_sensor_health(stations)

            # Fetch historical buffer for temporal lags & rolling statistics
            historical_buffer = self.db.fetch_trailing_history(stations=stations, limit_per_station=28)

            # Execute Steps 1 through 9 of The Complete Loop
            unified_results = self.pipeline.process_batch(
                new_records=batch,
                historical_buffer=historical_buffer,
                previous_sensor_health=previous_sensor_health
            )

            # Step 9: Store predictions, anomalies, and updated health in atomic transaction
            self.db.save_predictions_and_anomalies(
                predictions=unified_results["db_predictions"],
                anomalies=unified_results["db_anomalies"],
                telemetry_ids=telemetry_ids,
                health_records=unified_results["db_sensor_health"]
            )

            total_processed += batch_size
            total_anomalies += len(unified_results["db_anomalies"])
            batches += 1

            # Log health summary
            health_summary = ", ".join(f"{h['station_id']}: {h['health_score']:.1f}" for h in unified_results["db_sensor_health"])
            logger.info(
                f"[Batch {batches}] Processed {batch_size} readings | "
                f"Updated Health: [{health_summary}] | "
                f"{len(unified_results['db_anomalies'])} anomalies flagged"
            )

        duration = time.time() - start_time
        return {
            "records_processed": total_processed,
            "anomalies_flagged": total_anomalies,
            "batches": batches,
            "duration_seconds": round(duration, 3)
        }

    def run_scheduled_loop(self):
        """Main worker loop running every interval_seconds (default: 300s = 5 min)."""
        logger.info("=" * 75)
        logger.info(f"STARTING 5-MINUTE COMPLETE LOOP ANOMALY WORKER")
        logger.info(f"Polling Interval: {self.interval_seconds}s (every 5 minutes)")
        logger.info(f"Pipeline: IF (SHAP-free) + XGBoost Regressors + XGBoost Classifier + SHAP Reason")
        logger.info("=" * 75)

        iteration = 0
        while self.running:
            iteration += 1
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"\n>>> [Tick #{iteration} at {now_str}] Polling database for new telemetry...")

            try:
                result = self.process_pending_stream()
                if result["records_processed"] > 0:
                    logger.info(
                        f"Completed Tick #{iteration}: {result['records_processed']} readings processed in "
                        f"{result['duration_seconds']}s ({result['anomalies_flagged']} anomalies detected)."
                    )
                else:
                    logger.info("No pending telemetry readings. Database is up to date.")

                stats = self.db.get_summary_stats()
                logger.info(
                    f"[DB Stats] Total: {stats['total_telemetry']} | Processed: {stats['processed_telemetry']} | "
                    f"Anomalies: {stats['total_anomalies']} | Pending: {stats['pending_telemetry']}"
                )
                logger.info(f"[Current Sensor Health] {stats.get('latest_sensor_health', {})}")

            except Exception as e:
                logger.error(f"Error during stream tick processing: {e}", exc_info=True)

            if not self.running:
                break

            logger.info(f"Sleeping for {self.interval_seconds} seconds until next 5-minute tick...\n")
            for _ in range(self.interval_seconds):
                if not self.running:
                    break
                time.sleep(1)

        logger.info("Unified ML inference worker stopped.")


def main():
    parser = argparse.ArgumentParser(description="5-Minute Complete Loop Inference Worker")
    parser.add_argument("--interval", type=int, default=300, help="Interval in seconds between ticks (default: 300 = 5 min)")
    parser.add_argument("--chunk-size", type=int, default=500, help="Batch chunk size for streaming")
    parser.add_argument("--db-url", type=str, default=None, help="SQLite path or PostgreSQL connection URL")
    parser.add_argument("--once", action="store_true", help="Process pending telemetry once and exit")

    args = parser.parse_args()

    worker = StreamInferenceWorker(
        db_url=args.db_url,
        chunk_size=args.chunk_size,
        interval_seconds=args.interval
    )

    if args.once:
        logger.info("Running in single-pass mode (--once)...")
        res = worker.process_pending_stream()
        logger.info(f"Single pass complete: {res}")
    else:
        worker.run_scheduled_loop()


if __name__ == "__main__":
    main()
