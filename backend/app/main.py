from app.services.feature_window import get_latest_window
from fastapi import FastAPI, HTTPException
from app.schemas.telemetry import TelemetryCreate

from app.db.database import get_connection


app = FastAPI(title="SIH26073 AWS Anomaly Detection")


@app.get("/")
def root():
    return {"message": "AWS Anomaly Detection API is running"}


@app.get("/stations")
def get_stations():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            station_id,
            station_name,
            latitude,
            longitude,
            elevation,
            is_active
        FROM stations
        ORDER BY station_id
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    stations = []

    for row in rows:
        stations.append({
            "station_id": row[0],
            "station_name": row[1],
            "latitude": row[2],
            "longitude": row[3],
            "elevation": row[4],
            "is_active": row[5]
        })

    return stations
@app.get("/stations/{station_id}")
def get_station(station_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            station_id,
            station_name,
            latitude,
            longitude,
            elevation,
            is_active
        FROM stations
        WHERE station_id = %s
    """, (station_id,))

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Station not found")

    return {
        "station_id": row[0],
        "station_name": row[1],
        "latitude": row[2],
        "longitude": row[3],
        "elevation": row[4],
        "is_active": row[5]
    }
@app.get("/stations/{station_id}/readings")
def get_station_readings(station_id: str, limit: int = 10):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            telemetry_id,
            timestamp,
            temperature,
            humidity,
            pressure
        FROM telemetry
        WHERE station_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """, (station_id, limit))

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    readings = []

    for row in rows:
        readings.append({
            "telemetry_id": row[0],
            "timestamp": row[1],
            "temperature": row[2],
            "humidity": row[3],
            "pressure": row[4]
        })

    return readings
@app.post("/telemetry")
def create_telemetry(data: TelemetryCreate):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO telemetry (
            station_id,
            timestamp,
            temperature,
            humidity,
            pressure
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING telemetry_id
        """,
        (
            data.station_id,
            data.timestamp,
            data.temperature,
            data.humidity,
            data.pressure,
        ),
    )

    telemetry_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Telemetry stored successfully",
        "telemetry_id": telemetry_id,
        "station_id": data.station_id,
    }
@app.get("/stations/{station_id}/history")
def get_station_history(station_id: str):
    rows = get_latest_window(station_id)

    return [
        {
            "timestamp": row[0],
            "temperature": row[1],
            "humidity": row[2],
            "pressure": row[3],
        }
        for row in rows
    ]