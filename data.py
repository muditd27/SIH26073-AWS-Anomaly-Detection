from __future__ import annotations

import math
from datetime import datetime, timedelta

LAST_UPDATED = "14:32:08"


def _hash(n: float) -> float:
    x = math.sin(n * 12.9898) * 43758.5453
    return x - math.floor(x)


def build_trend(seed: int, temp_base: float, press_base: float, hum_base: float) -> list[dict]:
    start = datetime(2025, 1, 1)
    points = []
    for i in range(365):
        date = start + timedelta(days=i)
        season = math.sin((i / 365) * math.pi * 2)
        noise = (_hash(i + seed) - 0.5) * 2
        wiggle = math.sin(i / 2.4 + seed) + math.sin(i / 0.7 + seed * 1.7) * 0.55
        spike = 5 if _hash(i * 3 + seed) > 0.97 else 0

        temp_expected = temp_base + season * 8
        press_expected = press_base - season * 6
        hum_expected = hum_base + season * 10

        points.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "label": date.strftime("%b %d"),
                "month": date.strftime("%b"),
                "tempActual": round(temp_expected + noise * 2.8 + wiggle * 1.8 + spike, 1),
                "tempExpected": round(temp_expected + wiggle * 0.35, 1),
                "pressActual": round(press_expected + noise * 4.2 + wiggle * 2.2, 1),
                "pressExpected": round(press_expected + wiggle * 0.4, 1),
                "humActual": round(min(99, max(20, hum_expected + noise * 7 + wiggle * 3 + spike)), 1),
                "humExpected": round(hum_expected + wiggle * 0.5, 1),
            }
        )
    return points


def build_readings(last_updated: str, temp: float, pressure: float, humidity: float) -> list[dict]:
    weather_cycle = ["drizzle", "rain", "rain", "rain", "rain", "rain", "rain", "rain", "rain"]
    hours, minutes, *rest = [int(part) for part in last_updated.split(":")]
    seconds = rest[0] if rest else 0
    end = datetime(2025, 4, 27, hours, minutes, seconds)
    rows = []
    for i in range(9):
        time = end - timedelta(minutes=5 * i)
        drift = i * 1.15
        rows.append(
            {
                "id": i + 1,
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "temp": round(temp - drift, 1),
                "pressure": round(pressure + drift * 1.15, 1),
                "humidity": round(humidity - drift * 2.1, 1),
                "wind": round(4.7 - i * 0.32, 1),
                "weather": weather_cycle[i],
            }
        )
    return rows


STATIONS = [
    {
        "id": "AWS001",
        "number": "01",
        "name": "Station 01",
        "connectivity": "Online",
        "temperature": 28.4,
        "expectedTemp": 27.1,
        "pressure": 1011.8,
        "expectedPressure": 1012.4,
        "humidity": 72,
        "expectedHumidity": 70.2,
        "sensorHealth": 94,
        "anomalyStatus": "Normal",
        "lastUpdated": "14:32:08",
        "lastRecorded": "2025-04-27 14:32:08",
        "stationStatus": "Normal",
        "anomalyScore": 0.12,
        "confidence": 96,
        "reason": "Readings are within the expected range for this time of day. No sensor malfunction detected.",
        "trend": build_trend(11, 26, 1012, 68),
        "readings": build_readings("14:32:08", 28.4, 1011.8, 72),
    },
    {
        "id": "AWS002",
        "number": "02",
        "name": "Station 02",
        "connectivity": "Warning",
        "temperature": 32.7,
        "expectedTemp": 29.4,
        "pressure": 1008.3,
        "expectedPressure": 1011.1,
        "humidity": 68,
        "expectedHumidity": 64.8,
        "sensorHealth": 76,
        "anomalyStatus": "Possible Anomaly",
        "lastUpdated": "14:26:17",
        "lastRecorded": "2025-04-27 14:26:17",
        "stationStatus": "Warning",
        "anomalyScore": 0.58,
        "confidence": 81,
        "reason": "Temperature is trending above the expected band. Pressure is slightly depressed. Continue monitoring for sensor drift.",
        "trend": build_trend(23, 29, 1009, 66),
        "readings": build_readings("14:26:17", 32.7, 1008.3, 68),
    },
    {
        "id": "AWS003",
        "number": "03",
        "name": "Station 03",
        "connectivity": "Critical",
        "temperature": 42.8,
        "expectedTemp": 31.2,
        "pressure": 1004.2,
        "expectedPressure": 1012.1,
        "humidity": 89.2,
        "expectedHumidity": 74.5,
        "sensorHealth": 61,
        "anomalyStatus": "Anomaly Detected",
        "lastUpdated": "14:21:03",
        "lastRecorded": "2025-04-27 14:21:03",
        "stationStatus": "Critical",
        "anomalyScore": 0.87,
        "confidence": 92,
        "reason": "Temperature and relative humidity are significantly higher than expected. Possible sensor malfunction or extreme local weather event.",
        "trend": build_trend(47, 31, 1008, 74),
        "readings": build_readings("14:32:00", 42.8, 1004.2, 89.2),
    },
    {
        "id": "AWS004",
        "number": "04",
        "name": "Station 04",
        "connectivity": "Online",
        "temperature": 24.6,
        "expectedTemp": 24.1,
        "pressure": 1015.6,
        "expectedPressure": 1015.2,
        "humidity": 66,
        "expectedHumidity": 65.4,
        "sensorHealth": 97,
        "anomalyStatus": "Normal",
        "lastUpdated": "14:31:42",
        "lastRecorded": "2025-04-27 14:31:42",
        "stationStatus": "Normal",
        "anomalyScore": 0.08,
        "confidence": 98,
        "reason": "All sensor channels are stable and aligned with the forecast model. Station is operating normally.",
        "trend": build_trend(71, 23, 1015, 64),
        "readings": build_readings("14:31:42", 24.6, 1015.6, 66),
    },
]


def get_station(station_id: str | None) -> dict | None:
    if not station_id:
        return None
    return next((station for station in STATIONS if station["id"] == station_id), None)


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
    if rang == "7D":
        return trend[-7:]
    if rang == "1M":
        return trend[-30:]
    return trend
