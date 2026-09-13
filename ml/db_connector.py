# db_connector.py
"""
Database Connector & Streamlined Data Access Layer.
Supports SQLite (zero-config default, file: sih26073.db) and PostgreSQL (via psycopg/psycopg2).
Conforms to SIH26073 schema: stations, telemetry, predictions, anomalies, sensor_health, alerts.
Maintains the complete self-healing loop:
  - Fetches previous sensor health for spatial neighbor calculation.
  - Saves predictions, residual errors, classified anomalies, and updated sensor health.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

logger = logging.getLogger("ml_pipeline.db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent.parent / "db" / "sih26073.db"


class DatabaseConnector:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", str(DEFAULT_SQLITE_PATH))
        self.is_postgres = self.db_url.startswith("postgres://") or self.db_url.startswith("postgresql://")

        if not self.is_postgres:
            Path(self.db_url).parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using SQLite database at: {self.db_url}")
        else:
            logger.info(f"Using PostgreSQL database connection: {self.db_url}")

        self.init_schema()

    def get_connection(self):
        if self.is_postgres:
            try:
                import psycopg2
                return psycopg2.connect(self.db_url)
            except ImportError:
                import psycopg
                return psycopg.connect(self.db_url)
        else:
            conn = sqlite3.connect(self.db_url, timeout=30.0)
            conn.row_factory = sqlite3.Row
            return conn

    def init_schema(self):
        """Creates tables and applies dynamic schema migrations matching the SIH architecture."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if self.is_postgres:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stations (
                    station_id VARCHAR(50) PRIMARY KEY,
                    station_name VARCHAR(100),
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    elevation DOUBLE PRECISION,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS telemetry (
                    telemetry_id BIGSERIAL PRIMARY KEY,
                    station_id VARCHAR(50) REFERENCES stations(station_id),
                    timestamp TIMESTAMP NOT NULL,
                    temperature DOUBLE PRECISION,
                    humidity DOUBLE PRECISION,
                    pressure DOUBLE PRECISION,
                    is_processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id BIGSERIAL PRIMARY KEY,
                    telemetry_id BIGINT REFERENCES telemetry(telemetry_id),
                    station_id VARCHAR(50) REFERENCES stations(station_id),
                    expected_temperature DOUBLE PRECISION,
                    expected_pressure DOUBLE PRECISION,
                    expected_humidity DOUBLE PRECISION,
                    temperature_error DOUBLE PRECISION,
                    pressure_error DOUBLE PRECISION,
                    humidity_error DOUBLE PRECISION,
                    anomaly_score DOUBLE PRECISION,
                    anomaly_type VARCHAR(50),
                    confidence DOUBLE PRECISION,
                    explanation TEXT,
                    classifier_shap TEXT,
                    model_version VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS anomalies (
                    anomaly_id BIGSERIAL PRIMARY KEY,
                    telemetry_id BIGINT REFERENCES telemetry(telemetry_id),
                    station_id VARCHAR(50) REFERENCES stations(station_id),
                    anomaly_type VARCHAR(50),
                    is_anomaly BOOLEAN NOT NULL,
                    anomaly_score DOUBLE PRECISION,
                    confidence DOUBLE PRECISION,
                    severity VARCHAR(20),
                    affected_sensors TEXT,
                    explanation TEXT,
                    recommended_action TEXT,
                    classifier_shap TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sensor_health (
                    health_id BIGSERIAL PRIMARY KEY,
                    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
                    health_score DOUBLE PRECISION,
                    anomaly_count INTEGER DEFAULT 0,
                    prediction_error DOUBLE PRECISION,
                    communication_reliability DOUBLE PRECISION DEFAULT 1.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS stations (
                    station_id TEXT PRIMARY KEY,
                    station_name TEXT,
                    latitude REAL,
                    longitude REAL,
                    elevation REAL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS telemetry (
                    telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL REFERENCES stations(station_id),
                    timestamp TEXT NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    pressure REAL,
                    is_processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telemetry_id INTEGER REFERENCES telemetry(telemetry_id),
                    station_id TEXT REFERENCES stations(station_id),
                    expected_temperature REAL,
                    expected_pressure REAL,
                    expected_humidity REAL,
                    temperature_error REAL,
                    pressure_error REAL,
                    humidity_error REAL,
                    anomaly_score REAL,
                    anomaly_type TEXT,
                    confidence REAL,
                    explanation TEXT,
                    classifier_shap TEXT,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS anomalies (
                    anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telemetry_id INTEGER REFERENCES telemetry(telemetry_id),
                    station_id TEXT REFERENCES stations(station_id),
                    anomaly_type TEXT,
                    is_anomaly INTEGER NOT NULL,
                    anomaly_score REAL,
                    confidence REAL,
                    severity TEXT,
                    affected_sensors TEXT,
                    explanation TEXT,
                    recommended_action TEXT,
                    classifier_shap TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sensor_health (
                    health_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL REFERENCES stations(station_id),
                    health_score REAL,
                    anomaly_count INTEGER DEFAULT 0,
                    prediction_error REAL,
                    communication_reliability REAL DEFAULT 1.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_telemetry_proc ON telemetry(is_processed, timestamp);
                CREATE INDEX IF NOT EXISTS idx_pred_telemetry ON predictions(telemetry_id);
                CREATE INDEX IF NOT EXISTS idx_anom_telemetry ON anomalies(telemetry_id);
                CREATE INDEX IF NOT EXISTS idx_health_station ON sensor_health(station_id, health_id);
            """)

            # Dynamic migrations for SQLite
            self._ensure_sqlite_column(cursor, "predictions", "expected_temperature", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "expected_pressure", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "expected_humidity", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "temperature_error", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "pressure_error", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "humidity_error", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "anomaly_score", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "anomaly_type", "TEXT")
            self._ensure_sqlite_column(cursor, "predictions", "confidence", "REAL")
            self._ensure_sqlite_column(cursor, "predictions", "explanation", "TEXT")
            self._ensure_sqlite_column(cursor, "predictions", "classifier_shap", "TEXT")

            self._ensure_sqlite_column(cursor, "anomalies", "confidence", "REAL")
            self._ensure_sqlite_column(cursor, "anomalies", "severity", "TEXT")
            self._ensure_sqlite_column(cursor, "anomalies", "affected_sensors", "TEXT")
            self._ensure_sqlite_column(cursor, "anomalies", "explanation", "TEXT")
            self._ensure_sqlite_column(cursor, "anomalies", "recommended_action", "TEXT")
            self._ensure_sqlite_column(cursor, "anomalies", "classifier_shap", "TEXT")

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database schema initialized and verified with complete loop tables.")

    def _ensure_sqlite_column(self, cursor, table: str, column: str, col_type: str):
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            if column not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                logger.info(f"Added column '{column}' ({col_type}) to table '{table}'.")
        except Exception as e:
            logger.warning(f"Column check for {table}.{column}: {e}")

    def seed_stations_if_empty(self):
        """Seeds default weather stations if table is empty."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stations")
        count = cursor.fetchone()[0]
        if count == 0:
            default_stations = [
                ("AWS_01", "Station Alpha", 28.6139, 77.2090, 216.0, 1),
                ("AWS_02", "Station Beta", 28.7041, 77.1025, 220.0, 1),
                ("AWS_03", "Station Gamma", 28.5355, 77.3910, 200.0, 1),
                ("AWS_04", "Station Delta", 28.4595, 77.0266, 225.0, 1),
            ]
            ph = "%s, %s, %s, %s, %s, %s" if self.is_postgres else "?, ?, ?, ?, ?, ?"
            cursor.executemany(
                f"INSERT INTO stations (station_id, station_name, latitude, longitude, elevation, is_active) VALUES ({ph})",
                default_stations
            )
            conn.commit()
            logger.info(f"Seeded {len(default_stations)} default weather stations.")
        cursor.close()
        conn.close()

    def get_latest_sensor_health(self, station_ids: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Retrieves the previous sensor health score for each station from the database.
        Returns a dict: {station_id: health_score}.
        Defaults to 100.0 if station has no prior health history.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT station_id, health_score
            FROM sensor_health
            WHERE health_id IN (
                SELECT MAX(health_id)
                FROM sensor_health
                GROUP BY station_id
            )
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        health_dict = {r[0]: float(r[1]) for r in rows}
        if station_ids:
            for st in station_ids:
                if st not in health_dict:
                    health_dict[st] = 100.0
        return health_dict

    def insert_telemetry_batch(self, readings: List[Dict[str, Any]]) -> int:
        """Inserts new sensor readings into the telemetry table."""
        if not readings:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        ph = "%s, %s, %s, %s, %s, 0" if self.is_postgres else "?, ?, ?, ?, ?, 0"

        records = [
            (
                r["station_id"],
                str(r["timestamp"]),
                float(r["temperature"]),
                float(r.get("humidity", r.get("relative_humidity", 0.0))),
                float(r["pressure"]),
            )
            for r in readings
        ]

        cursor.executemany(
            f"INSERT INTO telemetry (station_id, timestamp, temperature, humidity, pressure, is_processed) VALUES ({ph})",
            records
        )
        conn.commit()
        count = cursor.rowcount if cursor.rowcount > 0 else len(records)
        cursor.close()
        conn.close()
        return count

    def fetch_unprocessed_batch(self, batch_size: int = 500) -> List[Dict[str, Any]]:
        """Extracts the next batch of un-scored telemetry records."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                telemetry_id, station_id, timestamp, temperature, humidity, pressure 
            FROM telemetry 
            WHERE is_processed = 0 
            ORDER BY timestamp ASC, telemetry_id ASC 
            LIMIT ?
        """
        if self.is_postgres:
            query = query.replace("LIMIT ?", "LIMIT %s")
            cursor.execute(query, (batch_size,))
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            cursor.execute(query, (batch_size,))
            rows = [dict(row) for row in cursor.fetchall()]

        cursor.close()
        conn.close()
        return rows

    def fetch_trailing_history(self, stations: List[str], limit_per_station: int = 28) -> List[Dict[str, Any]]:
        """
        Fetches trailing historical readings per station from the database.
        Required to compute historical lags (lag1..24), rolling statistics, and neighbor spatial values.
        """
        if not stations:
            return []

        conn = self.get_connection()
        cursor = conn.cursor()

        history_records = []
        for st in set(stations):
            query = """
                SELECT 
                    telemetry_id, station_id, timestamp, temperature, humidity, pressure
                FROM telemetry
                WHERE station_id = ? AND is_processed = 1
                ORDER BY timestamp DESC
                LIMIT ?
            """
            if self.is_postgres:
                query = query.replace("?", "%s")
            cursor.execute(query, (st, limit_per_station))

            if self.is_postgres:
                cols = [desc[0] for desc in cursor.description]
                rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            else:
                rows = [dict(r) for r in cursor.fetchall()]

            history_records.extend(reversed(rows))

        cursor.close()
        conn.close()
        return history_records

    def stream_unprocessed_telemetry(self, chunk_size: int = 500) -> Generator[List[Dict[str, Any]], None, None]:
        """Continuously yields chunks of unprocessed telemetry."""
        while True:
            batch = self.fetch_unprocessed_batch(batch_size=chunk_size)
            if not batch:
                break
            yield batch

    def save_predictions_and_anomalies(
        self,
        predictions: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        telemetry_ids: List[int],
        health_records: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Atomic write-back in a single transaction:
        1. Inserts into 'predictions' table (expected values, residuals, anomaly_type, SHAP reasons).
        2. Inserts into 'anomalies' table (only for flagged anomalies).
        3. Inserts updated sensor health into 'sensor_health' table.
        4. Updates 'telemetry.is_processed = 1'.
        """
        if not telemetry_ids:
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Bulk insert predictions
            if predictions:
                pred_ph = "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" if self.is_postgres else "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                pred_tuples = [
                    (
                        p["telemetry_id"],
                        p["station_id"],
                        p.get("expected_temperature"),
                        p.get("expected_pressure"),
                        p.get("expected_humidity"),
                        p.get("temperature_error"),
                        p.get("pressure_error"),
                        p.get("humidity_error"),
                        p.get("anomaly_score"),
                        p.get("anomaly_type", "NORMAL"),
                        p.get("confidence", 1.0),
                        p.get("explanation"),
                        p.get("classifier_shap"),
                        p.get("model_version", "IF_2 + XGBoost_v2"),
                    )
                    for p in predictions
                ]
                cursor.executemany(
                    f"""INSERT INTO predictions (
                        telemetry_id, station_id, expected_temperature, expected_pressure, 
                        expected_humidity, temperature_error, pressure_error, humidity_error,
                        anomaly_score, anomaly_type, confidence, explanation, classifier_shap, model_version
                    ) VALUES ({pred_ph})""",
                    pred_tuples
                )

            # 2. Bulk insert anomalies
            if anomalies:
                anom_ph = (
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
                    if self.is_postgres
                    else "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                )
                anom_tuples = [
                    (
                        a["telemetry_id"],
                        a["station_id"],
                        a["anomaly_type"],
                        1 if a.get("is_anomaly", True) else 0,
                        a.get("anomaly_score"),
                        a.get("confidence", 1.0),
                        a.get("severity", "MEDIUM"),
                        a.get("affected_sensors", "multivariate"),
                        a.get("explanation"),
                        a.get("recommended_action"),
                        a.get("classifier_shap"),
                    )
                    for a in anomalies
                ]
                cursor.executemany(
                    f"""INSERT INTO anomalies (
                        telemetry_id, station_id, anomaly_type, is_anomaly, anomaly_score,
                        confidence, severity, affected_sensors, explanation, recommended_action, classifier_shap
                    ) VALUES ({anom_ph})""",
                    anom_tuples
                )

            # 3. Store updated sensor health into 'sensor_health' table
            if health_records:
                h_ph = "%s, %s, %s, %s" if self.is_postgres else "?, ?, ?, ?"
                h_tuples = [
                    (
                        h["station_id"],
                        float(h["health_score"]),
                        int(h.get("anomaly_count", 0)),
                        float(h.get("prediction_error", 0.0)),
                    )
                    for h in health_records
                ]
                cursor.executemany(
                    f"""INSERT INTO sensor_health (
                        station_id, health_score, anomaly_count, prediction_error
                    ) VALUES ({h_ph})""",
                    h_tuples
                )

            # 4. Mark telemetry records as processed
            if self.is_postgres:
                cursor.execute(
                    "UPDATE telemetry SET is_processed = 1 WHERE telemetry_id = ANY(%s)",
                    (telemetry_ids,)
                )
            else:
                cursor.executemany(
                    "UPDATE telemetry SET is_processed = 1 WHERE telemetry_id = ?",
                    [(tid,) for tid in telemetry_ids]
                )

            conn.commit()
            logger.info(
                f"Atomic write-back complete: {len(predictions)} predictions saved, "
                f"{len(anomalies)} anomalies stored, {len(health_records or [])} sensor health records stored, "
                f"{len(telemetry_ids)} telemetry records marked processed."
            )
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed during save_predictions_and_anomalies: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def get_summary_stats(self) -> Dict[str, Any]:
        """Returns processing, anomaly, and sensor health metrics."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM telemetry")
        total_telemetry = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM telemetry WHERE is_processed = 1")
        processed_telemetry = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM telemetry WHERE is_processed = 0")
        pending_telemetry = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM anomalies")
        total_anomalies = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        latest_health = self.get_latest_sensor_health()

        return {
            "total_telemetry": total_telemetry,
            "processed_telemetry": processed_telemetry,
            "pending_telemetry": pending_telemetry,
            "total_predictions": total_predictions,
            "total_anomalies": total_anomalies,
            "latest_sensor_health": latest_health,
        }
