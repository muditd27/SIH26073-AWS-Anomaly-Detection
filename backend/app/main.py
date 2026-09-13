from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.telemetry import TelemetryCreate
from app.services.ml_service import predict_weather
from app.db.database import get_connection

from app.api.stations import router as stations_router
from app.api.sensor_health import router as sensor_health_router
from app.api.alerts import router as alerts_router
from app.api.anomalies import router as anomalies_router


app = FastAPI(title="SIH26073 AWS Anomaly Detection")


# ---------------------------------------------------------
# CORS - allow frontend to communicate with FastAPI
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------

app.include_router(anomalies_router)
app.include_router(alerts_router)
app.include_router(sensor_health_router)
app.include_router(stations_router)


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AWS Anomaly Detection API is running"
    }


# ---------------------------------------------------------
# GET TELEMETRY
# Used by frontend dashboard
# ---------------------------------------------------------

@app.get("/telemetry")
def get_telemetry():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            telemetry_id,
            station_id,
            timestamp,
            temperature,
            humidity,
            pressure
        FROM telemetry
        ORDER BY timestamp DESC
        LIMIT 100
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "telemetry_id": row[0],
            "station_id": row[1],
            "timestamp": row[2],
            "temperature": row[3],
            "humidity": row[4],
            "pressure": row[5],
        }
        for row in rows
    ]


# ---------------------------------------------------------
# POST TELEMETRY
# Complete ML processing pipeline
# ---------------------------------------------------------

@app.post("/telemetry")
def create_telemetry(data: TelemetryCreate):

    # ---------------------------------------------------------
    # 1. Store incoming telemetry
    # ---------------------------------------------------------

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


    # ---------------------------------------------------------
    # 2. Get recent history from all stations
    # ---------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            telemetry_id,
            station_id,
            timestamp,
            temperature,
            pressure,
            humidity
        FROM (
            SELECT
                telemetry_id,
                station_id,
                timestamp,
                temperature,
                pressure,
                humidity,
                ROW_NUMBER() OVER (
                    PARTITION BY station_id
                    ORDER BY timestamp DESC
                ) AS row_num
            FROM telemetry
            WHERE timestamp < %s
        ) AS recent_data
        WHERE row_num <= 28
        ORDER BY timestamp ASC
        """,
        (data.timestamp,),
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    historical_buffer = [
        {
            "telemetry_id": row[0],
            "station_id": row[1],
            "timestamp": row[2],
            "temperature": row[3],
            "pressure": row[4],
            "relative_humidity": row[5],
        }
        for row in rows
    ]


    # ---------------------------------------------------------
    # 3. Current reading for ML pipeline
    # ---------------------------------------------------------

    new_records = [
        {
            "telemetry_id": telemetry_id,
            "station_id": data.station_id,
            "timestamp": data.timestamp,
            "temperature": data.temperature,
            "pressure": data.pressure,
            "relative_humidity": data.humidity,
        }
    ]


    # ---------------------------------------------------------
    # 4. Get previous sensor health
    # ---------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT ON (station_id)
            station_id,
            health_score
        FROM sensor_health
        ORDER BY station_id, updated_at DESC
        """
    )

    health_rows = cursor.fetchall()

    cursor.close()
    connection.close()

    previous_sensor_health = {
        row[0]: float(row[1])
        for row in health_rows
    }

    for station_id in [
        "AWS_01",
        "AWS_02",
        "AWS_03",
        "AWS_04",
    ]:
        previous_sensor_health.setdefault(
            station_id,
            100.0
        )


    # ---------------------------------------------------------
    # 5. Run complete ML pipeline
    # ---------------------------------------------------------

    ml_result = predict_weather(
        new_records=new_records,
        historical_buffer=historical_buffer,
        previous_sensor_health=previous_sensor_health,
    )


    # ---------------------------------------------------------
    # 6. Extract ML results
    # ---------------------------------------------------------

    classification = ml_result["classification"]

    anomaly_type = classification["anomaly_type"]
    confidence = classification["confidence"]
    severity = classification["severity"]

    is_anomaly = (
        anomaly_type != "NORMAL"
        or ml_result["isolation_forest"]["flagged"]
    )

    anomaly_score = ml_result["isolation_forest"]["anomaly_score"]

    sensor_readings = ml_result["sensor_readings"]

    expected = sensor_readings["expected"]
    differences = sensor_readings["differences"]

    shap_explainability = ml_result["shap_explainability"]

    primary_reason = shap_explainability.get(
        "primary_reason",
        "Anomaly detected"
    )

    recommended_action = shap_explainability.get(
        "recommended_action",
        "Inspect the sensor"
    )

    affected_sensors = ""


    # ---------------------------------------------------------
    # 7. Save prediction
    # ---------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

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
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        """,
        (
            telemetry_id,
            data.station_id,
            expected["temperature"],
            expected["pressure"],
            expected["humidity"],
            differences["temperature_error"],
            differences["pressure_error"],
            differences["humidity_error"],
            anomaly_score,
            "IF_2 + XGBoost_v2",
        ),
    )

    connection.commit()

    cursor.close()
    connection.close()


    # ---------------------------------------------------------
    # 8. Save anomaly and create alert
    # ---------------------------------------------------------

    anomaly_id = None

    if is_anomaly:

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
                confidence,
                severity,
                affected_sensors,
                explanation,
                recommended_action
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            RETURNING anomaly_id
            """,
            (
                telemetry_id,
                data.station_id,
                anomaly_type,
                True,
                anomaly_score,
                confidence,
                severity,
                affected_sensors,
                primary_reason,
                recommended_action,
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
                severity,
                "NEW",
                f"{anomaly_type}: {primary_reason}",
            ),
        )

        connection.commit()

        cursor.close()
        connection.close()


    # ---------------------------------------------------------
    # 9. Calculate communication reliability
    # ---------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

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


    # ---------------------------------------------------------
    # 10. Get anomaly count
    # ---------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM anomalies
        WHERE station_id = %s
        """,
        (data.station_id,),
    )

    anomaly_count = cursor.fetchone()[0]


    # ---------------------------------------------------------
    # 11. Calculate prediction error
    # ---------------------------------------------------------

    prediction_error = (
        abs(differences["temperature_error"])
        + abs(differences["pressure_error"])
        + abs(differences["humidity_error"])
    ) / 3.0


    # ---------------------------------------------------------
    # 12. Get ML sensor health
    # ---------------------------------------------------------

    sensor_health = classification.get(
        "updated_sensor_health",
        100.0
    )

    sensor_health = min(
        100.0,
        max(
            0.0,
            float(sensor_health)
        )
    )


    # ---------------------------------------------------------
    # 13. Save sensor health
    # ---------------------------------------------------------

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
            sensor_health,
            anomaly_count,
            prediction_error,
            communication_reliability,
        ),
    )

    connection.commit()

    cursor.close()
    connection.close()


    # ---------------------------------------------------------
    # 14. Return API response
    # ---------------------------------------------------------

    return {
        "message": "Telemetry processed successfully",

        "telemetry_id": telemetry_id,

        "station_id": data.station_id,

        "ml_result": ml_result,

        "sensor_health": {
            "health_score": sensor_health,
            "anomaly_count": anomaly_count,
            "prediction_error": prediction_error,
            "communication_reliability": communication_reliability,
        },
    }