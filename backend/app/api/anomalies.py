from fastapi import APIRouter
from app.db.database import get_connection


router = APIRouter()


@router.get("/anomalies")
def get_anomalies():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            anomaly_id,
            telemetry_id,
            station_id,
            anomaly_type,
            is_anomaly,
            anomaly_score,
            severity,
            detected_at
        FROM anomalies
        ORDER BY detected_at DESC
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "anomaly_id": row[0],
            "telemetry_id": row[1],
            "station_id": row[2],
            "anomaly_type": row[3],
            "is_anomaly": row[4],
            "anomaly_score": row[5],
            "severity": row[6],
            "detected_at": row[7],
        }
        for row in rows
    ]