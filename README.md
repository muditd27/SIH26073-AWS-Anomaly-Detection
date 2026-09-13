
# SkyGuard AI

Streamlit dashboard from the SkyGuard / Nexora mockups.

## Run locally

```bash
cd skyguard-ai
python -m pip install -r requirements.txt
streamlit run app.py
```

- `stations_page.py` is the home grid (AWS001–AWS004)
- Click any station card to open `?station=AWS001`
- `station_detail.py` is the selected-station view
- Home icon and breadcrumb return to the station list

## SkyGuard AI

Intelligent Real-Time Anomaly Detection and Sensor Health Monitoring for Automatic Weather Stations

SkyGuard AI is a real-time artificial intelligence and machine learning system which is used for detecting anomalies in the data relating to temperature, atmospheric pressure, and relative humidity obtained from a number of nearby Automatic Weather Stations (AWS).

It uses data validation, temporal behaviour, spatial consistency, Isolation Forest, XGBoost regression, XGBoost classification, SHAP explainability, and sensor health tracking in order to tell the difference between sensor faults and real weather events.

System Workflow

At each timestamp the readings from the 4 AWS stations are processed as a group. Each of the AWS stations is compared with the other three.

4 AWS Readings at Same Timestamp
              ↓
Data Validation
              ↓
Health-Weighted Neighbour Features
              ↓
Temporal Features
              ↓
       ┌──────┴──────┐
       ↓             ↓
Isolation Forest   XGBoost Regressors
                     ↓
              Expected T / P / RH
                     ↓
              Prediction Errors
       └──────┬──────┘
              ↓
       XGBoost Classifier
              ↓
    Anomaly Type + Confidence
              ↓
            SHAP
              ↓
       Explain the Decision
              ↓
       Update Sensor Health
              ↓
      Decision Engine
              ↓
       PostgreSQL / Dashboard
              ↓
          Next Timestamp

## Machine Learning Pipeline

# Isolation Forest

An unsupervised model was used to find observations that are unlike normal sensor behaviour.

# XGBoost Regressors

Three regression models predict the expected:

Temperature

Atmospheric Pressure

Relative Humidity

The discrepancy between the real and the predicted values then constitutes an important anomaly signal.

# XGBoost Classifier

Combines sensor values, temporal features, spatial features, Isolation Forest evidence and regression errors to classify the event, such as:

NORMAL

SPIKE

FREEZE

DRIFT

GENUINE_WEATHER_EVENT

COMMUNICATION_ERROR

DATA_CORRUPTION

The specific classes are decided upon by the training dataset.

# SHAP Explainability

SHAP is used to explain the XGBoost classifier by highlighting the features that made the greatest contribution to the predicted anomaly type.

Example:

Prediction: SPIKE
Confidence: 97%

Major contributing factors:
• Temperature neighbour difference
• Temperature prediction error
• Isolation Forest score
• Temperature change

Key Features

Temporal Features

Lag values, changes and moving statistics show what has recently happened with the sensors and aid in the detection of sudden changes, fixed values and abnormal patterns.

Spatial Features

At each timestamp all of the AWS stations are compared with each of the other three AWS stations.

For AWS₁:

[
N_1 =
\frac{H_2A_2 + H_3A_3 + H_4A_4}
{H_2 + H_3 + H_4}
]

Where A represents the sensor reading and H represents the sensor health.

The values for Temperature, Pressure and Humidity are each calculated separately.

The gap between the target AWS and its neighbour value, adjusted for health, is also employed as a feature.

Model-Based Features

The scores from the Isolation Forest and the errors from the XGBoost regression both offer further evidence as to whether an observation differs from what is expected behaviour.

Example:

Actual Temperature   = 55°C
Expected Temperature = 31°C
Prediction Error     = +24°C

Sensor Health

SkyGuard has separate health scores on a scale from 0 to 100 for Temperature, Pressure and Relative Humidity, as well as an overall station health score.

Health is updated after anomaly classification:

NORMAL
   ↓
Health gradually recovers

SENSOR FAULT
   ↓
Health decreases

GENUINE WEATHER EVENT
   ↓
Health is not significantly penalized

The observation from neighbours at timestamp t+1 is weighted by the health at timestamp t.

A continuous feedback loop is thus formed as a result of which the impact of unreliable sensors is reduced.

What SkyGuard Detects

Sudden sensor spikes

Frozen/stuck values

Sensor drift and degradation

Communication/data errors

Abnormal observations

Real weather events as opposed to sensor faults

System Architecture

AWS Network
    ↓
FastAPI Ingestion & Validation
    ↓
PostgreSQL
    ↓
Feature Engineering
    ↓
ML Inference
    ↓
Decision Engine
    ↓
PostgreSQL Results
    ↓
Streamlit Dashboard

Components

The AWS Network offers real-time readings of temperature, pressure, and humidity.

FastAPI takes in and validates the telemetry that is received.

PostgreSQL is used for storing telemetry, station information, results, and sensor-health history.

– Generates features that are temporal and spatial.

Perform isolation forest and XGBoost models' inference.

The Decision Engine determines the event type, severity and level of confidence by combining the outputs of the model with the relevant evidence.

The Streamlit Dashboard displays the anomalies, along with explanations, confidence levels, and sensor health.

## Output

For each AWS and timestamp, SkyGuard can produce:

Anomaly Type
Confidence
Predicted Temperature / Pressure / Humidity
Prediction Errors
Neighbour Differences
SHAP Explanation
Temperature Health
Pressure Health
Humidity Health
Overall Health
Severity

Tech Stack

Python · Pandas · NumPy · Scikit-learn · XGBoost · SHAP · FastAPI · PostgreSQL · Streamlit
 Goal

The aim of SkyGuard AI is to create a weather observation network which is self-aware, resilient and explainable so that it can detect anomalies, tell the difference between sensor faults and real weather events, keep an eye on sensor degradation and issue alerts based on evidence.

## Research Foundation

The approach is based on research and practices covering:

Isolation Forest for unsupervised anomaly detection

XGBoost for prediction and classification

Automatic Weather Station quality control

Temporal and spatial consistency checks

Explainable machine learning

This was developed as part of the Smart India Hackathon 2026 — Problem Statement 26073.
