from fastapi import APIRouter
from backend.app.db.database import get_connection


router = APIRouter()


@router.get("/alerts")
def get_alerts():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            alert_id,
            anomaly_id,
            station_id,
            severity,
            status,
            message,
            created_at,
            resolved_at
        FROM alerts
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "alert_id": row[0],
            "anomaly_id": row[1],
            "station_id": row[2],
            "severity": row[3],
            "status": row[4],
            "message": row[5],
            "created_at": row[6],
            "resolved_at": row[7],
        }
        for row in rows
    ]