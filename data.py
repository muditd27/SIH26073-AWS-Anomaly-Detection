"""
Data provider module for SkyGuard AI Streamlit Dashboard.
Provides smooth, realistic meteorological trends matching physical weather patterns.
Strictly 3 sensors: Temperature, Pressure, Relative Humidity (no wind or weather).
"""
from __future__ import annotations

import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
LAST_UPDATED = "14:32:08"


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

        # Smooth seasonal envelope (gentle arc across the season)
        s_t = 5.5 * math.sin(prog * math.pi)
        s_p = -3.0 * math.sin(prog * math.pi)
        s_h = -5.0 * math.sin(prog * math.pi)

        # Synoptic scale weather front progression (wavelength ~10 days)
        syn_t = 1.6 * math.sin(prog * 10.0) + 0.8 * math.cos(prog * 18.0)
        syn_p = -1.8 * math.sin(prog * 10.0) - 0.9 * math.cos(prog * 18.0)
        syn_h = 2.2 * math.sin(prog * 10.0) + 1.1 * math.cos(prog * 18.0)

        # Diurnal day/night cycle only for 7D view where it renders cleanly
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

        # Actual closely follows Expected with mild natural variation
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


def filter_trend(trend: list[dict], range_key: str) -> list[dict]:
    return trend


def generate_station_readings(station_id: str) -> list[dict]:
    """Generates strictly 24 recent 5-minute ticks with unique timestamps and no wind/weather."""
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
    """Anomaly log events for each station matching problem statement."""
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


# Preset master stations matching screenshot metrics
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
        "reason": "Sensor measurements align perfectly with physical theoretical models and regional peers.",
        "recommendedAction": "No maintenance required.",
        "lastUpdated": "14:31:42",
    },
]


def get_stations() -> list[dict]:
    return [dict(s) for s in STATIONS_CONFIG]


def get_station(station_id: str | None, time_range: str = "3M") -> dict | None:
    if not station_id:
        return None
    normalized_id = station_id.upper().strip()
    match = next((s for s in STATIONS_CONFIG if s["id"] == normalized_id), None)
    if not match:
        match = STATIONS_CONFIG[0]

    st_dict = dict(match)
    st_dict["trend"] = generate_physical_trends(st_dict["id"], time_range)
    st_dict["readings"] = generate_station_readings(st_dict["id"])
    st_dict["anomalies"] = get_station_anomalies_list(st_dict["id"])
    return st_dict
