"""
Data provider module for Streamlit UI.
Connects to FastAPI backend and falls back to local DB/precomputed trends.
"""
from __future__ import annotations

import os
import sys
import requests
from typing import Dict, List, Any, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
LAST_UPDATED = "14:32:08"


def fetch_stations_from_backend() -> list[dict]:
    """Tries fetching station cards from FastAPI backend; falls back to local provider."""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/stations", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list):
                # Standardize format for Streamlit components
                formatted = []
                for s in data:
                    formatted.append({
                        "id": s.get("display_id", "AWS001"),
                        "number": s.get("number", "01"),
                        "name": s.get("station_name", "Station 01"),
                        "connectivity": s.get("status_badge", "Online"),
                        "temperature": float(s.get("temperature", 28.4)),
                        "pressure": float(s.get("pressure", 1011.8)),
                        "humidity": float(s.get("relative_humidity", 72.0)),
                        "sensorHealth": int(s.get("sensor_health", 94)),
                        "anomalyStatus": s.get("anomaly_status", "Normal"),
                        "anomalyType": s.get("anomaly_type", "NORMAL"),
                        "lastUpdated": s.get("last_updated", "14:32:08"),
                    })
                return formatted
    except Exception:
        pass

    # Fallback to streamlit_app data_provider
    try:
        from streamlit_app.data_provider import get_stations_summary
        local_data = get_stations_summary()
        formatted = []
        for s in local_data:
            formatted.append({
                "id": s["display_id"],
                "number": s["number"],
                "name": s["station_name"],
                "connectivity": s["status_badge"],
                "temperature": s["temperature"],
                "pressure": s["pressure"],
                "humidity": s["relative_humidity"],
                "sensorHealth": s["sensor_health"],
                "anomalyStatus": s["anomaly_status"],
                "anomalyType": s["anomaly_type"],
                "lastUpdated": s["last_updated"],
            })
        return formatted
    except Exception as e:
        print("Fallback data provider error:", e)
        return []


def get_stations() -> list[dict]:
    return fetch_stations_from_backend()


