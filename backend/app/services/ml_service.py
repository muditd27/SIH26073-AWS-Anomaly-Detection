from ml.unified_ml_pipeline import UnifiedMLPipeline

pipeline = UnifiedMLPipeline(
    xgb_models_dir="ml/models"
)


def predict_weather(
    new_records,
    historical_buffer,
    previous_sensor_health
):
    """
    Run the complete teammate ML pipeline:

    Isolation Forest
    → XGBoost weather regression
    → XGBoost anomaly classifier
    → SHAP explanation
    → sensor health
    """

    result = pipeline.process_batch(
        new_records=new_records,
        historical_buffer=historical_buffer,
        previous_sensor_health=previous_sensor_health
    )

    return result["frontend_results"][0]