from fastapi import APIRouter
from app.db.database import get_connection


router = APIRouter()


@router.get("/sensor-health")
def get_sensor_health():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT ON (station_id)
            station_id,
            health_score,
            anomaly_count,
            prediction_error,
            communication_reliability,
            updated_at
        FROM sensor_health
        ORDER BY station_id, updated_at DESC
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "station_id": row[0],
            "health_score": row[1],
            "anomaly_count": row[2],
            "prediction_error": row[3],
            "communication_reliability": row[4],
            "updated_at": row[5],
        }
        for row in rows
    ]