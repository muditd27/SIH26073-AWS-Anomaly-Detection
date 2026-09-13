from fastapi import APIRouter, HTTPException
from backend.app.db.database import get_connection

router = APIRouter()


def format_connectivity(reliability: float | None) -> str:
    if reliability is None:
        return "Online"
    if reliability >= 0.8:
        return "Online"
    if reliability >= 0.5:
        return "Warning"
    return "Critical"


def format_anomaly_status(is_anomaly: bool | None, severity: str | None, anomaly_type: str | None) -> str:
    if not is_anomaly or anomaly_type == "NORMAL":
        return "Normal"
    sev = (severity or "").upper()
    if sev in ["LOW", "MEDIUM"]:
        return "Possible Anomaly"
    return "Anomaly Detected"


def format_station_status(connectivity: str, anomaly_status: str, severity: str | None) -> str:
    sev = (severity or "").upper()
    if connectivity == "Critical" or sev in ["HIGH", "CRITICAL"] or anomaly_status == "Anomaly Detected":
        return "Critical"
    if connectivity == "Warning" or sev in ["LOW", "MEDIUM"] or anomaly_status == "Possible Anomaly":
        return "Warning"
    return "Normal"


@router.get("/api/dashboard/stations")
def get_dashboard_stations():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
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
            p.temperature_error,
            p.pressure_error,
            p.humidity_error,
            p.anomaly_score as p_anomaly_score,
            a.anomaly_type,
            a.is_anomaly,
            a.anomaly_score as a_anomaly_score,
            a.confidence,
            a.severity,
            a.explanation,
            a.recommended_action
        FROM stations s
        LEFT JOIN LATERAL (
            SELECT * FROM telemetry WHERE station_id = s.station_id ORDER BY timestamp DESC LIMIT 1
        ) t ON true
        LEFT JOIN LATERAL (
            SELECT * FROM sensor_health WHERE station_id = s.station_id ORDER BY updated_at DESC LIMIT 1
        ) sh ON true
        LEFT JOIN LATERAL (
            SELECT * FROM predictions WHERE station_id = s.station_id ORDER BY created_at DESC LIMIT 1
        ) p ON true
        LEFT JOIN LATERAL (
            SELECT * FROM anomalies WHERE station_id = s.station_id ORDER BY detected_at DESC LIMIT 1
        ) a ON true
        ORDER BY s.station_id;
        """
    )

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    result = []
    for r in rows:
        st_id = r[0]
        st_name = r[1]
        temp = r[2] if r[2] is not None else 0.0
        press = r[3] if r[3] is not None else 0.0
        hum = r[4] if r[4] is not None else 0.0
        timestamp = r[5]

        health = round(r[6], 1) if r[6] is not None else 100.0
        reliability = r[7]

        exp_temp = r[8] if r[8] is not None else temp
        exp_press = r[9] if r[9] is not None else press
        exp_hum = r[10] if r[10] is not None else hum

        temp_err = r[11] if r[11] is not None else round(temp - exp_temp, 2)
        press_err = r[12] if r[12] is not None else round(press - exp_press, 2)
        hum_err = r[13] if r[13] is not None else round(hum - exp_hum, 2)

        anom_score = r[14] if r[14] is not None else (r[17] if r[17] is not None else 0.0)

        anom_type = r[15] or "NORMAL"
        is_anom = r[16] if r[16] is not None else False
        confidence = r[18] if r[18] is not None else 95.0
        severity = r[19] or "NORMAL"
        explanation = r[20] or "Station readings operating normally."
        recommended_action = r[21] or "No action required."

        conn_status = format_connectivity(reliability)
        anom_status = format_anomaly_status(is_anom, severity, anom_type)
        st_status = format_station_status(conn_status, anom_status, severity)

        # Number extraction (e.g. AWS_01 -> 01)
        num_str = st_id.replace("AWS_", "").replace("AWS", "").zfill(2)

        last_updated = timestamp.strftime("%H:%M:%S") if timestamp else "N/A"
        last_recorded = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"

        result.append(
            {
                "id": st_id,
                "number": num_str,
                "name": st_name,
                "connectivity": conn_status,
                "temperature": round(temp, 1),
                "expectedTemp": round(exp_temp, 1),
                "tempError": round(temp_err, 2),
                "pressure": round(press, 1),
                "expectedPressure": round(exp_press, 1),
                "pressError": round(press_err, 2),
                "humidity": round(hum, 1),
                "expectedHumidity": round(exp_hum, 1),
                "humError": round(hum_err, 2),
                "sensorHealth": int(round(health)),
                "anomalyStatus": anom_status,
                "anomalyType": anom_type,
                "lastUpdated": last_updated,
                "lastRecorded": last_recorded,
                "stationStatus": st_status,
                "anomalyScore": round(anom_score, 2),
                "confidence": int(round(confidence)),
                "severity": severity,
                "reason": explanation,
                "recommendedAction": recommended_action,
            }
        )

    return result


@router.get("/api/stations/{station_id}/detail")
def get_station_detail(station_id: str):
    stations = get_dashboard_stations()
    station = next((s for s in stations if s["id"] == station_id), None)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    connection = get_connection()
    cursor = connection.cursor()

    # Telemetry and prediction history for trend charts
    cursor.execute(
        """
        SELECT 
            t.telemetry_id,
            t.timestamp,
            t.temperature,
            t.pressure,
            t.humidity,
            p.expected_temperature,
            p.expected_pressure,
            p.expected_humidity
        FROM telemetry t
        LEFT JOIN predictions p ON t.telemetry_id = p.telemetry_id
        WHERE t.station_id = %s
        ORDER BY t.timestamp ASC
        LIMIT 200;
        """,
        (station_id,),
    )
    history_rows = cursor.fetchall()

    trend = []
    readings = []

    for idx, row in enumerate(reversed(history_rows)):
        # Recent raw telemetry log (latest first)
        t_id = row[0]
        ts = row[1]
        temp = row[2]
        press = row[3]
        hum = row[4]
        if idx < 20:
            readings.append(
                {
                    "id": idx + 1,
                    "telemetryId": t_id,
                    "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "",
                    "temp": round(temp, 1) if temp is not None else 0.0,
                    "pressure": round(press, 1) if press is not None else 0.0,
                    "humidity": round(hum, 1) if hum is not None else 0.0,
                }
            )

    # Trend points (chronological order)
    for row in history_rows:
        ts = row[1]
        temp = row[2] if row[2] is not None else 0.0
        press = row[3] if row[3] is not None else 0.0
        hum = row[4] if row[4] is not None else 0.0

        exp_t = row[5] if row[5] is not None else temp
        exp_p = row[6] if row[6] is not None else press
        exp_h = row[7] if row[7] is not None else hum

        trend.append(
            {
                "date": ts.strftime("%Y-%m-%d") if ts else "",
                "label": ts.strftime("%b %d %H:%M") if ts else "",
                "month": ts.strftime("%b") if ts else "",
                "tempActual": round(temp, 1),
                "tempExpected": round(exp_t, 1),
                "pressActual": round(press, 1),
                "pressExpected": round(exp_p, 1),
                "humActual": round(hum, 1),
                "humExpected": round(exp_h, 1),
            }
        )

    # Fetch recent alerts for station
    cursor.execute(
        """
        SELECT alert_id, severity, status, message, created_at
        FROM alerts
        WHERE station_id = %s
        ORDER BY created_at DESC
        LIMIT 10;
        """,
        (station_id,),
    )
    alert_rows = cursor.fetchall()
    alerts = [
        {
            "alert_id": r[0],
            "severity": r[1],
            "status": r[2],
            "message": r[3],
            "created_at": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "",
        }
        for r in alert_rows
    ]

    cursor.close()
    connection.close()

    station["trend"] = trend
    station["readings"] = readings
    station["alerts"] = alerts

    return station
