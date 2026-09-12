from fastapi import APIRouter
from app.db.database import get_connection

router = APIRouter()


@router.get("/stations")
def get_stations():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            station_id,
            station_name,
            latitude,
            longitude,
            elevation,
            is_active
        FROM stations
        ORDER BY station_id
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "station_id": row[0],
            "station_name": row[1],
            "latitude": row[2],
            "longitude": row[3],
            "elevation": row[4],
            "is_active": row[5],
        }
        for row in rows
    ]