def get_station(station_id: str | None) -> dict | None:
    """Tries fetching station details from FastAPI backend; falls back to local provider."""
    if not station_id:
        return None

    try:
        resp_sum = requests.get(f"{BACKEND_URL}/api/station/{station_id}/summary", timeout=2)
        resp_raw = requests.get(f"{BACKEND_URL}/api/station/{station_id}/raw-data", timeout=2)
        resp_trends = requests.get(f"{BACKEND_URL}/api/station/{station_id}/trends?range=3M", timeout=2)
        resp_anom = requests.get(f"{BACKEND_URL}/api/station/{station_id}/anomalies", timeout=2)

        if resp_sum.status_code == 200:
            sum_data = resp_sum.json()
            raw_data = resp_raw.json() if resp_raw.status_code == 200 else []
            trends_data = resp_trends.json() if resp_trends.status_code == 200 else {}
            anom_data = resp_anom.json() if resp_anom.status_code == 200 else []

            # Reformat trend points for Plotly
            trend_points = []
            labels = trends_data.get("labels", [])
            timestamps = trends_data.get("timestamps", [])
            t_act = trends_data.get("temperature", {}).get("actual", [])
            t_exp = trends_data.get("temperature", {}).get("expected", [])
            p_act = trends_data.get("pressure", {}).get("actual", [])
            p_exp = trends_data.get("pressure", {}).get("expected", [])
            h_act = trends_data.get("humidity", {}).get("actual", [])
            h_exp = trends_data.get("humidity", {}).get("expected", [])

            for i in range(len(labels)):
                trend_points.append({
                    "label": labels[i],
                    "timestamp": timestamps[i] if i < len(timestamps) else labels[i],
                    "tempActual": t_act[i] if i < len(t_act) else 25.0,
                    "tempExpected": t_exp[i] if i < len(t_exp) else 25.0,
                    "pressActual": p_act[i] if i < len(p_act) else 1012.0,
                    "pressExpected": p_exp[i] if i < len(p_exp) else 1012.0,
                    "humActual": h_act[i] if i < len(h_act) else 65.0,
                    "humExpected": h_exp[i] if i < len(h_exp) else 65.0,
                })

            readings = []
            for r in raw_data:
                readings.append({
                    "id": r.get("index", 1),
                    "timestamp": r.get("timestamp", ""),
                    "temp": r.get("temperature", 0.0),
                    "pressure": r.get("pressure", 0.0),
                    "humidity": r.get("humidity", 0.0),
                })

            return {
                "id": sum_data.get("display_id", station_id),
                "number": sum_data.get("number", "01"),
                "name": sum_data.get("station_name", "Station 01"),
                "connectivity": sum_data.get("status_badge", "Online"),
                "lastRecorded": sum_data.get("last_recorded", "2025-04-27 14:32:08"),
                "sensorHealth": sum_data.get("sensor_health", 94),
                "stationStatus": sum_data.get("station_status", "Normal"),
                "temperature": sum_data.get("temperature", {}).get("actual", 28.4),
                "expectedTemp": sum_data.get("temperature", {}).get("expected", 28.0),
                "pressure": sum_data.get("pressure", {}).get("actual", 1011.8),
                "expectedPressure": sum_data.get("pressure", {}).get("expected", 1011.0),
                "humidity": sum_data.get("humidity", {}).get("actual", 72.0),
                "expectedHumidity": sum_data.get("humidity", {}).get("expected", 70.0),
                "anomalyScore": sum_data.get("anomaly_score", {}).get("score", 0.15),
                "confidence": sum_data.get("anomaly_score", {}).get("confidence", 92),
                "anomalyStatus": sum_data.get("anomaly_status", {}).get("status_text", "Normal"),
                "anomalyType": sum_data.get("anomaly_status", {}).get("type", "NORMAL"),
                "reason": sum_data.get("anomaly_status", {}).get("reason", "Sensor operating normally."),
                "recommendedAction": "Inspect ADC channel" if "RAIL" in sum_data.get("anomaly_status", {}).get("type", "") else "Routine maintenance.",
                "trend": trend_points,
                "readings": readings,
                "anomalies": anom_data,
            }
    except Exception:
        pass

    # Local fallback provider
    from streamlit_app.data_provider import (
        get_station_detail,
        get_station_trends,
        get_station_raw_data,
        get_station_anomalies,
    )
    detail = get_station_detail(station_id)
    trends = get_station_trends(station_id, "3M")
    raw = get_station_raw_data(station_id)
    anoms = get_station_anomalies(station_id)

    trend_points = []
    labels = trends.get("labels", [])
    timestamps = trends.get("timestamps", [])
    t_act = trends.get("temperature", {}).get("actual", [])
    t_exp = trends.get("temperature", {}).get("expected", [])
    p_act = trends.get("pressure", {}).get("actual", [])
    p_exp = trends.get("pressure", {}).get("expected", [])
    h_act = trends.get("humidity", {}).get("actual", [])
    h_exp = trends.get("humidity", {}).get("expected", [])

    for i in range(len(labels)):
        trend_points.append({
            "label": labels[i],
            "timestamp": timestamps[i] if i < len(timestamps) else labels[i],
            "tempActual": t_act[i] if i < len(t_act) else 25.0,
            "tempExpected": t_exp[i] if i < len(t_exp) else 25.0,
            "pressActual": p_act[i] if i < len(p_act) else 1012.0,
            "pressExpected": p_exp[i] if i < len(p_exp) else 1012.0,
            "humActual": h_act[i] if i < len(h_act) else 65.0,
            "humExpected": h_exp[i] if i < len(h_exp) else 65.0,
        })

    readings = []
    for r in raw:
        readings.append({
            "id": r.get("index", 1),
            "timestamp": r.get("timestamp", ""),
            "temp": r.get("temperature", 0.0),
            "pressure": r.get("pressure", 0.0),
            "humidity": r.get("humidity", 0.0),
        })

    return {
        "id": detail["display_id"],
        "number": detail["number"],
        "name": detail["station_name"],
        "connectivity": detail["status_badge"],
        "lastRecorded": detail["last_recorded"],
        "sensorHealth": detail["sensor_health"],
        "stationStatus": detail["station_status"],
        "temperature": detail["temperature"]["actual"],
        "expectedTemp": detail["temperature"]["expected"],
        "pressure": detail["pressure"]["actual"],
        "expectedPressure": detail["pressure"]["expected"],
        "humidity": detail["humidity"]["actual"],
        "expectedHumidity": detail["humidity"]["expected"],
        "anomalyScore": detail["anomaly_score"]["score"],
        "confidence": detail["anomaly_score"]["confidence"],
        "anomalyStatus": detail["anomaly_status"]["status_text"],
        "anomalyType": detail["anomaly_status"]["type"],
        "reason": detail["anomaly_status"]["reason"],
        "recommendedAction": "Inspect hardware and verify signal stability.",
        "trend": trend_points,
        "readings": readings,
        "anomalies": anoms,
    }


def delta(actual: float, expected: float, digits: int = 1) -> str:
    value = actual - expected
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{digits}f}"


def health_tone(value: int) -> str:
    if value >= 85:
        return "ok"
    if value >= 70:
        return "warn"
    return "bad"


def connectivity_class(status: str) -> str:
    s = (status or "").lower()
    if "online" in s: return "ok"
    if "warn" in s: return "warn"
    return "bad"


def anomaly_class(status: str) -> str:
    s = (status or "").lower()
    if "normal" in s: return "ok"
    if "possible" in s or "warn" in s: return "warn"
    return "bad"


def filter_trend(trend: list[dict], rang: str) -> list[dict]:
    if not trend:
        return []
    if rang == "7D":
        return trend[-70:] if len(trend) >= 70 else trend
    if rang == "1M":
        return trend[-140:] if len(trend) >= 140 else trend
    return trend
