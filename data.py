from __future__ import annotations

import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
LAST_UPDATED = "Live Sync"


def fetch_stations_from_backend() -> list[dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/api/dashboard/stations", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print("Error fetching stations from backend:", e)
    return []


def get_stations() -> list[dict]:
    return fetch_stations_from_backend()


def get_station(station_id: str | None) -> dict | None:
    if not station_id:
        return None
    try:
        resp = requests.get(f"{BACKEND_URL}/api/stations/{station_id}/detail", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error fetching station detail for {station_id}:", e)
    return None


def delta(actual: float, expected: float, digits: int = 1) -> str:
    value = actual - expected
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{digits}f}"


def health_tone(value: int) -> str:
    if value >= 90:
        return "ok"
    if value >= 70:
        return "warn"
    return "bad"


def connectivity_class(status: str) -> str:
    return {"Online": "ok", "Warning": "warn"}.get(status, "bad")


def anomaly_class(status: str) -> str:
    return {"Normal": "ok", "Possible Anomaly": "warn"}.get(status, "bad")


def filter_trend(trend: list[dict], rang: str) -> list[dict]:
    if not trend:
        return []
    if rang == "7D":
        return trend[-7:]
    if rang == "1M":
        return trend[-30:]
    return trend
