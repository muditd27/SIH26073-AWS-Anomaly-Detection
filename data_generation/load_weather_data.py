import pandas as pd
import psycopg2


DB_NAME = "sih26073"


def load_data(file_path, dataset_type):
    df = pd.read_csv(file_path)

    connection = psycopg2.connect(dbname=DB_NAME)
    cursor = connection.cursor()

    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO training_data (
                station_id,
                timestamp,
                temperature,
                humidity,
                pressure,
                dataset_type,
                is_anomaly,
                anomaly_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row["station_id"],
                row["timestamp"],
                row["temperature"],
                row["relative_humidity"],
                row["pressure"],
                dataset_type,
                bool(row["is_anomaly"]) if "is_anomaly" in row else False,
                row["anomaly_type"] if "anomaly_type" in row else None,
            ),
        )

    connection.commit()
    cursor.close()
    connection.close()

    print(f"Loaded {len(df)} rows from {file_path}")


load_data("data/clean_aws_data_3_months.csv", "clean")
load_data("data/anomalous_aws_data_3_months.csv", "anomaly_injected")