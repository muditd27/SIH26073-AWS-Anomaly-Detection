"""
Data provider module for SkyGuard AI Streamlit Dashboard.
Connects directly to the SIH26073 database (SQLite/PostgreSQL) and ML pipeline telemetry.
Strictly 3 sensors: Temperature, Pressure, Relative Humidity (no wind or weather).
"""
from __future__ import annotations

import os
import math
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
SQLITE_DB_PATH = Path(__file__).resolve().parent / "db" / "sih26073.db"
LAST_UPDATED = "14:32:08"


def get_db_connection():
    """Returns connection to SQLite or PostgreSQL database."""
    db_url = os.getenv("DATABASE_URL")
    if db_url and (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
        try:
            import psycopg2
            return psycopg2.connect(db_url)
        except Exception:
            pass

    if SQLITE_DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(SQLITE_DB_PATH), timeout=10.0)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"Error connecting to SQLite: {e}")
    return None


def connectivity_class(status: str) -> str:
    return {"Online": "ok", "Warning": "warn"}.get(status, "bad")


def health_tone(health: int) -> str:
    if health >= 85:
        return "ok"
    if health >= 65:
        return "warn"
    return "bad"


def anomaly_class(status: str) -> str:
    lower = status.lower()
    if "anomaly detected" in lower or "critical" in lower:
        return "bad"
    if "possible" in lower or "warning" in lower:
        return "warn"
    return "ok"


def delta(actual: float, expected: float) -> str:
    diff = actual - expected
    return f"{'+' if diff >= 0 else ''}{diff:.1f}"


def generate_physical_trends(station_id: str, time_range: str = "3M") -> list[dict]:
    """Generates continuous, smooth, realistic meteorological curves matching physical weather trends."""
    if time_range == "7D":
        pts = 42  # every 4 hours for 7 days
        step_hours = 4
    elif time_range == "1M":
        pts = 30  # 1 point per day for 30 days
        step_hours = 24
    else:  # 3M
        pts = 90  # 1 point per day for 90 days
        step_hours = 24

    end_time = datetime(2025, 4, 27, 14, 30, 0)

    base_t = {"AWS001": 28.0, "AWS002": 30.5, "AWS003": 28.5, "AWS004": 24.5}.get(station_id, 26.0)
    base_p = {"AWS001": 1012.0, "AWS002": 1009.0, "AWS003": 1011.0, "AWS004": 1015.2}.get(station_id, 1012.0)
    base_h = {"AWS001": 74.0, "AWS002": 66.0, "AWS003": 70.0, "AWS004": 65.5}.get(station_id, 68.0)

    records = []
    for i in range(pts):
        dt = end_time - timedelta(hours=step_hours * (pts - 1 - i))
        ts_str = dt.strftime("%Y-%m-%d %H:%M") if time_range == "7D" else dt.strftime("%Y-%m-%d")
        lbl = dt.strftime("%a %H:%M") if time_range == "7D" else dt.strftime("%b %d")

        prog = i / max(1, pts - 1)

        # Smooth seasonal envelope
        s_t = 5.5 * math.sin(prog * math.pi)
        s_p = -3.0 * math.sin(prog * math.pi)
        s_h = -5.0 * math.sin(prog * math.pi)

        # Synoptic scale weather front progression
        syn_t = 1.6 * math.sin(prog * 10.0) + 0.8 * math.cos(prog * 18.0)
        syn_p = -1.8 * math.sin(prog * 10.0) - 0.9 * math.cos(prog * 18.0)
        syn_h = 2.2 * math.sin(prog * 10.0) + 1.1 * math.cos(prog * 18.0)

        # Diurnal day/night cycle
        if time_range == "7D":
            hr = dt.hour
            d_t = 3.2 * math.sin((hr - 8) * math.pi / 12)
            d_p = 1.0 * math.cos(hr * math.pi / 6)
            d_h = -4.0 * math.sin((hr - 8) * math.pi / 12)
        else:
            d_t = d_p = d_h = 0.0

        exp_t = round(base_t + s_t + syn_t + d_t, 1)
        exp_p = round(base_p + s_p + syn_p + d_p, 1)
        exp_h = round(max(25.0, min(95.0, base_h + s_h + syn_h + d_h)), 1)

        noise_t = 0.35 * math.sin(i * 1.3) + 0.2 * math.cos(i * 2.7)
        noise_p = 0.45 * math.cos(i * 1.1) + 0.25 * math.sin(i * 2.2)
        noise_h = 0.55 * math.sin(i * 1.4) + 0.3 * math.cos(i * 2.5)

        act_t = round(exp_t + noise_t, 1)
        act_p = round(exp_p + noise_p, 1)
        act_h = round(max(20.0, min(98.0, exp_h + noise_h)), 1)

        # Anomaly divergence in the latest points
        if station_id == "AWS001" and i >= pts - 5:
            ramp = (i - (pts - 5)) / 4.0
            act_t = round(exp_t + (11.6 * ramp), 1)
            act_p = round(exp_p - (7.9 * ramp), 1)
            act_h = round(min(98.0, exp_h + (14.7 * ramp)), 1)
        elif station_id == "AWS002" and i >= pts - 20:
            drift = min(2.2, (i - (pts - 20)) * 0.11)
            act_t = round(exp_t + drift, 1)
            act_p = round(exp_p - (0.7 * (drift / 2.2)), 1)
            act_h = round(min(98.0, exp_h + (2.0 * (drift / 2.2))), 1)
        elif station_id == "AWS003" and i >= pts - 4:
            ramp = (i - (pts - 4)) / 3.0
            act_t = round(exp_t + (14.8 * ramp), 1)
            act_p = round(exp_p - (8.2 * ramp), 1)
            act_h = round(min(98.0, exp_h + (19.0 * ramp)), 1)

        records.append({
            "label": lbl,
            "timestamp": ts_str,
            "tempActual": act_t,
            "tempExpected": exp_t,
            "pressActual": act_p,
            "pressExpected": exp_p,
            "humActual": act_h,
            "humExpected": exp_h,
        })
    return records


