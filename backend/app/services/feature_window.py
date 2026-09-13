from backend.app.db.database import get_connection


def get_latest_window(station_id: str, limit: int = 97):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            timestamp,
            temperature,
            humidity,
            pressure
        FROM telemetry
        WHERE station_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """,
        (station_id, limit),
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    # Database returns newest → oldest.
    # ML needs oldest → newest.
    rows.reverse()

    return rows