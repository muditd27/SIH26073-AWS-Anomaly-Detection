import pandas as pd


def extract_features(rows):
    columns = [
        "timestamp",
        "temperature",
        "humidity",
        "pressure",
    ]

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        return df

    # Make sure data is in chronological order
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Previous reading
    df["temperature_lag1"] = df["temperature"].shift(1)
    df["humidity_lag1"] = df["humidity"].shift(1)
    df["pressure_lag1"] = df["pressure"].shift(1)

    # Change from previous reading
    df["temperature_change"] = (
        df["temperature"] - df["temperature_lag1"]
    )

    df["humidity_change"] = (
        df["humidity"] - df["humidity_lag1"]
    )

    df["pressure_change"] = (
        df["pressure"] - df["pressure_lag1"]
    )

    # Rolling statistics
    df["temperature_rolling_mean"] = (
        df["temperature"].rolling(window=6, min_periods=1).mean()
    )

    df["humidity_rolling_mean"] = (
        df["humidity"].rolling(window=6, min_periods=1).mean()
    )

    df["pressure_rolling_mean"] = (
        df["pressure"].rolling(window=6, min_periods=1).mean()
    )

    df["temperature_rolling_std"] = (
        df["temperature"].rolling(window=6, min_periods=1).std()
    )

    df["humidity_rolling_std"] = (
        df["humidity"].rolling(window=6, min_periods=1).std()
    )

    df["pressure_rolling_std"] = (
        df["pressure"].rolling(window=6, min_periods=1).std()
    )

    return df