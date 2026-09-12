from app.api.stations import router as stations_router
from app.api.sensor_health import router as sensor_health_router
from app.api.alerts import router as alerts_router
from app.api.anomalies import router as anomalies_router
from fastapi import FastAPI, HTTPException

from app.schemas.telemetry import TelemetryCreate
from app.services.feature_window import get_latest_window
from app.services.feature_extraction import extract_features
from app.services.ml_service import predict_anomaly
from app.db.database import get_connection


app = FastAPI(title="SIH26073 AWS Anomaly Detection")
app.include_router(anomalies_router)
app.include_router(alerts_router)
app.include_router(sensor_health_router)
app.include_router(stations_router)

@app.get("/")
def root():
    return {"message": "AWS Anomaly Detection API is running"}


@app.post("/telemetry")
def create_telemetry(data: TelemetryCreate):

    # 1. Store telemetry
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


    # 2. Get latest 97 readings
    history = get_latest_window(data.station_id)


    # 3. Extract temporal features
    features = extract_features(history)

    latest_features = features.iloc[-1:].to_dict(
        orient="records"
    )


    # 4. Run ML anomaly detection
    ml_result = predict_anomaly(history)


    # 5. Save ML prediction
    connection = get_connection()
    cursor = connection.cursor()

    latest = history[-1]

    temperature_error = (
        data.temperature - latest[1]
    )

    pressure_error = (
        data.pressure - latest[3]
    )

    humidity_error = (
        data.humidity - latest[2]
    )

    cursor.execute(
        """
        INSERT INTO predictions (
            telemetry_id,
            station_id,
            expected_temperature,
            expected_pressure,
            expected_humidity,
            temperature_error,
            pressure_error,
            humidity_error,
            anomaly_score,
            model_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            telemetry_id,
            data.station_id,
            latest[1],
            latest[3],
            latest[2],
            temperature_error,
            pressure_error,
            humidity_error,
            ml_result["anomaly_score"],
            "isolation_forest_v1",
        ),
    )

    connection.commit()

    cursor.close()
    connection.close()


    # 6. Save anomaly and create alert if detected
    if ml_result["is_anomaly"]:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO anomalies (
                telemetry_id,
                station_id,
                anomaly_type,
                is_anomaly,
                anomaly_score,
                severity
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING anomaly_id
            """,
            (
                telemetry_id,
                data.station_id,
                "ML_ANOMALY",
                True,
                ml_result["anomaly_score"],
                "MEDIUM",
            ),
        )

        anomaly_id = cursor.fetchone()[0]

        connection.commit()

        cursor.close()
        connection.close()


        # Create alert
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO alerts (
                anomaly_id,
                station_id,
                severity,
                status,
                message
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                anomaly_id,
                data.station_id,
                "MEDIUM",
                "NEW",
                "Anomaly detected by ML model",
            ),
        )

        connection.commit()

        cursor.close()
        connection.close()


    # 7. Update sensor health
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM anomalies
        WHERE station_id = %s
        """,
        (data.station_id,),
    )

    anomaly_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM telemetry
        WHERE station_id = %s
        AND timestamp >= NOW() - INTERVAL '1 hour'
        """,
        (data.station_id,),
    )

    recent_readings = cursor.fetchone()[0]

    communication_reliability = min(
        recent_readings / 6.0,
        1.0
    )

    prediction_error = (
        abs(temperature_error)
        + abs(pressure_error)
        + abs(humidity_error)
    ) / 3.0

    health_score = min(
        100.0,
        max(
            0.0,
            100.0
            - (anomaly_count * 5.0)
            - (prediction_error * 2.0)
            + (communication_reliability * 10.0)
        )
    )

    cursor.execute(
        """
        INSERT INTO sensor_health (
            station_id,
            health_score,
            anomaly_count,
            prediction_error,
            communication_reliability
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            data.station_id,
            health_score,
            anomaly_count,
            prediction_error,
            communication_reliability,
        ),
    )

    connection.commit()

    cursor.close()
    connection.close()


    # 8. Return result
    return {
        "message": "Telemetry stored successfully",
        "telemetry_id": telemetry_id,
        "station_id": data.station_id,

        "history": [
            {
                "timestamp": row[0],
                "temperature": row[1],
                "humidity": row[2],
                "pressure": row[3],
            }
            for row in history
        ],

        "features": latest_features,

        "ml_result": ml_result,

        "sensor_health": {
            "health_score": health_score,
            "anomaly_count": anomaly_count,
            "prediction_error": prediction_error,
            "communication_reliability": communication_reliability,
        },
    }