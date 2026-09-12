from fastapi import FastAPI

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