def generate_station_readings(station_id: str) -> list[dict]:
    """Generates strictly 24 recent 5-minute ticks with unique timestamps and no wind/weather."""
    # First try querying recent telemetry directly from database
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            db_id = station_id.replace("AWS00", "AWS_0").replace("AWS0", "AWS_")
            cursor.execute(
                "SELECT telemetry_id, timestamp, temperature, pressure, humidity FROM telemetry WHERE station_id IN (?, ?) ORDER BY timestamp DESC LIMIT 24",
                (station_id, db_id)
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return [
                    {
                        "id": idx + 1,
                        "timestamp": str(r[1]),
                        "temp": round(float(r[2]), 1) if r[2] is not None else 25.0,
                        "pressure": round(float(r[3]), 1) if r[3] is not None else 1013.0,
                        "humidity": round(float(r[4]), 1) if r[4] is not None else 65.0,
                    }
                    for idx, r in enumerate(rows)
                ]
        except Exception as e:
            print(f"Error querying telemetry table: {e}")

    # Fallback to simulated 5-minute ticks
    base_time = datetime(2025, 4, 27, 14, 32, 0)
    base_t = {"AWS001": 28.4, "AWS002": 32.7, "AWS003": 42.8, "AWS004": 24.6}.get(station_id, 28.0)
    base_p = {"AWS001": 1011.8, "AWS002": 1008.3, "AWS003": 1004.2, "AWS004": 1015.6}.get(station_id, 1012.0)
    base_h = {"AWS001": 72.0, "AWS002": 68.0, "AWS003": 89.0, "AWS004": 66.0}.get(station_id, 70.0)

    rows = []
    for i in range(1, 25):
        t = base_time - timedelta(minutes=(i - 1) * 5)
        t_val = round(base_t - (i * 0.12) + (math.sin(i * 1.5) * 0.15), 1)
        p_val = round(base_p + (i * 0.18) + (math.cos(i * 1.2) * 0.1), 1)
        h_val = round(max(20.0, min(100.0, base_h - (i * 0.08) + (math.sin(i * 2.1) * 0.2))), 1)

        rows.append({
            "id": i,
            "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
            "temp": t_val,
            "pressure": p_val,
            "humidity": h_val,
        })
    return rows


def get_station_anomalies_list(station_id: str) -> list[dict]:
    """Anomaly log events for each station with database lookup."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            db_id = station_id.replace("AWS00", "AWS_0").replace("AWS0", "AWS_")
            cursor.execute(
                "SELECT anomaly_id, detected_at, anomaly_type, severity, explanation, recommended_action FROM anomalies WHERE station_id IN (?, ?) ORDER BY detected_at DESC LIMIT 10",
                (station_id, db_id)
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return [
                    {
                        "id": f"AL-{r[0]}",
                        "timestamp": str(r[1]),
                        "type": str(r[2] or "ANOMALY"),
                        "severity": str(r[3] or "HIGH"),
                        "message": str(r[4] or "Anomaly flagged by ML pipeline."),
                        "action": str(r[5] or "Inspect sensor."),
                    }
                    for r in rows
                ]
        except Exception as e:
            print(f"Error querying anomalies table: {e}")

    logs = {
        "AWS001": [
            {
                "id": "AL-1092",
                "timestamp": "2025-04-27 14:30:15",
                "type": "OUT_OF_BOUNDS_RAIL",
                "severity": "CRITICAL",
                "message": "Temperature reading surge (+11.6°C) and RH (+14.7%) exceeded physical gradient limits.",
                "action": "Inspect ADC channel and replace sensor assembly.",
            },
            {
                "id": "AL-1088",
                "timestamp": "2025-04-27 12:15:00",
                "type": "SENSOR_SPIKE",
                "severity": "HIGH",
                "message": "Transient temperature spike of +6.2°C detected within 5-minute sampling window.",
                "action": "Verify electrical grounding and power supply ripple.",
            },
            {
                "id": "AL-1075",
                "timestamp": "2025-04-26 18:40:22",
                "type": "GENUINE_WEATHER_FRONT",
                "severity": "LOW",
                "message": "Correlated regional atmospheric drop verified across neighbor stations.",
                "action": "Atmospheric event verified by consensus; no maintenance required.",
            },
        ],
        "AWS002": [
            {
                "id": "AL-2041",
                "timestamp": "2025-04-27 14:25:00",
                "type": "SENSOR_DRIFT",
                "severity": "MEDIUM",
                "message": "Continuous positive drift (+2.2°C) against regional peer station consensus.",
                "action": "Schedule recalibration of temperature sensor during next maintenance window.",
            },
            {
                "id": "AL-2035",
                "timestamp": "2025-04-26 09:10:00",
                "type": "GENUINE_WEATHER_FRONT",
                "severity": "LOW",
                "message": "Minor barometric pressure change matching regional weather progression.",
                "action": "Routine observation; sensors within safe bounds.",
            },
        ],
        "AWS003": [
            {
                "id": "AL-3099",
                "timestamp": "2025-04-27 14:20:00",
                "type": "SENSOR_SPIKE",
                "severity": "CRITICAL",
                "message": "Extreme multi-channel divergence: Temp 42.8°C (+14.8°C error) and RH 89.0%.",
                "action": "Immediate isolation; hardware sensor failure confirmed.",
            },
            {
                "id": "AL-3081",
                "timestamp": "2025-04-27 10:05:00",
                "type": "OUT_OF_BOUNDS_RAIL",
                "severity": "HIGH",
                "message": "ADC voltage reading pegged to maximum upper rail limit.",
                "action": "Inspect sensor circuit board for short circuit.",
            },
        ],
        "AWS004": [
            {
                "id": "AL-4012",
                "timestamp": "2025-04-25 11:30:00",
                "type": "GENUINE_WEATHER_FRONT",
                "severity": "LOW",
                "message": "Normal atmospheric perturbation verified across regional network.",
                "action": "All sensors nominal; no action required.",
            },
        ],
    }
    return logs.get(station_id, [])


# Preset master stations matching reference specification
STATIONS_CONFIG = [
    {
        "id": "AWS001",
        "number": "01",
        "name": "Station 01",
        "connectivity": "Online",
        "lastRecorded": "2025-04-27 14:32:08",
        "sensorHealth": 94,
        "stationStatus": "Normal",
        "temperature": 42.8,
        "expectedTemp": 31.2,
        "pressure": 1004.2,
        "expectedPressure": 1012.1,
        "humidity": 89.2,
        "expectedHumidity": 74.5,
        "anomalyScore": 0.87,
        "confidence": 92,
        "anomalyStatus": "Anomaly Detected",
        "anomalyType": "OUT_OF_BOUNDS_RAIL",
        "primary_feature": "Temperature",
        "shap_drivers": {"Temperature": 76, "Relative Humidity": 16, "Pressure": 8},
        "reason": "Temperature (+11.6°C) and RH (+14.7%) significantly higher than physical baseline.",
        "recommendedAction": "Inspect ADC channel and check sensor probe.",
        "lastUpdated": "14:32:08",
    },
    {
        "id": "AWS002",
        "number": "02",
        "name": "Station 02",
        "connectivity": "Warning",
        "lastRecorded": "2025-04-27 14:26:17",
        "sensorHealth": 76,
        "stationStatus": "Warning",
        "temperature": 32.7,
        "expectedTemp": 30.5,
        "pressure": 1008.3,
        "expectedPressure": 1009.0,
        "humidity": 68.0,
        "expectedHumidity": 66.0,
        "anomalyScore": 0.45,
        "confidence": 74,
        "anomalyStatus": "Possible Anomaly",
        "anomalyType": "SENSOR_DRIFT",
        "primary_feature": "Temperature",
        "shap_drivers": {"Temperature": 68, "Relative Humidity": 20, "Pressure": 12},
        "reason": "Gradual calibration drift detected on temperature sensor relative to regional consensus (+2.2°C).",
        "recommendedAction": "Schedule sensor recalibration at next maintenance cycle.",
        "lastUpdated": "14:26:17",
    },
    {
        "id": "AWS003",
        "number": "03",
        "name": "Station 03",
        "connectivity": "Critical",
        "lastRecorded": "2025-04-27 14:21:03",
        "sensorHealth": 61,
        "stationStatus": "Critical",
        "temperature": 42.8,
        "expectedTemp": 28.0,
        "pressure": 1004.2,
        "expectedPressure": 1012.0,
        "humidity": 89.0,
        "expectedHumidity": 70.0,
        "anomalyScore": 0.88,
        "confidence": 96,
        "anomalyStatus": "Anomaly Detected",
        "anomalyType": "SENSOR_SPIKE",
        "primary_feature": "Temperature",
        "shap_drivers": {"Temperature": 82, "Relative Humidity": 12, "Pressure": 6},
        "reason": "Sharp transient jump on temperature channel (+14.8°C error) exceeding physical rate of change.",
        "recommendedAction": "Isolate unit, inspect electrical grounding, and replace sensor probe.",
        "lastUpdated": "14:21:03",
    },
    {
        "id": "AWS004",
        "number": "04",
        "name": "Station 04",
        "connectivity": "Online",
        "lastRecorded": "2025-04-27 14:31:42",
        "sensorHealth": 97,
        "stationStatus": "Normal",
        "temperature": 24.6,
        "expectedTemp": 24.8,
        "pressure": 1015.6,
        "expectedPressure": 1015.2,
        "humidity": 66.0,
        "expectedHumidity": 65.5,
        "anomalyScore": 0.08,
        "confidence": 98,
        "anomalyStatus": "Normal",
        "anomalyType": "NORMAL",
        "primary_feature": "None",
        "shap_drivers": {"Temperature": 34, "Relative Humidity": 33, "Pressure": 33},
        "reason": "Sensor measurements align perfectly with physical theoretical models and regional peers.",
        "recommendedAction": "No maintenance required.",
        "lastUpdated": "14:31:42",
    },
]


def get_stations() -> list[dict]:
    """Fetches stations directly from database, falling back cleanly to STATIONS_CONFIG."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.station_id,
                    s.station_name,
                    t.temperature,
                    t.pressure,
                    t.humidity,
                    t.timestamp,
                    sh.health_score,
                    sh.communication_reliability,
                    p.expected_temperature,
                    p.expected_pressure,
                    p.expected_humidity,
                    p.anomaly_score,
                    a.anomaly_type,
                    a.severity,
                    a.explanation,
                    a.recommended_action,
                    a.classifier_shap
                FROM stations s
                LEFT JOIN telemetry t ON t.telemetry_id = (
                    SELECT MAX(t2.telemetry_id) FROM telemetry t2 WHERE t2.station_id = s.station_id
                )
                LEFT JOIN predictions p ON p.telemetry_id = t.telemetry_id
                LEFT JOIN sensor_health sh ON sh.health_id = (
                    SELECT MAX(sh2.health_id) FROM sensor_health sh2 WHERE sh2.station_id = s.station_id
                )
                LEFT JOIN anomalies a ON a.anomaly_id = (
                    SELECT MAX(a2.anomaly_id) FROM anomalies a2 WHERE a2.station_id = s.station_id
                )
                ORDER BY s.station_id
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if rows and any(r["temperature"] is not None for r in rows):
                db_stations = []
                for idx, r in enumerate(rows):
                    st_id = r["station_id"]
                    digits = "".join(c for c in st_id if c.isdigit())
                    num_val = int(digits) if digits else (idx + 1)
                    disp_id = f"AWS{num_val:03d}"
                    num_str = f"{num_val:02d}"

                    temp = float(r["temperature"]) if r["temperature"] is not None else 25.0
                    exp_t = float(r["expected_temperature"]) if r["expected_temperature"] is not None else temp
                    press = float(r["pressure"]) if r["pressure"] is not None else 1013.0
                    exp_p = float(r["expected_pressure"]) if r["expected_pressure"] is not None else press
                    hum = float(r["humidity"]) if r["humidity"] is not None else 65.0
                    exp_h = float(r["expected_humidity"]) if r["expected_humidity"] is not None else hum

                    health = int(round(float(r["health_score"]))) if r["health_score"] is not None else 95
                    rel = float(r["communication_reliability"]) if r["communication_reliability"] is not None else 1.0
                    conn_val = "Online" if rel >= 0.8 else "Warning" if rel >= 0.5 else "Critical"

                    anom_type = r["anomaly_type"] or "NORMAL"
                    is_anom = anom_type != "NORMAL"
                    sev = r["severity"] or ("NORMAL" if not is_anom else "CRITICAL")
                    anom_status = "Anomaly Detected" if is_anom else "Normal"
                    anom_score = float(r["anomaly_score"]) if r["anomaly_score"] is not None else (0.85 if is_anom else 0.05)

                    ts_val = r["timestamp"]
                    last_updated = str(ts_val).split(" ")[-1] if ts_val else "14:32:08"
                    last_recorded = str(ts_val) if ts_val else "2025-04-27 14:32:08"

                    # Calculate SHAP drivers from residual errors
                    t_err = abs(temp - exp_t)
                    p_err = abs(press - exp_p)
                    h_err = abs(hum - exp_h)
                    tot_err = max(0.01, t_err + p_err + h_err)
                    shap_drivers = {
                        "Temperature": int(round((t_err / tot_err) * 100)),
                        "Relative Humidity": int(round((h_err / tot_err) * 100)),
                        "Pressure": int(round((p_err / tot_err) * 100)),
                    }
                    if not is_anom:
                        shap_drivers = {"Temperature": 34, "Relative Humidity": 33, "Pressure": 33}
                        primary = "None"
                    else:
                        primary = max(shap_drivers, key=shap_drivers.get)

                    db_stations.append({
                        "id": disp_id,
                        "number": num_str,
                        "name": f"Station {num_str}",
                        "connectivity": conn_val,
                        "lastRecorded": last_recorded,
                        "sensorHealth": health,
                        "stationStatus": "Normal" if not is_anom else "Critical" if sev == "CRITICAL" else "Warning",
                        "temperature": round(temp, 1),
                        "expectedTemp": round(exp_t, 1),
                        "pressure": round(press, 1),
                        "expectedPressure": round(exp_p, 1),
                        "humidity": round(hum, 1),
                        "expectedHumidity": round(exp_h, 1),
                        "anomalyScore": round(anom_score, 2),
                        "confidence": 94 if is_anom else 98,
                        "anomalyStatus": anom_status,
                        "anomalyType": anom_type,
                        "primary_feature": primary,
                        "shap_drivers": shap_drivers,
                        "reason": r["explanation"] or "Sensor measurements align with physical theoretical models.",
                        "recommendedAction": r["recommended_action"] or "Routine monitoring.",
                        "lastUpdated": last_updated,
                    })
                return db_stations
        except Exception as e:
            print(f"Error reading stations from DB: {e}")

    return [dict(s) for s in STATIONS_CONFIG]


def get_station(station_id: str | None, time_range: str = "3M") -> dict | None:
    """Gets single station detail linked to database."""
    if not station_id:
        return None
    normalized_id = station_id.upper().strip()
    stations = get_stations()
    match = next((s for s in stations if s["id"] == normalized_id or s["id"].replace("AWS00", "AWS_0") == normalized_id), None)
    if not match:
        match = stations[0]

    st_dict = dict(match)
    st_dict["trend"] = generate_physical_trends(st_dict["id"], time_range)
    st_dict["readings"] = generate_station_readings(st_dict["id"])
    st_dict["anomalies"] = get_station_anomalies_list(st_dict["id"])
    return st_dict
